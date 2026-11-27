"""Play (choose quality): listing the renditions and playing the one picked."""
import pytest
import xbmcgui
import xbmcplugin
from samples import STREAM, VIDEO

from resources.lib.twitch import http, parser, playback, quality, router

MASTER = '\n'.join([
    '#EXTM3U',
    '#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="chunked",NAME="1440p60",AUTOSELECT=YES,DEFAULT=YES',
    '#EXT-X-STREAM-INF:BANDWIDTH=9500000,RESOLUTION=2560x1440,CODECS="hvc1.1.2.L150,mp4a.40.2",VIDEO="chunked",'
    'FRAME-RATE=60.000',
    'https://cdn/chunked.m3u8',
    '#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="720p60",NAME="720p60",AUTOSELECT=YES,DEFAULT=YES',
    '#EXT-X-STREAM-INF:BANDWIDTH=3322199,RESOLUTION=1280x720,CODECS="avc1.4D401F,mp4a.40.2",VIDEO="720p60",'
    'FRAME-RATE=60.000',
    'https://cdn/720p60.m3u8',
    '#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="1080p60",NAME="1080p60",AUTOSELECT=YES,DEFAULT=YES',
    '#EXT-X-STREAM-INF:BANDWIDTH=8042999,RESOLUTION=1920x1080,CODECS="avc1.4D401F,mp4a.40.2",VIDEO="1080p60",'
    'FRAME-RATE=60.000',
    'https://cdn/1080p60.m3u8',
    '#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="audio_only",NAME="audio_only",AUTOSELECT=NO,DEFAULT=NO',
    '#EXT-X-STREAM-INF:BANDWIDTH=160000,CODECS="mp4a.40.2",VIDEO="audio_only"',
    'https://cdn/audio_only.m3u8',
])


def test_renditions_best_first_without_audio_only():
    found = quality.renditions(MASTER)
    assert [r['name'] for r in found] == ['1440p60', '1080p60', '720p60']
    assert (found[0]['codec'], found[0]['source'], found[0]['url']) == ('HEVC', True, 'https://cdn/chunked.m3u8')


def test_label(english):
    english(30122)
    first = quality.renditions(MASTER)[0]
    assert quality.label(first) == '1440p60 (source) • HEVC • 9.5 Mbps'


def test_label_doesnt_repeat_twitchs_own_source_note(english):
    english(30122)
    first = quality.renditions(MASTER.replace('NAME="1440p60"', 'NAME="1440p60 (source)"'))[0]
    assert quality.label(first) == '1440p60 (source) • HEVC • 9.5 Mbps'


@pytest.fixture
def pick(monkeypatch):
    """The viewer picks the option at the index given (-1 closes the list); the labels shown are kept."""
    shown = []

    def choose(index):
        monkeypatch.setattr(xbmcgui.Dialog, 'select',
                            lambda self, heading, labels, **kw: shown.append(labels) or index)
        return shown
    return choose


def test_choose_rendition_plays_the_one_picked(monkeypatch, pick):
    monkeypatch.setattr(http, 'request', lambda url, **kw: (200, MASTER.encode()))
    shown = pick(1)
    assert quality.choose_rendition('https://usher/master.m3u8') == 'https://cdn/1080p60.m3u8'
    assert len(shown[0]) == 3


def test_closing_the_list_cancels(monkeypatch, pick):
    monkeypatch.setattr(http, 'request', lambda url, **kw: (200, MASTER.encode()))
    pick(-1)
    with pytest.raises(quality.Cancelled):
        quality.choose_rendition('https://usher/master.m3u8')


def test_choose_clip(monkeypatch, pick):
    monkeypatch.setattr(playback, 'clip_files', lambda slug: [
        ({'quality': '1080', 'frameRate': 60}, 'https://clips/1080.mp4'),
        ({'quality': '720', 'frameRate': 30}, 'https://clips/720.mp4')])
    shown = pick(1)
    assert quality.choose_clip('slug') == 'https://clips/720.mp4'
    assert shown[0] == ['1080p60', '720p']


def test_play_route_with_choose_plays_the_rendition(monkeypatch, pick):
    monkeypatch.setattr(playback, 'live_url', lambda login: 'https://usher/master.m3u8')
    monkeypatch.setattr(http, 'request', lambda url, **kw: (200, MASTER.encode()))
    pick(2)
    url = router.choose_quality_url(parser.live(STREAM))
    router.run([url.split('?')[0], '1', '?' + url.split('?')[1]])
    succeeded, li = xbmcplugin.RESOLVED[0]
    assert succeeded and li.path == 'https://cdn/720p60.m3u8'


def test_play_route_cancelled_quietly(monkeypatch, pick):
    monkeypatch.setattr(playback, 'video_url', lambda video_id: 'https://usher/master.m3u8')
    monkeypatch.setattr(http, 'request', lambda url, **kw: (200, MASTER.encode()))
    pick(-1)
    url = router.choose_quality_url(parser.video(VIDEO))
    router.run([url.split('?')[0], '1', '?' + url.split('?')[1]])
    assert xbmcplugin.RESOLVED[0][0] is False
    assert not xbmcgui.NOTIFICATIONS


def test_menu_entry_first_for_playable_items(english):
    english(30120)
    for item in (parser.live(STREAM), parser.video(VIDEO)):
        label, command = router._context_menu(item)[0]
        assert label == 'Play (choose quality)' and 'quality=choose' in command
