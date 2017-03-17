# -*- coding: utf-8 -*-
"""

    Copyright (C) 2016 Twitch-on-Kodi

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import json
from functools import wraps
from common import kodi, log_utils
from twitch.exceptions import ResourceUnavailableException
import utils

i18n = utils.i18n


class TwitchException(Exception):
    pass


def error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except ResourceUnavailableException as error:
            log_utils.log('Error: Resource not available |{0}|'.format(error.message), log_utils.LOGERROR)
            kodi.notify(i18n('error'), error.message, duration=7000, sound=False)
        except TwitchException as error:
            log_utils.log('Error: |{0}|'.format(error.message), log_utils.LOGERROR)
            kodi.notify(i18n('error'), error.message, duration=7000, sound=False)

    return wrapper


def api_error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            try:
                logging_result = json.dumps(result, indent=4)
            except:
                logging_result = result
            log_utils.log(logging_result, log_utils.LOGDEBUG)
            if 'error' in result:
                message = '[Status {0}] {1}'.format(result['status'], result['message'])
                raise TwitchException(message)
            if not result or (isinstance(result, dict) and ('_total' in result) and (int(result['_total'] == 0))):
                raise TwitchException('No results returned')
            return result
        except ResourceUnavailableException:
            raise

    return wrapper
