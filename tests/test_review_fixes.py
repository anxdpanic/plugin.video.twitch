"""Fixes from the code review: kept sign-ins, partial pages, no audio-only, clear offline message, polling."""
import urllib.parse

import pytest
from samples import GAME, STREAM, connection

from resources.lib.twitch import auth, gql, helix, http, lists, pages, playback, signin


def refuse(status, body=b'{}'):
    def answer(url, *args, **kwargs):
        raise http.HTTPError(status, body, url)
    return answer


def test_token_that_still_validates_is_kept(monkeypatch, signed_in):
    monkeypatch.setattr(auth, 'validate', lambda token: {'login': 'tester'})
    assert auth.recover_token() == 'tok'
    assert auth.signed_in()


def test_unknown_token_is_refreshed(monkeypatch, signed_in):
    monkeypatch.setattr(auth, 'validate', refuse(401))
    monkeypatch.setattr(http, 'request_json', lambda url, data=None, **kw: {'access_token': 'new'})
    assert auth.recover_token() == 'new'


def test_unknown_token_that_wont_refresh_signs_out(monkeypatch, signed_in):
    monkeypatch.setattr(auth, 'validate', refuse(401))
    monkeypatch.setattr(http, 'request_json', refuse(400))
    with pytest.raises(auth.AuthError):
        auth.recover_token()
    assert not auth.signed_in()


def test_validate_outage_keeps_the_account(monkeypatch, signed_in):
    monkeypatch.setattr(auth, 'validate', refuse(503))
    assert auth.recover_token() == 'tok' and auth.signed_in()


def test_gql_retries_a_401_with_the_recovered_token(monkeypatch, signed_in):
    sent = []

    def request_json(url, data=None, headers=None, **kw):
        sent.append(headers.get('Authorization'))
        if len(sent) == 1:
            raise http.HTTPError(401, b'', url)
        return {'data': {'ok': True}}
    monkeypatch.setattr(http, 'request_json', request_json)
    monkeypatch.setattr(auth, 'recover_token', lambda: 'again')
    assert gql.query('query{ok}') == {'ok': True}
    assert sent == ['OAuth tok', 'OAuth again']


def test_helix_retries_a_401(monkeypatch, signed_in):
    sent = []

    def request_json(url, headers=None, **kw):
        sent.append(headers['Authorization'])
        if len(sent) == 1:
            raise http.HTTPError(401, b'', url)
        return {'data': []}
    monkeypatch.setattr(http, 'request_json', request_json)
    monkeypatch.setattr(auth, 'recover_token', lambda: 'again')
    assert helix.get('streams/followed') == {'data': []}
    assert sent == ['Bearer tok', 'Bearer again']


def test_home_keeps_its_public_rows_when_followed_channels_fail(monkeypatch, signed_in, english):
    english(30011, 30012)

    def broken(self, params, after=None):
        raise http.HTTPError(0, b'', 'helix')
    monkeypatch.setattr(lists.FollowedList, 'fetch', broken)
    monkeypatch.setattr(gql, 'batch', lambda queries, anonymous=False: [{'streams': connection([STREAM])},
                                                                         {'games': connection([GAME])}])
    page = pages.load({'page': 'home'})
    assert [s['title'] for s in page['shelves']] == ['Top live channels', 'Top categories']


def test_cached_batch_keeps_the_repeated_cursor_guard(monkeypatch):
    calls = []
    monkeypatch.setattr(lists.List, 'fetch', lambda self, params, after=None: calls.append(1) or (['x'], after))
    shelf = {'list': 'top_streams', 'params': {}}
    assert pages.more(shelf, 'same') == (['x'], None)
    assert pages.more(shelf, 'same') == (['x'], None)  # from the cache, still ended
    assert len(calls) == 1


@pytest.fixture
def stream_token(monkeypatch):
    monkeypatch.setattr(gql, 'query', lambda text, variables=None, anonymous=False: {
        'streamPlaybackAccessToken': {'value': 'v', 'signature': 's'}})


def test_no_audio_only_rendition(stream_token, monkeypatch):
    monkeypatch.setattr(http, 'request', lambda url, **kw: (200, b''))
    query = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(playback.live_url('runner')).query))
    assert query['allow_audio_only'] == 'false'


def test_offline_channel_says_so(stream_token, monkeypatch, english):
    english(30071)
    monkeypatch.setattr(http, 'request', refuse(404, b'[{"error":"Can not find channel"}]'))
    with pytest.raises(playback.PlaybackError, match='This channel is offline.'):
        playback.live_url('runner')


def test_poll_token_slow_down(monkeypatch):
    monkeypatch.setattr(http, 'request_json', refuse(400, b'{"message":"slow_down"}'))
    assert auth.poll_token('code') == auth.SLOW_DOWN


def test_sign_in_wait_polls_less_often_after_slow_down(monkeypatch):
    class Dialog:
        def iscanceled(self):
            return False

        def close(self):
            pass

    waits = []

    class Monitor:
        def waitForAbort(self, seconds):  # noqa: N802 (Kodi API)
            waits.append(seconds)
            return False

    replies = iter([auth.SLOW_DOWN, None, {'access_token': 't'}])
    monkeypatch.setattr(signin, '_waiting_dialog', lambda code: Dialog())
    monkeypatch.setattr(signin.xbmc, 'Monitor', Monitor)
    monkeypatch.setattr(auth, 'poll_token', lambda code: next(replies))
    assert signin._wait_for_approval({'device_code': 'd', 'interval': 5}) == {'access_token': 't'}
    assert len(waits) == (5 + 10 + 10) * 4  # 5 s, then 10 s for each poll after slow_down
