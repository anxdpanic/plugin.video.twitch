# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2024 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon.common import kodi
from ..addon.watch_history import get_watch_history
from ..addon.utils import i18n


def route(content_type=None, content_id=None, clear_all=False):
    """Clear watch history entries
    
    Args:
        content_type: Type of content to remove ('stream', 'video', 'clip')
        content_id: Specific content ID to remove
        clear_all: If True, clear all history after confirmation
    """
    watch_history = get_watch_history()
    
    if clear_all == 'true' or clear_all is True:
        # Confirm before clearing all
        if kodi.Dialog().yesno(i18n('watch_history'), i18n('confirm_clear_history')):
            watch_history.clear()
            kodi.notify(kodi.get_name(), i18n('watch_history_cleared'), sound=False)
            kodi.refresh_container()
    elif content_type and content_id:
        # Remove specific entry
        watch_history.remove(content_type, content_id)
        kodi.notify(kodi.get_name(), i18n('removed_from_history'), sound=False)
        kodi.refresh_container()
