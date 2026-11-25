# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""The TV window's layout, made to work with any skin.

A script's window uses the current skin's fonts, and skins name their fonts differently: only font13 is
common to all. So the layout is a template (resources/tv/twitch-tv.xml) with a role in place of each font,
and before the window opens each role gets the current skin's font closest in size and weight. The result is
written to Kodi's temp folder, which Kodi then loads the window from."""
import json
import os
import re
import xml.etree.ElementTree as ET

import xbmc
import xbmcvfs

from .. import kodi

TEMPLATE = os.path.join(kodi.ADDON_PATH, 'resources', 'tv', 'twitch-tv.xml')
MEDIA = os.path.join(kodi.ADDON_PATH, 'resources', 'tv', 'media')
WINDOW_DIR = os.path.join(kodi.TEMP_DIR, 'tv')  # Kodi looks for <dir>/resources/skins/Default/1080i/<file>
XML_NAME = 'twitch-tv.xml'
FALLBACK = 'font13'

# role -> (size at 1080 lines, bold)
ROLES = {
    'hero_title': (50, True),
    'hero_plot': (27, False),
    'screen_title': (27, True),
    'row_title': (33, True),
    'tile_title': (25, False),
    'tile_meta': (23, False),
    'rail': (30, False),
    'badge': (20, True),
}
# Fonts made for one purpose (clocks, weather, flags, monospace) or a style that would look out of place.
UNSUITABLE = re.compile(r'mono|clock|weather|flag|italic|thin|light|symbol|icon', re.I)


def pick_fonts(fonts, roles=None):
    """For each role, the name of the closest font. `fonts` is [(name, size at 1080 lines, bold, caps)]."""
    roles = roles or ROLES
    usable = [f for f in fonts if not f[3] and not UNSUITABLE.search(f[0])]
    picked = {}
    for role, (size, bold) in roles.items():
        if not usable:
            picked[role] = FALLBACK
            continue
        # A wrong weight counts like being 6 pixels off; ties go to the plainer (shorter) name.
        best = min(usable, key=lambda f: (abs(f[1] - size) + (6 if f[2] != bold else 0), len(f[0])))
        picked[role] = best[0]
    return picked


def _font_entry(font, scale):
    """(name, size at 1080 lines, bold, caps) of a <font> element; None for one that is no use here (no
    readable size, or a clock, icon or monospace file)."""
    name = font.findtext('name') or ''
    filename = (font.findtext('filename') or '').lower()
    try:
        size = float(font.findtext('size') or 0) * scale
    except ValueError:
        return None
    if UNSUITABLE.search(filename):
        return None
    style = (font.findtext('style') or '').lower()
    bold = 'bold' in style or 'bold' in filename or name.lower().endswith('bold')
    return name, size, bold, 'uppercase' in style


def read_fonts(font_xml, fontset_id, height):
    """[(name, size at 1080 lines, bold, caps)] from a skin's Font.xml, for the named fontset (or the first)."""
    sets = ET.parse(font_xml).getroot().findall('fontset')
    chosen = next((s for s in sets if s.get('id') == fontset_id), sets[0] if sets else None)
    if chosen is None:
        return []
    scale = 1080.0 / (height or 1080)
    entries = (_font_entry(font, scale) for font in chosen.findall('font'))
    return [entry for entry in entries if entry]


def _skin_font_xml():
    """The current skin's Font.xml and the height its layouts are made for."""
    skin_path = xbmcvfs.translatePath('special://skin/')
    root = ET.parse(os.path.join(skin_path, 'addon.xml')).getroot()
    for res in root.iter('res'):
        path = os.path.join(skin_path, res.get('folder', ''), 'Font.xml')
        if os.path.exists(path):
            return path, int(res.get('height') or 1080)
    return None, 1080


def _fontset():
    """The name of the fontset in use (Kodi's lookandfeel.font setting)."""
    reply = json.loads(xbmc.executeJSONRPC(json.dumps({
        'jsonrpc': '2.0', 'id': 1, 'method': 'Settings.GetSettingValue', 'params': {'setting': 'lookandfeel.font'}})))
    return reply.get('result', {}).get('value', 'Default')


def current_fonts():
    """{role: font name} for the current skin; the one font every skin has when it can't be read."""
    try:
        path, height = _skin_font_xml()
        if path:
            return pick_fonts(read_fonts(path, _fontset(), height))
    except (OSError, ET.ParseError, ValueError) as exc:
        kodi.log('TV interface: reading the skin fonts failed: %s' % exc)
    return dict.fromkeys(ROLES, FALLBACK)


def render(template, fonts, media, icon):
    """The template with its includes pasted in and its fonts, media folder and icon filled in."""
    includes = {}

    def keep_include(match):  # an <include> is taken out of the template and kept for pasting
        includes[match.group(1)] = match.group(2)
        return ''

    xml = re.sub(r'\s*<include name="(\w+)">(.*?)</include>', keep_include, template, flags=re.S)
    xml = re.sub(r'@include:(\w+)@', lambda m: includes[m.group(1)], xml)
    xml = re.sub(r'@font:(\w+)@', lambda m: fonts.get(m.group(1), FALLBACK), xml)
    return xml.replace('@media@', media.replace('\\', '/')).replace('@icon@', icon.replace('\\', '/'))


def prepare():
    """Write the window for the current skin; returns the folder to open it from."""
    with open(TEMPLATE, encoding='utf-8') as handle:
        template = handle.read()
    fonts = current_fonts()
    kodi.log('TV interface fonts for %s: %s' % (xbmc.getSkinDir(), fonts))
    icon = os.path.join(MEDIA, 'icon.png')
    target = os.path.join(WINDOW_DIR, 'resources', 'skins', 'Default', '1080i')
    os.makedirs(target, exist_ok=True)
    with open(os.path.join(target, XML_NAME), 'w', encoding='utf-8') as handle:
        handle.write(render(template, fonts, MEDIA, icon))
    return WINDOW_DIR
