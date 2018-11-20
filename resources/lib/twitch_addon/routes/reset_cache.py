# -*- coding: utf-8 -*-
"""

    This file is part of plugin.video.twitch

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import cache
from ..addon.common import kodi
from ..addon.utils import i18n


def route():
    confirmed = kodi.Dialog().yesno(i18n('confirm'), i18n('cache_reset_confirm'))
    if confirmed:
        result = cache.reset_cache()
        if result:
            kodi.notify(msg=i18n('cache_reset_succeeded'), sound=False)
        else:
            kodi.notify(msg=i18n('cache_reset_failed'), sound=False)
