import urllib.parse

import pytest
import xbmcaddon

from resources.lib.twitch import gql, http, playback

TOKEN = {'value': '{"channel":"runner"}', 'signature': 'sig'}


@pytest.fixture
def token(monkeypatch):
    asked = []

    def query(text, variables=None, anonymous=False):
        asked.append(text)
        field = 'streamPlaybackAccessToken' if 'streamPlayback' in text else 'videoPlaybackAccessToken'
        return {field: TOKEN}
    monkeypatch.setattr(gql, 'query', query)
    return asked


@pytest.fixture
def usher(monkeypatch):
    fetched = []
    monkeypatch.setattr(http, 'request', lambda url, **kw: fetched.append(url) or (200, b'#EXTM3U'))
    return fetched


def test_live_url(token, usher):
    url = playback.live_url('Runner')
    parts = urllib.parse.urlsplit(url)
    query = dict(urllib.parse.parse_qsl(parts.query))
    assert parts.path == '/api/channel/hls/runner.m3u8'
    assert (query['sig'], query['token'], query['supported_codecs']) == ('sig', TOKEN['value'], 'h264')
    assert 'channelName:"Runner"' in token[0]
    assert usher == [url]


def test_codecs_setting(token, usher):
    xbmcaddon.SETTINGS['codecs'] = 2
    query = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(playback.video_url('123')).query))
    assert query['supported_codecs'] == 'av1,h265,h264'


def test_refused_playlist_says_why(token, monkeypatch):
    def refused(url, **kwargs):
        raise http.HTTPError(403, b'[{"error":"Content is restricted to subscribers"}]', url)
    monkeypatch.setattr(http, 'request', refused)
    with pytest.raises(playback.PlaybackError, match='restricted to subscribers'):
        playback.live_url('runner')


def test_missing_token_is_an_error(monkeypatch):
    monkeypatch.setattr(gql, 'query', lambda text, variables=None, anonymous=False: {'videoPlaybackAccessToken': None})
    with pytest.raises(playback.PlaybackError):
        playback.video_url('1')


def test_clip_plays_the_best_file(monkeypatch):
    monkeypatch.setattr(gql, 'query', lambda text, variables=None, anonymous=False: {'clip': {
        'videoQualities': [{'quality': '720', 'frameRate': 60, 'sourceURL': 'https://clips/720.mp4'},
                           {'quality': '1080', 'frameRate': 30, 'sourceURL': 'https://clips/1080.mp4'},
                           {'quality': '1080', 'frameRate': 60, 'sourceURL': 'https://clips/1080-60.mp4'}],
        'playbackAccessToken': TOKEN}})
    url = playback.clip_url('slug')
    assert url.startswith('https://clips/1080-60.mp4?sig=sig&token=')
