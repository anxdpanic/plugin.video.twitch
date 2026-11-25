"""Choosing between InputStream Adaptive and InputStream FFmpeg Direct for HLS playback."""
import pytest
import xbmc
import xbmcaddon
import xbmcgui

from resources.lib.twitch import players

ENABLED = 'System.AddonIsEnabled(inputstream.ffmpegdirect)'
INSTALLED = 'System.HasAddon(inputstream.ffmpegdirect)'


@pytest.fixture
def ffmpeg_direct(monkeypatch):
    """FFmpeg Direct installed and turned on, and the setting choosing it."""
    monkeypatch.setitem(xbmc.CONDITIONS, ENABLED, True)
    monkeypatch.setitem(xbmc.CONDITIONS, INSTALLED, True)
    xbmcaddon.SETTINGS['player'] = 1


def test_adaptive_by_default():
    li = players.stream_item('https://usher/live.m3u8', live=True)
    assert li.getProperty('inputstream') == players.ADAPTIVE
    assert li.getProperty('inputstream.adaptive.live_delay') == '8'
    assert li.mime == players.HLS_MIME


def test_adaptive_asks_for_the_quality_when_set():
    xbmcaddon.SETTINGS['ask_quality'] = True
    li = players.stream_item('https://usher/vod.m3u8', live=False)
    assert li.getProperty('inputstream.adaptive.stream_selection_type') == 'ask-quality'


def test_ffmpeg_direct_live(ffmpeg_direct):
    li = players.stream_item('https://usher/live.m3u8', live=True)
    assert li.getProperty('inputstream') == players.FFMPEG_DIRECT
    assert li.getProperty('inputstream.ffmpegdirect.manifest_type') == 'hls'
    assert li.getProperty('inputstream.ffmpegdirect.is_realtime_stream') == 'true'
    assert li.getProperty('inputstream.ffmpegdirect.stream_mode') == 'timeshift'
    assert li.getProperty('inputstream.adaptive.live_delay') == ''


def test_past_broadcasts_always_use_adaptive(ffmpeg_direct):
    li = players.stream_item('https://usher/vod.m3u8', live=False)
    assert li.getProperty('inputstream') == players.ADAPTIVE


def test_play_from_beginning_always_uses_adaptive(ffmpeg_direct):
    li = players.stream_item('https://usher/recording.m3u8', live=False, from_start=True)
    assert li.getProperty('inputstream') == players.ADAPTIVE
    assert li.getProperty('inputstream.adaptive.play_timeshift_buffer') == 'true'


def test_ffmpeg_direct_not_installed_falls_back(monkeypatch):
    xbmcaddon.SETTINGS['player'] = 1
    assert players.chosen(live=True) == players.ADAPTIVE


def test_turned_off_ffmpeg_direct_is_offered(monkeypatch):
    xbmcaddon.SETTINGS['player'] = 1
    monkeypatch.setitem(xbmc.CONDITIONS, INSTALLED, True)
    enabled = []

    def enable(addon_id):
        enabled.append(addon_id)
        xbmc.CONDITIONS[ENABLED] = True
    monkeypatch.setattr(players, '_enable', enable)
    monkeypatch.setattr(xbmcgui.Dialog, 'yesno', lambda self, heading, message, **kw: True)
    assert players.chosen(live=True) == players.FFMPEG_DIRECT
    assert enabled == [players.FFMPEG_DIRECT]
    xbmc.CONDITIONS.pop(ENABLED, None)


def test_declining_to_turn_it_on_plays_with_adaptive(monkeypatch):
    xbmcaddon.SETTINGS['player'] = 1
    monkeypatch.setitem(xbmc.CONDITIONS, INSTALLED, True)
    monkeypatch.setattr(players, '_enable', lambda addon_id: pytest.fail('should not turn it on'))
    monkeypatch.setattr(xbmcgui.Dialog, 'yesno', lambda self, heading, message, **kw: False)
    assert players.chosen(live=True) == players.ADAPTIVE
