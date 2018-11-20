# -*- coding: utf-8 -*-
"""

    This file is part of plugin.video.twitch

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon.common import kodi
from ..addon.utils import i18n


def route(oauth_token):
    kodi.set_setting('oauth_token', oauth_token)
    kodi.notify(msg=i18n('token_updated'))
