# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""Device-code sign-in (twitch.tv/activate) and token storage, with multiple accounts.

The add-on signs in as Twitch's TV app: its client is registered for the device-code flow and its tokens
are accepted by the GraphQL API the add-on uses for everything, playback included, so a single sign-in
also brings the account's Turbo or subscriber benefits to playback.

Accounts live in accounts.json in the add-on's profile:
    {'active': account_id or None, 'accounts': {account_id: {name, user_id, avatar, scopes, access_token,
                                                             refresh_token, expires_at, added}}}"""
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
SLOW_DOWN = 'slow_down'  # poll_token's answer when Twitch asks to be polled less often

STORE = 'accounts.json'


class AuthError(Exception):
    """Signing in failed, or the active account's sign-in is no longer accepted."""


# The account store
def _store():
    """The stored accounts, with both keys present even before the first sign-in."""
    data = kodi.load_json(STORE, {})
    data.setdefault('accounts', {})
    data.setdefault('active', None)
    return data


def _save(data):
    kodi.save_json(STORE, data)


def accounts():
    """List of (account_id, name) in sign-in order."""
    data = _store()
    items = sorted(data['accounts'].items(), key=lambda kv: kv[1].get('added', 0))
    return [(key, value.get('name') or key) for key, value in items]


def active_account():
    """(account_id, account) of the account in use, or (None, None) when signed out."""
    data = _store()
    key = data.get('active')
    if key and key in data['accounts']:
        return key, data['accounts'][key]
    return None, None


def signed_in():
    return active_account()[0] is not None


def user_id():
    """The Twitch user id of the account in use ('' when signed out); Helix lists are asked for by it."""
    return (active_account()[1] or {}).get('user_id') or ''


def set_active(account_id):
    """Switch to another signed-in account (or sign out of all of them, with an unknown id)."""
    data = _store()
    data['active'] = account_id if account_id in data['accounts'] else None
    _save(data)


# The device-code flow
def _form_reply(url, form):
    """The JSON Twitch's identity server answers a form with, whether it said yes (200) or no (4xx)."""
    try:
        return http.request_json(url, data=form)
    except http.HTTPError as exc:
        return exc.json()


def request_device_code():
    """{'device_code', 'user_code', 'verification_uri', 'interval', 'expires_in'}; raises AuthError."""
    reply = _form_reply(DEVICE_URL, {'client_id': CLIENT_ID, 'scopes': SCOPES})
    if 'device_code' not in reply:
        raise AuthError(reply.get('message') or 'no device code')
    return reply


def poll_token(device_code):
    """One look at whether the code was approved: the token dict, None while still pending, SLOW_DOWN when
    Twitch asks to poll less often; raises AuthError when it was refused or ran out."""
    reply = _form_reply(TOKEN_URL, {'client_id': CLIENT_ID, 'scopes': SCOPES, 'device_code': device_code,
                                    'grant_type': DEVICE_GRANT})
    if reply.get('access_token'):
        return reply
    message = str(reply.get('message') or '').lower()
    if message == SLOW_DOWN:
        return SLOW_DOWN
    if message == 'authorization_pending':
        return None
    raise AuthError(message or 'no token')


def validate(access_token):
    """{'login', 'user_id', 'expires_in', ...} for a token; raises HTTPError when it isn't valid."""
    return http.request_json(VALIDATE_URL, headers={'Authorization': 'OAuth ' + access_token})


# Adding and removing accounts
def _expiry(token):
    """When to refresh a token, as a timestamp; 0 for a token with no expiry (used until Twitch refuses it)."""
    seconds = int(token.get('expires_in') or 0)
    return time.time() + seconds - EXPIRY_MARGIN if seconds else 0


def _account_of_user(data, twitch_user_id):
    """The id of the stored account of this Twitch user, so signing in again replaces it; None if new."""
    if not twitch_user_id:
        return None
    return next((key for key, value in data['accounts'].items() if value.get('user_id') == twitch_user_id), None)


def add_account(token, name, user_id='', avatar=''):
    """Remember a signed-in account (replacing an earlier sign-in of the same user) and make it active."""
    data = _store()
    account_id = _account_of_user(data, user_id) or uuid.uuid4().hex[:12]
    earlier = data['accounts'].get(account_id, {})
    data['accounts'][account_id] = {
        'name': name,
        'user_id': user_id,
        'scopes': SCOPES,
        'avatar': avatar,
        'access_token': token['access_token'],
        'refresh_token': token.get('refresh_token', ''),
        'expires_at': _expiry(token),
        'added': earlier.get('added') or time.time(),  # keeps its place in the account list
    }
    data['active'] = account_id
    _save(data)
    return account_id


def _revoke(access_token):
    """Ask Twitch to forget a token; a failure is only logged, the account is gone here either way."""
    try:
        http.request(REVOKE_URL, data={'client_id': CLIENT_ID, 'token': access_token})
    except http.HTTPError as exc:
        kodi.log('revoking a token failed: %s' % exc)


def remove_account(account_id):
    """Sign an account out: forget it here, then revoke its token at Twitch."""
    data = _store()
    account = data['accounts'].pop(account_id, None)
    if data.get('active') == account_id:
        data['active'] = None
    _save(data)
    if account and account.get('access_token'):
        _revoke(account['access_token'])


def _drop_active(data, key):
    """Sign the active account out after Twitch refused both its token and a refresh."""
    kodi.log('token of account %s rejected, signing it out' % key)
    data['accounts'].pop(key, None)
    data['active'] = None
    _save(data)


# Tokens of the active account
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


def _due(account):
    """Whether the account's token is about to run out (never, for one without an expiry)."""
    expires_at = account.get('expires_at', 0)
    return bool(expires_at) and expires_at <= time.time()


def _take_refreshed(account, reply):
    """Put a refresh reply into the account; Twitch may or may not hand out a new refresh token too."""
    account['access_token'] = reply['access_token']
    account['expires_at'] = _expiry(reply)
    if reply.get('refresh_token'):
        account['refresh_token'] = reply['refresh_token']


def access_token(force_refresh=False):
    """Valid access token for the active account, refreshing it when it is due (or when forced). None when
    signed out; AuthError, and the account signed out, when Twitch won't refresh it."""
    data = _store()
    key = data.get('active')
    account = data['accounts'].get(key) if key else None
    if not account:
        return None
    if not force_refresh and not _due(account):
        return account['access_token']
    try:
        reply = _refresh(account)
    except AuthError:
        _drop_active(data, key)
        raise
    _take_refreshed(account, reply)
    _save(data)
    return account['access_token']


def recover_token():
    """After Twitch refused the token (HTTP 401): the token to try again with. A token that still validates
    was refused by chance and is kept; only a token Twitch no longer knows is refreshed, and only when that
    is refused too is the account signed out (AuthError)."""
    token = access_token()
    if not token:
        raise AuthError('signed out')
    try:
        validate(token)
        return token
    except http.HTTPError as exc:
        if exc.status != 401:
            return token  # Twitch couldn't say: keep the account and let the caller fail as it would
    return access_token(force_refresh=True)
