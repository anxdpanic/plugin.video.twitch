# -*- coding: utf-8 -*-
"""

    This file is part of plugin.video.twitch

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon.common import kodi
from ..addon.constants import Scripts


def route():
    kodi.execute_builtin('RunScript(%s)' % Scripts.REFRESH)

