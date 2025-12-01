# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from twitch.exceptions import ResourceUnavailableException

ResourceUnavailableException = ResourceUnavailableException


class TwitchException(Exception):
    pass


class SubRequired(Exception):
    """Raised when subscription is required to view content"""
    pass


class NotFound(Exception):
    """Raised when requested content is not found"""
    pass


class PlaybackFailed(Exception):
    """Raised when video playback fails"""
    pass


class StreamOffline(Exception):
    """Raised when trying to watch a stream that is offline"""
    pass


class TokenExpired(Exception):
    """Raised when OAuth token has expired"""
    pass


class RateLimited(Exception):
    """Raised when API rate limit is exceeded"""
    pass


class NetworkError(Exception):
    """Raised when network connection fails"""
    pass


class QualityUnavailable(Exception):
    """Raised when requested video quality is not available"""
    pass
