# -*- coding: utf-8 -*-
"""

    This file is part of plugin.video.twitch

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import utils
from ..addon.constants import LIVE_PREVIEW_TEMPLATE


def route(notify=True):
    utils.TextureCacheCleaner().remove_like(LIVE_PREVIEW_TEMPLATE, notify)
