# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""Signing in and out, and switching accounts: the dialogs, shared by the plugin and the TV interface."""
import xbmc
import xbmcgui

from . import auth, gql, http, kodi, lists, qr

ACTIVATE = 'twitch.tv/activate'
QR_ADDRESS = 'https://www.twitch.tv/activate?device-code=%s'


def _notify(message, error=False):
    xbmcgui.Dialog().notification(kodi.ADDON.getAddonInfo('name'), message,
                                  xbmcgui.NOTIFICATION_ERROR if error else xbmcgui.NOTIFICATION_INFO, 4000)


def _code_message(code):
    return kodi.formatted(30061, ACTIVATE, code['user_code'])


def _waiting_dialog(code):
    """The QR dialog when a QR code can be made, else Kodi's progress dialog; both have create/iscanceled/close."""
    image = qr.image(QR_ADDRESS % code['user_code'])
    dialog = qr.Dialog(image) if image else xbmcgui.DialogProgress()
    dialog.create(kodi.string(30060), _code_message(code))
    return dialog


def _wait_for_approval(code):
    """Poll until the code is approved (the token), cancelled or expired (None); raises AuthError."""
    dialog = _waiting_dialog(code)
    monitor = xbmc.Monitor()
    interval = max(int(code.get('interval') or 5), 2)
    expires = int(code.get('expires_in') or 1800)
    try:
        waited = 0
        while waited < expires:
            for _ in range(interval * 4):  # a quarter second at a time, so Cancel answers at once
                if dialog.iscanceled() or monitor.waitForAbort(0.25):
                    return None
            waited += interval
            token = auth.poll_token(code['device_code'])
            if token == auth.SLOW_DOWN:
                interval += 5  # as the device-code flow asks: poll five seconds less often from now on
            elif token:
                return token
        _notify(kodi.string(30064), error=True)
        return None
    finally:
        dialog.close()


def _profile(login):
    """(display name, picture) of a user, for the account list."""
    data = gql.query('query{user(login:%s){displayName profileImageURL(width:600)}}' % lists.literal(login),
                     anonymous=True)
    user = data.get('user') or {}
    return user.get('displayName') or login, user.get('profileImageURL') or ''


def sign_in():
    """Run the device-code sign-in; True once an account was added."""
    try:
        token = _wait_for_approval(auth.request_device_code())
        if not token:
            return False
        who = auth.validate(token['access_token'])
        name, avatar = _profile(who.get('login') or '')
    except (auth.AuthError, http.HTTPError, gql.GQLError) as exc:
        kodi.log_error('sign-in failed: %s' % exc)
        _notify(kodi.formatted(30063, exc), error=True)
        return False
    auth.add_account(token, name, who.get('user_id') or '', avatar)
    _notify(kodi.formatted(30062, name))
    return True


def sign_out(account_id=None):
    account_id = account_id or auth.active_account()[0]
    names = dict(auth.accounts())
    if not account_id or not xbmcgui.Dialog().yesno(kodi.string(30008),
                                                     kodi.formatted(30065, names.get(account_id, ''))):
        return False
    auth.remove_account(account_id)
    _notify(kodi.string(30067))
    return True


def _account_choices():
    """[(label, action)] for the accounts dialog: each account to switch to, then add and sign out."""
    active = auth.active_account()[0]
    choices = [('%s%s' % (name, ' ✓' if key == active else ''), ('switch', key)) for key, name in auth.accounts()]
    choices.append((kodi.string(30066), ('add', None)))
    if active:
        choices.append((kodi.string(30008), ('sign_out', active)))
    return choices


def accounts_menu():
    """Signed out: straight to sign-in. Signed in: switch account, add another, or sign out.
    True when the active account changed."""
    if not auth.accounts():
        return sign_in()
    choices = _account_choices()
    picked = xbmcgui.Dialog().select(kodi.string(30068), [label for label, _ in choices])
    if picked < 0:
        return False
    action, key = choices[picked][1]
    if action == 'switch':
        changed = key != auth.active_account()[0]
        auth.set_active(key)
        return changed
    if action == 'add':
        return sign_in()
    return sign_out(key)
