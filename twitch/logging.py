# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging

log = logging.getLogger('twitch')


def deprecation_warning(logger, old, new):
    logger.warning("DEPRECATED call to '%s\' detected, "
                   "please use '%s' instead",
                   old, new)
