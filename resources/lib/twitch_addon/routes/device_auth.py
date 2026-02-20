# -*- coding: utf-8 -*-
"""
    Device Authentication Route

    Copyright (C) 2026 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

from ..addon import utils
from ..addon.common import kodi
from ..addon.device_auth import show_device_auth_dialog, clear_device_tokens, get_device_tokens

i18n = utils.i18n


def route_connect(api):
    """
    Start the Device Code Authentication flow.
    Shows a dialog with the user code and waits for authorization.
    """
    # Check if user has entered their Client-ID
    client_id = utils.get_client_id()
    if not client_id:
        kodi.Dialog().ok(
            i18n('device_auth_title'),
            i18n('client_id_required')
        )
        kodi.show_settings()
        return
    
    result = show_device_auth_dialog(client_id=client_id)
    
    if result:
        # Refresh the settings dialog to show updated state
        kodi.execute_builtin('Container.Refresh')


def route_disconnect(api):
    """
    Disconnect the Twitch account by clearing saved tokens.
    """
    tokens = get_device_tokens()
    
    if not tokens or not tokens.get('access_token'):
        kodi.notify(kodi.get_name(), i18n('device_auth_disconnected'), sound=False)
        return
    
    # Ask for confirmation
    dialog = kodi.Dialog()
    confirmed = dialog.yesno(
        i18n('device_auth_title'),
        i18n('device_auth_disconnect_confirm')
    )
    
    if confirmed:
        clear_device_tokens()
        kodi.notify(kodi.get_name(), i18n('device_auth_disconnected'), sound=False)
        kodi.execute_builtin('Container.Refresh')
