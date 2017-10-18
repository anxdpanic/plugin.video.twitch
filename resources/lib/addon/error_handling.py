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

import copy
import json
import re
from functools import wraps
import utils
from common import kodi, log_utils
from twitch_exceptions import TwitchException, SubRequired, ResourceUnavailableException, NotFound, PlaybackFailed

i18n = utils.i18n


def __mask_client_id(client_id):
    return client_id[:4] + ('*' * (len(client_id) - 8)) + client_id[(len(client_id) - 4):]


def __mask_auth_header(auth_header):
    token = re.search(r'(?:OAuth|Bearer)\s(?P<token>.+)', auth_header)
    if token:
        token = token.group('token')
        masked_auth_header = re.sub(r'(OAuth|Bearer)\s.+', r'\1 ' + token[:4] + ('*' * (len(token) - 8)) + token[(len(token) - 4):], auth_header)
    else:
        masked_auth_header = '*' * 30

    return masked_auth_header


def error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except ResourceUnavailableException as error:
            log_utils.log('Connection failed |{0}|'.format(error.message), log_utils.LOGERROR)
            kodi.notify(i18n('connection_failed'), error.message, duration=7000, sound=False)
        except SubRequired as error:
            log_utils.log('Requires subscription to |{0}|'.format(error.message), log_utils.LOGDEBUG)
            kodi.notify(kodi.get_name(), i18n('subscription_required') % error.message, duration=5000, sound=False)
        except NotFound as error:
            log_utils.log('Not found |{0}|'.format(error.message), log_utils.LOGDEBUG)
            kodi.notify(kodi.get_name(), i18n('none_found') % error.message.lower(), duration=5000, sound=False)
        except PlaybackFailed as error:
            log_utils.log('Playback Failed |{0}|'.format(error.message), log_utils.LOGDEBUG)
            kodi.notify(kodi.get_name(), i18n('playback_failed'), duration=5000, sound=False)
        except TwitchException as error:
            _error = ''
            try:
                _message = error.message
                _error = _message['error']
                message = '[{0}] {1}'.format(_message['status'], _message['message'])
            except:
                message = error.message
            log_utils.log('Error |{0}| |{1}|'.format(_error, message.strip()), log_utils.LOGERROR)
            kodi.notify(_error if _error else i18n('error'), message.strip(), duration=7000, sound=False)

    return wrapper


def api_error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            logging_result = copy.deepcopy(result)
            try:
                if 'headers' in logging_result:
                    if 'Authorization' in logging_result['headers']:
                        logging_result['headers']['Authorization'] = __mask_auth_header(logging_result['headers']['Authorization'])
                    if 'Client-ID' in logging_result['headers']:
                        logging_result['headers']['Client-ID'] = __mask_client_id(logging_result['headers']['Client-ID'])
                if u'email' in logging_result:
                    logging_result[u'email'] = 'addon@removed.org'
                if u'token' in logging_result:
                    if u'client_id' in logging_result[u'token']:
                        logging_result[u'token'][u'client_id'] = __mask_client_id(logging_result[u'token'][u'client_id'])
                logging_result = json.dumps(logging_result, indent=4)
            except:
                pass
            log_utils.log(logging_result, log_utils.LOGDEBUG)
            return result
        except:
            raise

    return wrapper
