# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

from ast import literal_eval
from copy import deepcopy
from functools import wraps
import traceback

from . import utils
from .common import kodi, log_utils
from .twitch_exceptions import (
    TwitchException, SubRequired, ResourceUnavailableException, 
    NotFound, PlaybackFailed, StreamOffline, TokenExpired,
    RateLimited, NetworkError, QualityUnavailable
)

i18n = utils.i18n


def get_friendly_error_message(error_code, error_message=''):
    """Convert technical error codes to user-friendly messages"""
    error_map = {
        401: 'error_unauthorized',
        403: 'error_forbidden',
        404: 'error_not_found',
        429: 'error_rate_limited',
        500: 'error_server',
        502: 'error_server',
        503: 'error_server',
        504: 'error_timeout',
    }
    
    # Check for specific error patterns in message
    if error_message:
        error_lower = error_message.lower()
        if 'vod_manifest_restricted' in error_lower or 'unauthorized_entitlements' in error_lower:
            return 'error_sub_only_vod'
        if 'token' in error_lower and ('invalid' in error_lower or 'expired' in error_lower):
            return 'error_token_expired'
        if 'rate limit' in error_lower:
            return 'error_rate_limited'
        if 'not found' in error_lower:
            return 'error_not_found'
        if 'offline' in error_lower:
            return 'error_stream_offline'
    
    return error_map.get(error_code, 'error_unknown')


# types
# 0 - nothing (just notify)
# 1 - directory (send end_of_directory)
def error_handler(func=None, route_type=0):
    def _real_dec(func):    
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result
            except ResourceUnavailableException as error:
                message = str(error)
                log_utils.log('Connection failed |{0}|'.format(message), log_utils.LOGERROR)
                # More user-friendly network error message
                kodi.notify(i18n('connection_failed'), i18n('error_network_check'), duration=7000, sound=False)
            except SubRequired as error:
                message = str(error)
                log_utils.log('Requires subscription to |{0}|'.format(message), log_utils.LOGDEBUG)
                kodi.notify(kodi.get_name(), i18n('subscription_required') % message, duration=5000, sound=False)
            except StreamOffline as error:
                message = str(error)
                log_utils.log('Stream offline |{0}|'.format(message), log_utils.LOGDEBUG)
                kodi.notify(kodi.get_name(), i18n('error_stream_offline'), duration=5000, sound=False)
            except TokenExpired as error:
                log_utils.log('Token expired', log_utils.LOGWARNING)
                kodi.notify(kodi.get_name(), i18n('error_token_expired'), duration=7000, sound=False)
            except RateLimited as error:
                log_utils.log('Rate limited by Twitch API', log_utils.LOGWARNING)
                kodi.notify(kodi.get_name(), i18n('error_rate_limited'), duration=5000, sound=False)
            except NetworkError as error:
                message = str(error)
                log_utils.log('Network error |{0}|'.format(message), log_utils.LOGERROR)
                kodi.notify(i18n('connection_failed'), i18n('error_network_check'), duration=7000, sound=False)
            except QualityUnavailable as error:
                message = str(error)
                log_utils.log('Quality unavailable |{0}|'.format(message), log_utils.LOGDEBUG)
                kodi.notify(kodi.get_name(), i18n('error_quality_unavailable'), duration=5000, sound=False)
            except NotFound as error:
                message = str(error)
                log_utils.log('Not found |{0}|'.format(message), log_utils.LOGDEBUG)
                kodi.notify(kodi.get_name(), i18n('none_found') % message.lower(), duration=5000, sound=False)
            except PlaybackFailed as error:
                message = str(error)
                log_utils.log('Playback Failed |{0}|'.format(message), log_utils.LOGDEBUG)
                kodi.notify(kodi.get_name(), i18n('playback_failed'), duration=5000, sound=False)
                kodi.set_resolved_url(kodi.ListItem(), succeeded=False)
            except TwitchException as error:
                _error = ''
                _message = ''
                _status = 0
                try:
                    error_data = literal_eval(str(deepcopy(error)).strip(','))
                    _error = error_data.get('error', '')
                    _message = error_data.get('message', '')
                    _status = error_data.get('status', 0)
                except:
                    _message = str(error)
                
                # Get friendly message based on status code
                friendly_key = get_friendly_error_message(_status, _message)
                friendly_msg = i18n(friendly_key)
                
                # Fall back to original message if translation not found
                if friendly_msg == friendly_key:
                    if _error and _message:
                        friendly_msg = '[{0}] {1}'.format(_status, _message) if _status else _message
                    else:
                        friendly_msg = str(error)
                
                log_utils.log('Error |{0}| |{1}| |{2}|'.format(_error, _status, _message), log_utils.LOGERROR)
                kodi.notify(_error if _error else i18n('error'), friendly_msg.strip(), duration=7000, sound=False)
            except Exception as error:
                # Catch-all for unexpected errors
                log_utils.log('Unexpected error: {0}'.format(traceback.format_exc()), log_utils.LOGERROR)
                kodi.notify(i18n('error'), i18n('error_unexpected'), duration=7000, sound=False)
            if route_type==1:
                kodi.end_of_directory(succeeded=False)
        return wrapper
    
    if func:
        return _real_dec(func)
    return _real_dec


def api_error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except:
            raise

    return wrapper
