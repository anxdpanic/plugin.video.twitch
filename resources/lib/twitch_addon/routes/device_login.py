# -*- coding: utf-8 -*-
"""

    Copyright (C) 2024 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

import os
import time
import threading

import xbmc
import xbmcgui
import xbmcvfs

from ..addon import utils, device_oauth
from ..addon.common import kodi, log_utils
from ..addon.constants import SCOPES, ADDON_DATA_DIR
from ..addon.utils import i18n

try:
    from ..addon import qr as qr_render
except Exception:
    qr_render = None

# Short, clean activation URL (Twitch's verification_uri carries the code as a long query string).
_ACTIVATE_URL = 'https://www.twitch.tv/activate'

_ALIGN_CENTER_X = 0x00000002  # XBFONT_CENTER_X
ACTION_PREVIOUS_MENU = 10
ACTION_STOP = 13
ACTION_NAV_BACK = 92


def do_device_login(heading, body_i18n, client_id, scopes, store_tokens, success_i18n, log_tag):
    """Shared device-code login flow: show a QR code (with a text-dialog fallback),
    poll for the token, and store it via store_tokens()."""
    ok, data = device_oauth.request_device_code(client_id, scopes)
    if not ok or not data.get('user_code'):
        kodi.Dialog().ok(heading, i18n('device_login_unsupported'))
        return

    user_code = data['user_code']
    device_code = data['device_code']
    interval = int(data.get('interval', 5)) or 5
    expires_in = int(data.get('expires_in', 1800)) or 1800
    verification_uri = data.get('verification_uri') or _ACTIVATE_URL
    body = i18n(body_i18n) % (_ACTIVATE_URL, user_code)

    poll = _make_poller(client_id, scopes, device_code)

    # Prefer the QR window; fall back to the plain text dialog when QR can't be
    # rendered/shown. A QR user-cancel or expiry is a definitive end (no fallback).
    result, token = 'fallback', None
    qr_path = _render_qr(verification_uri)
    if qr_path:
        try:
            result, token = _qr_login(heading, qr_path, verification_uri, user_code,
                                      expires_in, interval, poll)
        except Exception as err:
            log_utils.log('QR login window failed, using text fallback: %s' % repr(err),
                          log_utils.LOGWARNING)
            result = 'fallback'
        finally:
            _remove(qr_path)
    if result == 'fallback':
        result, token = _text_login(heading, body, expires_in, interval, poll)

    if result == 'ok' and token and token.get('access_token'):
        store_tokens(token['access_token'],
                     token.get('refresh_token', ''),
                     token.get('expires_in', 14400))
        log_utils.log('OAuth%s: device login succeeded, refresh token stored' % log_tag,
                      log_utils.LOGNOTICE)
        kodi.Dialog().ok(heading, i18n(success_i18n))
    elif result == 'cancelled':
        kodi.notify(i18n('login'), i18n('device_login_cancelled'), sound=False)
    else:
        kodi.notify(i18n('login'), i18n('device_login_failed'), sound=False)


def _make_poller(client_id, scopes, device_code):
    """Return poll() -> (state, token) where state is 'ok' | 'slow_down' | 'stop' | 'pending'."""
    def poll():
        status, tdata = device_oauth.poll_device_token(client_id, scopes, device_code)
        if status == 'ok':
            return 'ok', tdata
        if status == 'slow_down':
            return 'slow_down', None
        if status in ('expired', 'denied'):
            return 'stop', None
        return 'pending', None
    return poll


def _text_login(heading, body, expires_in, interval, poll):
    """Modal progress-dialog fallback that works on every skin/device (and when a
    camera isn't handy -- the viewer just types the short code). Returns (result, token)."""
    monitor = xbmc.Monitor()
    progress = xbmcgui.DialogProgress()
    progress.create(heading, body)
    waited = 0
    while waited < expires_in:
        for _ in range(interval):
            if progress.iscanceled():
                progress.close()
                return 'cancelled', None
            if monitor.waitForAbort(1):  # Kodi is shutting down
                progress.close()
                return 'failed', None
            waited += 1
        state, token = poll()
        if state == 'ok':
            progress.close()
            return 'ok', token
        elif state == 'slow_down':
            interval += 2
        elif state == 'stop':
            break
        try:
            progress.update(int(min(99, (waited * 100) // expires_in)),
                            body + '[CR]' + i18n('device_login_waiting'))
        except Exception:
            pass
    progress.close()
    return 'failed', None


def _render_qr(verification_uri):
    if qr_render is None:
        return None
    try:
        if not xbmcvfs.exists(ADDON_DATA_DIR):
            xbmcvfs.mkdirs(ADDON_DATA_DIR)
        qr_path = os.path.join(ADDON_DATA_DIR, 'device_login_qr.png')
        return qr_render.generate_qr_png(verification_uri, qr_path, scale=8, border=4)
    except Exception as err:
        log_utils.log('QR render failed: %s' % repr(err), log_utils.LOGWARNING)
        return None


def _remove(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def _qr_login(heading, qr_path, verification_uri, user_code, expires_in, interval, poll):
    dialog = _QRLoginDialog()
    try:
        dialog.setup(heading, qr_path, verification_uri, user_code, expires_in, interval, poll)
        dialog.start_polling()
        dialog.doModal()
        dialog.stop = True
        return dialog.result, dialog.token
    finally:
        _remove(dialog.bg_path)
        del dialog


class _QRLoginDialog(xbmcgui.WindowDialog):
    def __init__(self):
        super(_QRLoginDialog, self).__init__()
        self.result = 'failed'
        self.token = None
        self.stop = False
        self.bg_path = None
        self._poll = None
        self._interval = 5
        self._expires_in = 1800
        self._thread = None

    def setup(self, heading, qr_path, verification_uri, user_code, expires_in, interval, poll):
        self._poll = poll
        self._interval = interval
        self._expires_in = expires_in

        width = self.getWidth()
        height = self.getHeight()
        center_x = width // 2

        panel_w = min(760, width - 40)
        panel_h = min(640, height - 40)
        panel_x = center_x - panel_w // 2
        panel_y = (height - panel_h) // 2

        qr_size = min(360, panel_h - 260)
        text_x = panel_x + 30
        text_w = panel_w - 60

        # Solid backdrop panel rendered to its own PNG so we don't rely on skin textures.
        if qr_render is not None:
            try:
                self.bg_path = os.path.join(ADDON_DATA_DIR, 'device_login_bg.png')
                qr_render.generate_solid_png(self.bg_path, 8, 8, value=20)
                self.addControl(xbmcgui.ControlImage(panel_x, panel_y, panel_w, panel_h,
                                                     self.bg_path, aspectRatio=0))
            except Exception:
                self.bg_path = None

        self.addControl(xbmcgui.ControlLabel(
            text_x, panel_y + 22, text_w, 40, heading,
            alignment=_ALIGN_CENTER_X, textColor='FFFFFFFF'))

        qr_x = center_x - qr_size // 2
        qr_y = panel_y + 74
        self.addControl(xbmcgui.ControlImage(qr_x, qr_y, qr_size, qr_size, qr_path, aspectRatio=0))

        info_y = qr_y + qr_size + 14
        self.addControl(xbmcgui.ControlLabel(
            text_x, info_y, text_w, 30, i18n('device_login_scan') % verification_uri,
            alignment=_ALIGN_CENTER_X, textColor='FFDDDDDD'))
        self.addControl(xbmcgui.ControlLabel(
            text_x, info_y + 36, text_w, 44, i18n('device_login_code') % user_code,
            alignment=_ALIGN_CENTER_X, textColor='FF9147FF'))
        self.addControl(xbmcgui.ControlLabel(
            text_x, info_y + 86, text_w, 30, i18n('device_login_waiting_cancel'),
            alignment=_ALIGN_CENTER_X, textColor='FFAAAAAA'))

    def start_polling(self):
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._thread.start()

    def _run(self):
        # Let doModal() take over before this thread is allowed to close the window.
        xbmc.sleep(400)
        start = time.time()
        while not self.stop:
            state, token = self._safe_poll()
            if state == 'ok':
                self.token = token
                self.result = 'ok'
                break
            if state == 'stop':
                self.result = 'failed'
                break
            if state == 'slow_down':
                self._interval += 2
            if time.time() - start >= self._expires_in:
                self.result = 'failed'
                break
            waited = 0.0
            while waited < self._interval and not self.stop:
                xbmc.sleep(500)
                waited += 0.5
        self.close()

    def _safe_poll(self):
        try:
            return self._poll()
        except Exception:
            return 'pending', None

    def onAction(self, action):
        if action.getId() in (ACTION_PREVIOUS_MENU, ACTION_NAV_BACK, ACTION_STOP):
            self.result = 'cancelled'
            self.stop = True
            self.close()


def route():
    do_device_login(heading=i18n('device_login'),
                    body_i18n='device_login_instructions',
                    client_id=utils.get_client_id(),
                    scopes=' '.join(SCOPES),
                    store_tokens=utils.store_oauth_tokens,
                    success_i18n='device_login_success',
                    log_tag='')
