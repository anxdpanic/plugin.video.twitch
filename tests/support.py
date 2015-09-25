#-*- encoding: utf-8 -*-

import re
import unittest
from logging.handlers import BufferingHandler
from twitch.logging import setup_log
from twitch.logging import DEBUG

log = setup_log('twitch-debug', DEBUG)


class LogCountHandler(BufferingHandler):
    """Capturing and counting logged messages."""

    def __init__(self, capacity=1000):
        BufferingHandler.__init__(self, capacity)

    def count_logs(self, msg=None, level=None):
        return len([
            l
            for l
            in self.buffer
            if (msg is None or re.match(msg, l.getMessage())) and
               (level is None or l.levelno == level)
        ])

class LoggedTestCase(unittest.TestCase):
    """A test case that captures log messages."""

    def setUp(self):
        super(LoggedTestCase, self).setUp()
        self._logcount_handler = LogCountHandler()
        log.addHandler(self._logcount_handler)

    def tearDown(self):
        log.removeHandler(self._logcount_handler)
        super(LoggedTestCase, self).tearDown()

    def assertLogCountEqual(self, count=None, msg=None, **kwargs):
        actual = self._logcount_handler.count_logs(msg=msg, **kwargs)
        self.assertEqual(
            actual, count,
            msg='expected {} occurrences of {!r}, but found {}'.format(
                count, msg, actual))
