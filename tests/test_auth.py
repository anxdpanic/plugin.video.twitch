import time

import pytest

from resources.lib.twitch import auth, http


def test_add_switch_and_remove_accounts(monkeypatch):
    revoked = []
    monkeypatch.setattr(http, 'request', lambda url, data=None, **kw: revoked.append(data['token']) or (200, b''))
    first = auth.add_account({'access_token': 'a'}, 'One', '1')
    second = auth.add_account({'access_token': 'b'}, 'Two', '2')
    assert auth.accounts() == [(first, 'One'), (second, 'Two')]
    assert auth.active_account()[0] == second and auth.user_id() == '2'
    auth.set_active(first)
    assert auth.access_token() == 'a'
    auth.remove_account(first)
    assert revoked == ['a'] and not auth.signed_in()


def test_signing_in_again_replaces_the_same_user():
    first = auth.add_account({'access_token': 'a'}, 'One', '1')
    again = auth.add_account({'access_token': 'new'}, 'One', '1')
    assert first == again and len(auth.accounts()) == 1
    assert auth.access_token() == 'new'


def test_token_without_expiry_is_used_as_it_is(monkeypatch, no_network):
    auth.add_account({'access_token': 'a', 'refresh_token': 'r'}, 'One', '1')
    assert auth.access_token() == 'a'


def test_expired_token_is_refreshed(monkeypatch):
    auth.add_account({'access_token': 'old', 'refresh_token': 'r', 'expires_in': 1}, 'One', '1')
    monkeypatch.setattr(http, 'request_json', lambda url, data=None, **kw: {
        'access_token': 'fresh', 'refresh_token': 'r2', 'expires_in': 3600})
    assert auth.access_token() == 'fresh'
    account = auth.active_account()[1]
    assert account['refresh_token'] == 'r2' and account['expires_at'] > time.time()


def test_refused_refresh_signs_out(monkeypatch):
    auth.add_account({'access_token': 'old', 'refresh_token': 'r'}, 'One', '1')

    def refuse(url, **kwargs):
        raise http.HTTPError(400, b'{"message":"Invalid refresh token"}', url)
    monkeypatch.setattr(http, 'request_json', refuse)
    with pytest.raises(auth.AuthError):
        auth.access_token(force_refresh=True)
    assert not auth.signed_in()


@pytest.mark.parametrize('reply, expected', [
    ({'access_token': 't'}, {'access_token': 't'}),
    ({'status': 400, 'message': 'authorization_pending'}, None),
    ({'status': 400, 'message': 'slow_down'}, None),
])
def test_poll_token(monkeypatch, reply, expected):
    def answer(url, data=None, **kwargs):
        if 'access_token' in reply:
            return reply
        raise http.HTTPError(400, str(reply).replace("'", '"').encode(), url)
    monkeypatch.setattr(http, 'request_json', answer)
    assert auth.poll_token('code') == expected


def test_poll_token_denied(monkeypatch):
    def deny(url, data=None, **kwargs):
        raise http.HTTPError(400, b'{"status":400,"message":"authorization_declined"}', url)
    monkeypatch.setattr(http, 'request_json', deny)
    with pytest.raises(auth.AuthError):
        auth.poll_token('code')


def test_device_code_asks_for_the_follows_scope(monkeypatch):
    sent = []
    monkeypatch.setattr(http, 'request_json', lambda url, data=None, **kw: sent.append(data) or {
        'device_code': 'd', 'user_code': 'ABCD'})
    assert auth.request_device_code()['user_code'] == 'ABCD'
    assert 'user:read:follows' in sent[0]['scopes'].split()
