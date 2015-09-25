# -*- coding: utf-8 -*-
from __future__ import absolute_import

from logging import getLogger, StreamHandler, Formatter, INFO, DEBUG, WARNING

def setup_log(name, level=INFO):
    _log = getLogger(name)
    _log.setLevel(level)
    handler = StreamHandler()
    formatter = Formatter('%(asctime)s - %(levelname)s - [%(name)s] %(message)s')
    handler.setFormatter(formatter)
    _log.addHandler(handler)
    return _log

def deprecation_warning(logger, old, new):
    logger.warning("DEPRECATED call to '%s\' detected, "
                   "please use '%s' instead",
                   old, new)

log = setup_log('twitch')
