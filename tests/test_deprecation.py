#-*- encoding: utf-8 -*-

from support import unittest, LoggedTestCase
from support import log

from twitch import TwitchTV, Twitch
from twitch.logging import INFO, DEBUG, WARNING

class TestDeprecation(LoggedTestCase):

    def test_warning_if_twitchtv(self):
        twitch = TwitchTV(log)
        self.assertLogCountEqual(count=1,
                msg="DEPRECATED call to 'TwitchTV' detected, please use 'Twitch' instead",
                level=WARNING)

    def test_no_warning_if_twitch(self):
        twitch = Twitch(log)
        self.assertLogCountEqual(count=0,
                msg="DEPRECATED call to 'TwitchTV' detected, please use 'Twitch' instead",
                level=WARNING)
