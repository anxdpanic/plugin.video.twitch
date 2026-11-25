# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""Device-code sign-in (twitch.tv/activate) and token storage, with multiple accounts.

The add-on signs in as Twitch's TV app: its client is registered for the device-code flow and its tokens
are accepted by the GraphQL API the add-on uses for everything, playback included, so a single sign-in
also brings the account's Turbo or subscriber benefits to playback."""
import time
import uuid

from . import http, kodi

CLIENT_ID = 'ue6666qo983tsx6so1t0vnawi233wa'
# user:read:follows is for Helix, where the followed-channel lists come from (GraphQL refuses them).
SCOPES = ('channel_read chat:read user_blocks_edit user_blocks_read user_follows_edit user_read user_subscriptions '
          'user:read:follows')
DEVICE_URL = 'https://id.twitch.tv/oauth2/device'
TOKEN_URL = 'https://id.twitch.tv/oauth2/token'
VALIDATE_URL = 'https://id.twitch.tv/oauth2/validate'
REVOKE_URL = 'https://id.twitch.tv/oauth2/revoke'
DEVICE_GRANT = 'urn:ietf:params:oauth:grant-type:device_code'
EXPIRY_MARGIN = 120  # seconds: refresh this long before the token runs out

STORE = 'accounts.json'


class AuthError(Exception):
    pass


def _store():
    data = kodi.load_json(STORE, {})
    data.setdefault('accounts', {})
    data.setdefault('active', None)
    return data


def accounts():
    """List of (account_id, name) in sign-in order."""
    data = _store()
    items = sorted(data['accounts'].items(), key=lambda kv: kv[1].get('added', 0))
    return [(key, value.get('name') or key) for key, value in items]


def active_account():
    data = _store()
    key = data.get('active')
    if key and key in data['accounts']:
        return key, data['accounts'][key]
    return None, None


def signed_in():
    return active_account()[0] is not None


def user_id():
    return (active_account()[1] or {}).get('user_id') or ''


def set_active(account_id):
    data = _store()
    data['active'] = account_id if account_id in data['accounts'] else None
    kodi.save_json(STORE, data)


def request_device_code():
    """{'device_code', 'user_code', 'verification_uri', 'interval', 'expires_in'}; raises AuthError."""
    try:
        resp = http.request_json(DEVICE_URL, data={'client_id': CLIENT_ID, 'scopes': SCOPES})
    except http.HTTPError as exc:
        resp = exc.json()
    if 'device_code' not in resp:
        raise AuthError(resp.get('message') or 'no device code')
    return resp


def poll_token(device_code):
    """Returns the token dict, None while still pending, or raises AuthError."""
    try:
        resp = http.request_json(TOKEN_URL, data={'client_id': CLIENT_ID, 'scopes': SCOPES,
                                                  'device_code': device_code, 'grant_type': DEVICE_GRANT})
    except http.HTTPError as exc:
        resp = exc.json()
    if resp.get('access_token'):
        return resp
    message = str(resp.get('message') or '')
    if message.lower() in ('authorization_pending', 'slow_down'):
        return None
    raise AuthError(message or 'no token')


def validate(access_token):
    """{'login', 'user_id', 'expires_in', ...} for a token; raises HTTPError when it isn't valid."""
    return http.request_json(VALIDATE_URL, headers={'Authorization': 'OAuth ' + access_token})


def _expiry(token):
    return time.time() + int(token.get('expires_in') or 0) - EXPIRY_MARGIN if token.get('expires_in') else 0


def add_account(token, name, user_id='', avatar=''):
    """Remember a signed-in account (replacing an earlier sign-in of the same user) and make it active."""
    data = _store()
    previous = next((k for k, v in data['accounts'].items() if user_id and v.get('user_id') == user_id), None)
    account_id = previous or uuid.uuid4().hex[:12]
    data['accounts'][account_id] = {
        'name': name,
        'user_id': user_id,
        'scopes': SCOPES,
        'avatar': avatar,
        'access_token': token['access_token'],
        'refresh_token': token.get('refresh_token', ''),
        'expires_at': _expiry(token),  # 0: no expiry given, the token is used until Twitch rejects it
        'added': data['accounts'].get(account_id, {}).get('added') or time.time(),
    }
    data['active'] = account_id
    kodi.save_json(STORE, data)
    return account_id


def remove_account(account_id):
    data = _store()
    account = data['accounts'].pop(account_id, None)
    if data.get('active') == account_id:
        data['active'] = None
    kodi.save_json(STORE, data)
    if account and account.get('access_token'):
        try:
            http.request(REVOKE_URL, data={'client_id': CLIENT_ID, 'token': account['access_token']})
        except http.HTTPError:
            pass


def _drop_active(data, key):
    kodi.log('token of account %s rejected, signing it out' % key)
    data['accounts'].pop(key, None)
    data['active'] = None
    kodi.save_json(STORE, data)


def _refresh(account):
    """A refreshed token for the account; raises AuthError when Twitch won't refresh it."""
    if not account.get('refresh_token'):
        raise AuthError('no refresh token')
    try:
        return http.request_json(TOKEN_URL, data={'client_id': CLIENT_ID, 'grant_type': 'refresh_token',
                                                  'refresh_token': account['refresh_token']})
    except http.HTTPError as exc:
        if exc.status in (400, 401):
            raise AuthError(exc.json().get('message') or 'refresh refused') from exc
        raise


def access_token(force_refresh=False):
    """Valid access token for the active account, refreshing it when needed. None when signed out."""
    data = _store()
    key = data.get('active')
    account = data['accounts'].get(key) if key else None
    if not account:
        return None
    expires_at = account.get('expires_at', 0)
    if not force_refresh and (not expires_at or expires_at > time.time()):
        return account['access_token']
    try:
        resp = _refresh(account)
    except AuthError:
        _drop_active(data, key)
        raise
    account['access_token'] = resp['access_token']
    account['expires_at'] = _expiry(resp)
    if resp.get('refresh_token'):
        account['refresh_token'] = resp['refresh_token']
    kodi.save_json(STORE, data)
    return account['access_token']
