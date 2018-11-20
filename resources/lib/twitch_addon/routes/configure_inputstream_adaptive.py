# -*- coding: utf-8 -*-
"""

    This file is part of plugin.video.twitch

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import utils
from ..addon.common import kodi


def route():
    use_ia = utils.use_inputstream_adaptive()
    if use_ia:
        if kodi.get_setting('video_support_ia_addon') == 'true':
            kodi.Addon(id='inputstream.adaptive').openSettings()
