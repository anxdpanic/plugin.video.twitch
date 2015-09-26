# -*- encoding: utf-8 -*-

from twitch.app import Twitch
from twitch.exceptions import TwitchException  # NOQA
from twitch.logging import deprecation_warning, log

__all__ = ["Twitch", "TwitchException"]
VERSION = '0.5.0'


def TwitchTV(logger=log):
    deprecation_warning(logger, 'TwitchTV', 'Twitch')
    return Twitch(logger)
