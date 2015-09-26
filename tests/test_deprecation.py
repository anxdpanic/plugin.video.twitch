#-*- encoding: utf-8 -*-
from logging import WARNING

from twitch import TwitchTV, Twitch

from .support import unittest, LoggedTestCase


class TestDeprecation(LoggedTestCase):

    def test_warning_if_twitchtv(self):
        twitch = TwitchTV()
        self.assertLogCountEqual(count=1,
                msg="DEPRECATED call to 'TwitchTV' detected, please use 'Twitch' instead",
                level=WARNING)

    def test_no_warning_if_twitch(self):
        twitch = Twitch()
        self.assertLogCountEqual(count=0,
                msg="DEPRECATED call to 'TwitchTV' detected, please use 'Twitch' instead",
                level=WARNING)
