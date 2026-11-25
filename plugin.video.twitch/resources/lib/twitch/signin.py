# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""Signing in and out, and switching accounts: the dialogs, shared by the plugin and the TV interface."""
import xbmc
import xbmcgui

from . import auth, gql, http, kodi, lists, qr

ACTIVATE = 'twitch.tv/activate'
QR_ADDRESS = 'https://www.twitch.tv/activate?device-code=%s'  # opens the page with the code filled in
TICK = 0.25  # seconds between looks at the dialog while waiting, so Cancel answers at once
SLOW_DOWN_STEP = 5  # seconds added to the polling interval each time Twitch asks to slow down
SIGN_IN_ERRORS = (auth.AuthError, http.HTTPError, gql.GQLError)


def _notify(message, error=False):
    xbmcgui.Dialog().notification(kodi.ADDON.getAddonInfo('name'), message,
                                  xbmcgui.NOTIFICATION_ERROR if error else xbmcgui.NOTIFICATION_INFO, 4000)


# Waiting for the code to be approved
def _code_message(code):
    """The dialog's instructions: where to go and the code to enter there."""
    return kodi.formatted(30061, ACTIVATE, code['user_code'])


def _waiting_dialog(code):
    """The QR dialog when a QR code can be made, else Kodi's progress dialog; both have create/iscanceled/close."""
    image = qr.image(QR_ADDRESS % code['user_code'])
    dialog = qr.Dialog(image) if image else xbmcgui.DialogProgress()
    dialog.create(kodi.string(30060), _code_message(code))
    return dialog


def _wait(dialog, monitor, seconds):
    """Wait `seconds`, a TICK at a time; False when the viewer cancelled or Kodi is closing meanwhile."""
    for _ in range(int(seconds / TICK)):  # noqa: SIM110 (a loop that waits reads better than all())
        if dialog.iscanceled() or monitor.waitForAbort(TICK):
            return False
    return True


def _poll_until_approved(code, dialog):
    """Poll Twitch every interval until the code is approved (the token), or until it is cancelled or runs
    out (None); raises AuthError when it was refused."""
    monitor = xbmc.Monitor()
    interval = max(int(code.get('interval') or 5), 2)
    expires = int(code.get('expires_in') or 1800)
    waited = 0
    while waited < expires:
        if not _wait(dialog, monitor, interval):
            return None
        waited += interval
        token = auth.poll_token(code['device_code'])
        if token == auth.SLOW_DOWN:
            interval += SLOW_DOWN_STEP  # as the device-code flow asks: poll less often from now on
        elif token:
            return token
    _notify(kodi.string(30064), error=True)
    return None


def _wait_for_approval(code):
    """Show the code and wait for it to be approved (the token), cancelled or expired (None)."""
    dialog = _waiting_dialog(code)
    try:
        return _poll_until_approved(code, dialog)
    finally:
        dialog.close()


# Signing in
def _profile(login):
    """(display name, picture) of a user, for the account list."""
    data = gql.query('query{user(login:%s){displayName profileImageURL(width:600)}}' % lists.literal(login),
                     anonymous=True)
    user = data.get('user') or {}
    return user.get('displayName') or login, user.get('profileImageURL') or ''


def _remember(token):
    """Store the account a fresh token belongs to, named and pictured as on Twitch; returns its name."""
    who = auth.validate(token['access_token'])
    name, avatar = _profile(who.get('login') or '')
    auth.add_account(token, name, who.get('user_id') or '', avatar)
    return name


def sign_in():
    """Run the device-code sign-in; True once an account was added."""
    try:
        token = _wait_for_approval(auth.request_device_code())
        if not token:
            return False
        name = _remember(token)
    except SIGN_IN_ERRORS as exc:
        kodi.log_error('sign-in failed: %s' % exc)
        _notify(kodi.formatted(30063, exc), error=True)
        return False
    _notify(kodi.formatted(30062, name))
    return True


def sign_out(account_id=None):
    """Sign out of an account (the active one by default) once the viewer confirms; True when signed out."""
    account_id = account_id or auth.active_account()[0]
    if not account_id:
        return False
    name = dict(auth.accounts()).get(account_id, '')
    if not xbmcgui.Dialog().yesno(kodi.string(30008), kodi.formatted(30065, name)):
        return False
    auth.remove_account(account_id)
    _notify(kodi.string(30067))
    return True


# The accounts dialog
def _account_choices():
    """[(label, (action, account id))] for the accounts dialog: each account to switch to (the active one
    ticked), then add another, then sign out."""
    active = auth.active_account()[0]
    choices = [('%s%s' % (name, ' ✓' if key == active else ''), ('switch', key)) for key, name in auth.accounts()]
    choices.append((kodi.string(30066), ('add', None)))
    if active:
        choices.append((kodi.string(30008), ('sign_out', active)))
    return choices


def _switch_to(account_id):
    """Make an account the active one; True when that is a change."""
    changed = account_id != auth.active_account()[0]
    auth.set_active(account_id)
    return changed


def _run_choice(action, account_id):
    """Do what was picked in the accounts dialog; True when the active account changed."""
    if action == 'switch':
        return _switch_to(account_id)
    if action == 'add':
        return sign_in()
    return sign_out(account_id)


def accounts_menu():
    """Signed out: straight to sign-in. Signed in: switch account, add another, or sign out.
    True when the active account changed."""
    if not auth.accounts():
        return sign_in()
    choices = _account_choices()
    picked = xbmcgui.Dialog().select(kodi.string(30068), [label for label, _ in choices])
    if picked < 0:
        return False
    return _run_choice(*choices[picked][1])
