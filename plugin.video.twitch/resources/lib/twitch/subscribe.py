# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""Subscribing happens on the viewer's phone: the add-on only shows a QR code of the channel's subscribe page."""
import xbmc
import xbmcgui

from . import kodi, qr

PAGE = 'twitch.tv/subs/%s'
CLOSE = 15067  # Kodi's "Close"


def address(login):
    return PAGE % login.lower()


def _message(login, name):
    return kodi.formatted(30099, name, address(login))


def _wait_until_closed(dialog):
    monitor = xbmc.Monitor()
    while not dialog.iscanceled() and not monitor.waitForAbort(0.25):
        pass
    dialog.close()


def show(login, name):
    """The QR code of the channel's subscribe page, until the viewer closes it. Without a QR code (no
    script.module.pyqrcode), the address alone."""
    image = qr.image('https://www.' + address(login))
    if not image:
        xbmcgui.Dialog().ok(kodi.formatted(30098, name), _message(login, name))
        return
    dialog = qr.Dialog(image, button=CLOSE)
    dialog.create(kodi.formatted(30098, name), _message(login, name))
    _wait_until_closed(dialog)
