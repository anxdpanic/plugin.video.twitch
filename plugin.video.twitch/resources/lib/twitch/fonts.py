# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""Which characters the skin's font can draw.

Kodi has no font fallback: a character missing from the skin's font is drawn as a box. Twitch titles are
full of them (emoji, text faces, scripts the font doesn't cover), so the add-on reads the character map of
the fonts the skin uses for its text and leaves out what isn't in all of them."""
import bisect
import os
import struct
import time
import xml.etree.ElementTree as ET

import xbmc
import xbmcvfs

from . import kodi

CACHE = 'font-coverage.json'
FONT_DIRS = ('special://skin/fonts/', 'special://home/media/Fonts/', 'special://xbmc/media/Fonts/')


def _table(data, tag):
    """(offset, length) of a table in a TrueType/OpenType file, or None."""
    count = struct.unpack_from('>H', data, 4)[0]
    for index in range(count):
        name, _, offset, length = struct.unpack_from('>4sIII', data, 12 + 16 * index)
        if name == tag:
            return offset, length
    return None


def _segment_codes(data, glyphs_at, start, end):
    """The codes of a format-4 segment that map through its glyph array to a glyph (0 means none)."""
    return [(code, code) for code in range(start, end + 1)
            if struct.unpack_from('>H', data, glyphs_at + 2 * (code - start))[0]]


def _format4(data, at):
    """The (first, last) ranges of a format-4 subtable (16-bit codes, as segments)."""
    count = struct.unpack_from('>H', data, at + 6)[0] // 2
    ends = struct.unpack_from('>%dH' % count, data, at + 14)
    starts = struct.unpack_from('>%dH' % count, data, at + 16 + 2 * count)
    offsets_at = at + 16 + 6 * count
    offsets = struct.unpack_from('>%dH' % count, data, offsets_at)
    ranges = []
    for i, (start, end) in enumerate(zip(starts, ends)):
        if start == 0xFFFF:  # the closing segment
            continue
        if offsets[i] == 0:  # mapped by a delta: every code in the segment has a glyph
            ranges.append((start, end))
        else:  # mapped through an array of glyph ids, which the offset points at from where it is stored
            ranges += _segment_codes(data, offsets_at + 2 * i + offsets[i], start, end)
    return ranges


def _format12(data, at):
    """The (first, last) ranges of a format-12 subtable (full Unicode, as groups)."""
    count = struct.unpack_from('>I', data, at + 12)[0]
    return [struct.unpack_from('>II', data, at + 16 + 12 * i)[:2] for i in range(count)]


FULL_UNICODE = ((3, 10), (0, 4), (0, 6))  # (platform, encoding) of subtables covering all of Unicode
BASIC_PLANE = ((3, 1), (0, 3), (0, 1), (0, 0))  # ... and of those covering the basic plane


def _subtable(data, base):
    """(format, offset) of the cmap subtable to read: a full-Unicode format 12, else a basic-plane format 4;
    None when the font has neither."""
    count = struct.unpack_from('>H', data, base + 2)[0]
    best = None
    for index in range(count):
        platform, encoding, offset = struct.unpack_from('>HHI', data, base + 4 + 8 * index)
        fmt = struct.unpack_from('>H', data, base + offset)[0]
        if (platform, encoding) in FULL_UNICODE and fmt == 12:
            return 12, base + offset
        if (platform, encoding) in BASIC_PLANE and fmt == 4 and best is None:
            best = (4, base + offset)
    return best


def _merge(ranges):
    """Ranges sorted, with overlapping and touching ones joined."""
    merged = []
    for first, last in sorted(ranges):
        if merged and first <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], last))
        else:
            merged.append((first, last))
    return merged


def coverage(data):
    """Merged [(first, last)] code point ranges a font file maps to glyphs; [] when it can't be read."""
    cmap = _table(data, b'cmap')
    subtable = _subtable(data, cmap[0]) if cmap else None
    if not subtable:
        return []
    fmt, at = subtable
    return _merge(_format12(data, at) if fmt == 12 else _format4(data, at))


class Coverage:
    """Tests characters against ranges; with no ranges (unknown font) everything passes."""

    def __init__(self, ranges):
        """`ranges`: merged (first, last) code point ranges, sorted."""
        self.firsts = [first for first, _ in ranges]
        self.ranges = ranges

    def __contains__(self, char):
        """Whether the font draws `char`; spaces always pass, so text keeps its gaps."""
        if not self.ranges or char.isspace():
            return True
        code = ord(char)
        index = bisect.bisect_right(self.firsts, code) - 1
        return index >= 0 and self.ranges[index][0] <= code <= self.ranges[index][1]


