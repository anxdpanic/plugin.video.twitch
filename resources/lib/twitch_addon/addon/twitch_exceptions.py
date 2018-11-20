# -*- coding: utf-8 -*-
"""

    Copyright (C) 2016 Twitch-on-Kodi

    This file is part of plugin.video.twitch

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from twitch.exceptions import ResourceUnavailableException

ResourceUnavailableException = ResourceUnavailableException


class TwitchException(Exception):
    pass


class SubRequired(Exception):
    pass


class NotFound(Exception):
    pass


class PlaybackFailed(Exception):
    pass
