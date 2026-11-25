import struct

from resources.lib.twitch import fonts, parser


def font_with(subtable):
    """A font file with only a cmap table holding one (3, 10) or (3, 1) subtable."""
    platform_encoding = (3, 10) if struct.unpack_from('>H', subtable)[0] == 12 else (3, 1)
    cmap = struct.pack('>HH', 0, 1) + struct.pack('>HHI', *platform_encoding, 12) + subtable
    header = struct.pack('>IHHHH', 0x00010000, 1, 16, 0, 0)
    return header + struct.pack('>4sIII', b'cmap', 0, 28, len(cmap)) + cmap


def format12(groups):
    body = b''.join(struct.pack('>III', first, last, 1) for first, last in groups)
    return struct.pack('>HHIII', 12, 0, 16 + len(body), 0, len(groups)) + body


def format4(segments):
    """Segments of (first, last), all mapped by delta, plus the closing 0xFFFF segment."""
    segments = list(segments) + [(0xFFFF, 0xFFFF)]
    count = len(segments)
    ends = struct.pack('>%dH' % count, *[last for _, last in segments])
    starts = struct.pack('>%dH' % count, *[first for first, _ in segments])
    deltas = struct.pack('>%dh' % count, *([1] * count))
    offsets = struct.pack('>%dH' % count, *([0] * count))
    body = ends + b'\0\0' + starts + deltas + offsets
    return struct.pack('>HHHHHHH', 4, 14 + len(body), 0, 2 * count, 0, 0, 0) + body


def test_format12_ranges_are_merged():
    data = font_with(format12([(0x20, 0x7E), (0x7F, 0xFF), (0x400, 0x4FF)]))
    assert fonts.coverage(data) == [(0x20, 0xFF), (0x400, 0x4FF)]


def test_format4_ranges():
    data = font_with(format4([(0x20, 0x7E), (0x2022, 0x2022)]))
    assert fonts.coverage(data) == [(0x20, 0x7E), (0x2022, 0x2022)]


def test_unreadable_font_has_no_ranges():
    assert fonts.coverage(struct.pack('>IHHHH', 0x00010000, 0, 0, 0, 0)) == []


def test_intersect():
    assert fonts.intersect([(0, 10), (20, 30)], [(5, 25)]) == [(5, 10), (20, 25)]
    assert fonts.intersect([(0, 10)], []) == []


def test_coverage_membership():
    covered = fonts.Coverage([(0x20, 0x7E), (0x400, 0x4FF)])
    assert 'a' in covered and 'Ж' in covered and ' ' in covered
    assert '한' not in covered and 'é' not in covered
    assert '한' in fonts.Coverage([])  # unknown font: nothing is dropped


def test_clean_drops_what_the_font_lacks(monkeypatch):
    monkeypatch.setattr(fonts, '_current', fonts.Coverage([(0x20, 0x7E), (0xB0, 0xB0)]))
    assert parser.clean('( ͡° ͜ʖ ͡°) hi 한국어') == '( ° °) hi'
    assert parser.live({'title': '한국어', 'broadcaster': {'login': 'k', 'displayName': 'K'}})['title'] == 'K'