def intersect(first, second):
    """The code points in both lists of merged ranges, as merged ranges."""
    result, i, j = [], 0, 0
    while i < len(first) and j < len(second):
        low, high = max(first[i][0], second[j][0]), min(first[i][1], second[j][1])
        if low <= high:
            result.append((low, high))
        if first[i][1] < second[j][1]:
            i += 1
        else:
            j += 1
    return result


def _fontset_in_use(font_xml):
    """The <fontset> element of the skin's Font.xml that is in use (the first one when none matches)."""
    from .tv import skin

    sets = ET.parse(font_xml).getroot().findall('fontset')
    fontset_id = skin._fontset()
    return next((s for s in sets if s.get('id') == fontset_id), sets[0] if sets else None)


def _text_font_files():
    """The distinct files of the text fonts in the skin's fontset in use: every one of them draws some of the
    skin's text (Kodi's own windows, the views, the TV window). Clock, icon and monospace fonts are left out."""
    from .tv import skin  # the TV window's skin helpers already find the skin's Font.xml and fontset

    font_xml, _ = skin._skin_font_xml()
    fontset = _fontset_in_use(font_xml) if font_xml else None
    if fontset is None:
        return []
    names = [f.findtext('filename') or '' for f in fontset.findall('font')]
    return sorted({n for n in names if n and not skin.UNSUITABLE.search(n)})


def _find(filename):
    """The font file on disk; skins and Kodi don't agree on case (Arial.ttf is arial.ttf)."""
    for folder in FONT_DIRS:
        folder = xbmcvfs.translatePath(folder)
        if not os.path.isdir(folder):
            continue
        names = {name.lower(): name for name in os.listdir(folder)}
        if filename.lower() in names:
            return os.path.join(folder, names[filename.lower()])
    return None


def _stamps(paths):
    """[path, size, modified] of each font file: the cache is only used for exactly the same files."""
    return [[path, os.stat(path).st_size, int(os.stat(path).st_mtime)] for path in paths]


def _cached(stamps):
    """Ranges worked out before for these same font files, or None."""
    stored = kodi.load_json(CACHE, {})
    if stored.get('fonts') == stamps:
        return [tuple(r) for r in stored.get('ranges', [])]
    return None


def _read_all(paths):
    """The characters every one of the font files can draw."""
    ranges = None
    for path in paths:
        with open(path, 'rb') as handle:
            found = coverage(handle.read())
        if found:  # a file that can't be read says nothing either way
            ranges = found if ranges is None else intersect(ranges, found)
    return ranges or []


_current = None
_skin = None  # (skin, fontset) _current was worked out for
_checked_at = 0.0
RECHECK = 30  # seconds between looks at the skin and fontset in use (a look is a JSON-RPC call)


def _skin_in_use():
    """(skin id, fontset name) in use now."""
    from .tv import skin

    return xbmc.getSkinDir(), skin._fontset()


def _skin_changed():
    """Whether the skin or fontset changed since the coverage was worked out. With reuselanguageinvoker, this
    module outlives a skin change, so it looks again every RECHECK seconds."""
    global _checked_at
    if _current is not None and time.time() - _checked_at < RECHECK:
        return False
    _checked_at = time.time()
    try:
        return _skin_in_use() != _skin
    except (RuntimeError, ValueError) as exc:
        kodi.log('could not tell the skin in use: %s' % exc)
        return _current is None


def _ranges_of(paths):
    """The characters all these font files draw, from the cache when they are the same files as last time."""
    stamps = _stamps(paths)
    ranges = _cached(stamps)
    if ranges is None:
        ranges = _read_all(paths)
        kodi.save_json(CACHE, {'fonts': stamps, 'ranges': ranges})
    return ranges


def _work_out():
    """The ranges of the skin's text fonts; [] (nothing dropped) when they can't be found or read."""
    try:
        paths = [p for p in (_find(name) for name in _text_font_files()) if p]
        ranges = _ranges_of(paths) if paths else []
    except (OSError, ET.ParseError, struct.error, ValueError) as exc:
        kodi.log('could not read the skin fonts of %s: %s' % (xbmc.getSkinDir(), exc))
        return []
    kodi.log('skin fonts %s cover %d ranges' % (', '.join(os.path.basename(p) for p in paths), len(ranges)))
    return ranges


def _note_skin():
    """Remember the skin and fontset the coverage is being worked out for."""
    global _skin
    try:
        _skin = _skin_in_use()
    except (RuntimeError, ValueError):
        _skin = None


def current():
    """The Coverage of the skin's text fonts, worked out again when the skin or fontset changes."""
    global _current
    if _skin_changed():
        _note_skin()
        _current = Coverage(_work_out())
    return _current
