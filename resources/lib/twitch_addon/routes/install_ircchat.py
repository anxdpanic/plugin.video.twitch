# -*- coding: utf-8 -*-
"""

    This file is part of plugin.video.twitch

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon.common import kodi


def route():
    if kodi.get_kodi_version().major > 16:
        kodi.execute_builtin('InstallAddon(script.ircchat)')
    else:
        kodi.execute_builtin('RunPlugin(plugin://script.ircchat/)')
