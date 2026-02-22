# -*- coding: utf-8 -*-
"""
     
    Copyright (C) 2012-2019 Twitch-on-Kodi
    
    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

import re
import time

from base64 import b64decode
from datetime import datetime
from urllib.parse import quote_plus

from .common import kodi, json_store
from .strings import STRINGS
from .constants import CLIENT_ID, REDIRECT_URI, LIVE_PREVIEW_TEMPLATE, Images, ADDON_DATA_DIR, COLORS, Keys
from .search_history import StreamsSearchHistory, ChannelsSearchHistory, GamesSearchHistory, IdUrlSearchHistory

from twitch.api.parameters import Boolean, Period, ClipPeriod, Direction, Language, SortBy, VideoSort

import xbmcvfs

translations = kodi.Translations(STRINGS)
i18n = translations.i18n

if not xbmcvfs.exists(ADDON_DATA_DIR):
    mkdir_result = xbmcvfs.mkdir(ADDON_DATA_DIR)
storage = json_store.JSONStore(ADDON_DATA_DIR + 'storage.json')


def show_menu(menu, parent=None):
    setting_id = 'menu'
    if parent:
        setting_id += '_%s' % parent
    setting_id += '_%s' % menu
    return kodi.get_setting(setting_id) == 'true'


def to_string(value):
    return kodi.decode_utf8(value)


def loose_version(v):
    filled = []
    for point in v.split("."):
        filled.append(point.zfill(8))
    return tuple(filled)


def use_inputstream_adaptive():
    if kodi.get_setting('video_quality_ia') == 'true' or kodi.get_setting('video_quality') == '3':
        if kodi.get_setting('video_support_ia_builtin') == 'true':
            return True
        elif kodi.get_setting('video_support_ia_addon') == 'true':
            use_ia = kodi.get_setting('video_quality_ia') == 'true' or kodi.get_setting('video_quality') == '3'
            if not use_ia:
                return False

            ia_enabled = kodi.addon_enabled('inputstream.adaptive')
            if ia_enabled is False:
                if kodi.Dialog().yesno(kodi.get_name(), i18n('adaptive_is_disabled')):
                    ia_enabled = kodi.set_addon_enabled('inputstream.adaptive')

            if ia_enabled:
                ia_min_version = '2.0.10'
                ia_version = kodi.Addon('inputstream.adaptive').getAddonInfo('version')
                ia_enabled = loose_version(ia_version) >= loose_version(ia_min_version)
                if not ia_enabled:
                    result = kodi.Dialog().ok(kodi.get_name(), i18n('adaptive_version_check') % ia_min_version)

            if not ia_enabled:
                kodi.set_setting('video_quality_ia', 'false')
                kodi.set_setting('video_quality', '0')
                return False
            else:
                return True
        else:
            kodi.set_setting('video_quality_ia', 'false')
            kodi.set_setting('video_quality', '0')
            return False
    else:
        return False


def inputstream_adpative_supports(feature):
    try:
        ia_version = kodi.Addon('inputstream.adaptive').getAddonInfo('version')
    except RuntimeError:
        ia_version = '0.0.0'

    if feature == 'EXT-X-DISCONTINUITY':
        if loose_version(ia_version) >= loose_version('2.4.6'):
            return True

    return False


def append_headers(headers):
    from .common import log_utils
    
    log_utils.log('append_headers called with: %s' % headers, log_utils.LOGINFO)
    
    header_parts = []
    
    # Add existing headers
    if headers:
        header_parts.extend(['%s=%s' % (key, quote_plus(headers[key])) for key in headers])
    
    # Add proxy configuration if enabled
    proxy_config = get_proxy_dict()
    if proxy_config:
        proxy_url = proxy_config['http']
        # Try different proxy parameter formats that Kodi might support
        header_parts.append('http-proxy=%s' % quote_plus(proxy_url))
        # Also try these alternative formats
        header_parts.append('proxy=%s' % quote_plus(proxy_url))
        log_utils.log('Adding proxy to video URL: %s' % proxy_url, log_utils.LOGINFO)
    
    if header_parts:
        return '|%s' % '&'.join(header_parts)
    return ''


def get_redirect_uri():
    settings_id = kodi.get_setting('oauth_redirecturi')
    stripped_id = settings_id.strip()
    if settings_id != stripped_id:
        settings_id = stripped_id
        kodi.set_setting('oauth_redirecturi', settings_id)
    if settings_id:
        return kodi.decode_utf8(settings_id)
    else:
        return kodi.decode_utf8(REDIRECT_URI)


def get_twitch_client_id():
    """Get the user's Twitch App Client-ID from settings.
    
    This is the user's own registered Twitch application Client-ID,
    required for Helix API access and Device Auth flow.
    Returns empty string if not configured.
    """
    settings_id = kodi.get_setting('twitch_client_id')
    stripped_id = settings_id.strip()
    if settings_id != stripped_id:
        settings_id = stripped_id
        kodi.set_setting('twitch_client_id', settings_id)
    return kodi.decode_utf8(settings_id) if settings_id else ''


def get_twitch_client_secret():
    """Get the user's Twitch App Client Secret from settings.
    
    Required for token refresh. Without it, access tokens cannot be
    refreshed and the user must re-authenticate every ~4 hours.
    Returns empty string if not configured.
    """
    settings_val = kodi.get_setting('twitch_client_secret')
    stripped_val = settings_val.strip()
    if settings_val != stripped_val:
        settings_val = stripped_val
        kodi.set_setting('twitch_client_secret', settings_val)
    return kodi.decode_utf8(settings_val) if settings_val else ''


def get_hevc_token():
    """Get the HEVC token from settings (optional, for HEVC streams)"""
    token = kodi.get_setting('twitch_hevc_token').strip()
    if token:
        # Remove 'oauth:' prefix if present
        if token.lower().startswith('oauth:'):
            token = token[6:]
        elif ':' in token:
            idx = token.find(':')
            token = token[idx + 1:]
    return kodi.decode_utf8(token) if token else ""


# Legacy compatibility functions
def use_twitch_token():
    """Check if HEVC token is configured"""
    return bool(get_hevc_token())


def get_twitch_website_token():
    """Deprecated - use get_hevc_token() instead"""
    return get_hevc_token()


def use_custom_oauth():
    """Deprecated"""
    return use_twitch_token()


def get_client_id(default=False):
    """Get Client-ID for Helix API - uses the main twitch_client_id setting"""
    return get_twitch_client_id()


def get_client_secret():
    """Get Client Secret for token refresh - uses the twitch_client_secret setting"""
    return get_twitch_client_secret()


def clear_client_id():
    kodi.set_setting('oauth_clientid', '')


def get_oauth_token(token_only=True, required=False):
    from .common import log_utils
    # Note: Twitch Website Tokens do NOT work with Helix API
    # They only work with GQL/Private API (use get_private_oauth_token() for that)
    # So we do NOT use Twitch website token for Helix API calls
    
    oauth_token = kodi.get_setting('oauth_token_helix')
    if not oauth_token or not oauth_token.strip():
        if not required: return ''
        kodi.notify(kodi.get_name(), i18n('token_required'), sound=False)
        kodi.show_settings()
        oauth_token = kodi.get_setting('oauth_token_helix')
    stripped_token = oauth_token.strip()
    if oauth_token != stripped_token:
        oauth_token = stripped_token
        kodi.set_setting('oauth_token_helix', oauth_token)
    if oauth_token:
        if token_only:
            idx = oauth_token.find(':')
            if idx >= 0:
                oauth_token = oauth_token[idx + 1:]
        else:
            if not oauth_token.lower().startswith('oauth:'):
                idx = oauth_token.find(':')
                if idx >= 0:
                    oauth_token = oauth_token[idx + 1:]
                oauth_token = 'oauth:{0}'.format(oauth_token)
    return kodi.decode_utf8(oauth_token)


def get_private_oauth_token():
    """Get token for private/GQL API (HEVC streams)"""
    from .common import log_utils
    # Use HEVC token if available, otherwise fall back to main OAuth token
    hevc_token = get_hevc_token()
    if hevc_token:
        log_utils.log('get_private_oauth_token: Using HEVC token', log_utils.LOGDEBUG)
        return hevc_token
    
    # Fall back to main OAuth token
    oauth_token = get_oauth_token()
    if oauth_token:
        log_utils.log('get_private_oauth_token: Using main OAuth token', log_utils.LOGDEBUG)
        return oauth_token
    
    return ""


def get_private_client_id():
    """Get Client-ID for private/GQL API - always uses Twitch's web client ID.
    
    The GQL API (gql.twitch.tv) only accepts Twitch's own web client ID.
    Third-party app client IDs get rejected with 'The Client-ID header is invalid'.
    """
    return 'kimne78kx3ncx6brgo4mv6wki5h1ko'


def get_low_latency():
    """Check if low latency mode is enabled in settings"""
    return kodi.get_setting('low_latency') == 'true'


def get_watch_history_size():
    """Get the maximum number of watch history entries to keep"""
    try:
        size = int(kodi.get_setting('watch_history_size'))
        return max(0, min(size, 200))  # Clamp between 0 and 200
    except (ValueError, TypeError):
        return 50  # Default


def get_proxy_dict():
    from .common import log_utils
    
    if kodi.get_setting('proxy_enabled') != 'true':
        log_utils.log('Proxy is disabled in settings', log_utils.LOGINFO)
        return None
    
    proxy_host = kodi.get_setting('proxy_host').strip()
    proxy_port = kodi.get_setting('proxy_port')
    proxy_username = kodi.get_setting('proxy_username').strip()
    proxy_password = kodi.get_setting('proxy_password').strip()
    
    if not proxy_host:
        log_utils.log('Proxy host is empty', log_utils.LOGWARNING)
        return None
    
    proxy_url = 'http://'
    if proxy_username and proxy_password:
        proxy_url += '{username}:{password}@'.format(
            username=proxy_username,
            password=proxy_password
        )
        log_utils.log('Using proxy with authentication: {host}:{port}'.format(
            host=proxy_host, port=proxy_port or '8080'), log_utils.LOGINFO)
    else:
        log_utils.log('Using proxy without authentication: {host}:{port}'.format(
            host=proxy_host, port=proxy_port or '8080'), log_utils.LOGINFO)
    
    proxy_url += '{host}:{port}'.format(
        host=proxy_host,
        port=proxy_port or '8080'
    )
    
    return {
        'http': proxy_url,
        'https': proxy_url
    }


def get_search_history_size():
    return int(kodi.get_setting('search_history_size'))


def get_search_history(search_type):
    history = None
    history_size = get_search_history_size()
    if history_size > 0:
        if search_type == 'streams':
            history = StreamsSearchHistory(max_items=history_size)
        elif search_type == 'channels':
            history = ChannelsSearchHistory(max_items=history_size)
        elif search_type == 'games':
            history = GamesSearchHistory(max_items=history_size)
        elif search_type == 'id_url':
            history = IdUrlSearchHistory(max_items=history_size)
    return history


def get_items_per_page():
    return int(kodi.get_setting('items_per_page'))


def get_thumbnail_size():
    size_map = [Keys.SOURCE, Keys.LARGE, Keys.MEDIUM, Keys.SMALL]
    return size_map[int(kodi.get_setting('thumbnail_size'))]


def get_vodcast_color():
    color = int(kodi.get_setting('vodcast_highlight'))
    color = COLORS.split('|')[color]
    return kodi.decode_utf8(color)


def the_art(art=None):
    if not art:
        art = {}
    return {'icon': art.get('icon', Images.ICON),
            'thumb': art.get('thumb', Images.THUMB),
            'poster': art.get('poster', Images.POSTER),
            'banner': art.get('banner', Images.BANNER),
            'fanart': art.get('fanart', Images.FANART),
            'clearart': art.get('clearart', Images.CLEARART),
            'clearlogo': art.get('clearlogo', Images.CLEARLOGO),
            'landscape': art.get('landscape', Images.LANDSCAPE)}


def link_to_next_page(queries):
    return {'label': i18n('next_page'),
            'art': the_art(),
            'path': kodi.get_plugin_url(queries),
            'info': {'plot': i18n('next_page')}}


def irc_enabled():
    return (kodi.get_setting('irc_enable') == 'true') and kodi.has_addon('script.ircchat')


def exec_irc_script(username, channel):
    if not irc_enabled():
        return
    password = get_oauth_token(token_only=False, required=True)
    if username and password:
        host = 'irc.chat.twitch.tv'
        builtin = 'RunScript(script.ircchat, run_irc=True&nickname=%s&username=%s&password=%s&host=%s&channel=#%s)' % \
                  (username, username, password, host, channel)
        kodi.execute_builtin(builtin)


def notify_refresh():
    if kodi.get_setting('notify_refresh') == 'false':
        return False
    return True


def refresh_previews():
    refresh_interval = int(kodi.get_setting('refresh_interval')) * 60
    if refresh_interval > 0:
        if not get_refresh_stamp():
            set_refresh_stamp()
            return
        if get_refresh_diff() >= refresh_interval:
            set_refresh_stamp()
    else:
        clear_refresh_stamp()


def clear_refresh_stamp():
    window = kodi.Window(10000)
    window.clearProperty(key='%s-lpr_stamp' % kodi.get_id())


def set_refresh_stamp():
    window = kodi.Window(10000)
    window.setProperty(key='%s-lpr_stamp' % kodi.get_id(), value=str(datetime.now()))


def get_refresh_stamp():
    window = kodi.Window(10000)
    return window.getProperty(key='%s-lpr_stamp' % kodi.get_id())


def strptime(stamp, stamp_fmt):
    import _strptime
    try:
        time.strptime('01 01 2012', '%d %m %Y')  # dummy call
    except:
        pass
    return time.strptime(stamp, stamp_fmt)


def get_stamp_diff(current_stamp):
    stamp_format = '%Y-%m-%d %H:%M:%S.%f'
    current_datetime = datetime.now()
    if not current_stamp: return 86400  # 24 hrs
    try:
        stamp_datetime = datetime(*(strptime(current_stamp, stamp_format)[0:6]))
    except ValueError:  # current_stamp has no microseconds
        stamp_format = '%Y-%m-%d %H:%M:%S'
        stamp_datetime = datetime(*(strptime(current_stamp, stamp_format)[0:6]))

    time_delta = current_datetime - stamp_datetime
    total_seconds = 0
    if time_delta:
        total_seconds = ((time_delta.seconds + time_delta.days * 24 * 3600) * 10 ** 6) / 10 ** 6
    return total_seconds


def get_refresh_diff():
    return get_stamp_diff(get_refresh_stamp())


def extract_video(url):
    video_id = None
    seek_time = 0
    id_string = url  # http://twitch.tv/a/v/12345678?t=9m1s
    idx = id_string.find('?')
    if idx >= 0:
        id_string = id_string[:idx]  # https://twitch.tv/a/v/12345678
    idx = id_string.rfind('/')
    if idx >= 0:
        id_string = id_string[:idx] + id_string[idx + 1:]  # https://twitch.tv/a/v12345678
    idx = id_string.rfind('/')
    if idx >= 0:
        id_string = id_string[idx + 1:]  # v12345678
    if id_string.startswith("videos"):  # videos12345678
        id_string = "v" + id_string[6:]  # v12345678
    start_time = url  # http://twitch.tv/a/v/12345678?t=9m1s
    idx = url.find('?')
    if idx >= 0:
        time_string = start_time[idx:]  # t=9m1s
        pattern = re.compile('t=(?:(?P<hours>[0-9]+)(?:h))?(?:(?P<minutes>[0-9]+)(?:m))?(?:(?P<seconds>[0-9]+)(?:s))?')
        match = re.search(pattern, time_string)
        if match:
            hours = match.group('hours')
            minutes = match.group('minutes')
            seconds = match.group('seconds')
            if hours:
                seek_time += int(hours) * 3600
            if minutes:
                seek_time += int(minutes) * 60
            if seconds:
                seek_time += int(seconds)

    return id_string, seek_time


_sorting_defaults = \
    {
        'followed_channels':
            {
                'by': SortBy.LAST_BROADCAST,
                'direction': Direction.DESC,
                'period': None
            },
        'channel_videos':
            {
                'by': VideoSort.TIME,
                'direction': None,
                'period': None
            },
        'clips':
            {
                'by': Boolean.TRUE,
                'direction': None,
                'period': ClipPeriod.WEEK
            },
        'top_videos':
            {
                'by': None,
                'direction': None,
                'period': Period.WEEK
            }
    }


def get_stored_json():
    json_data = storage.load()
    needs_save = False
    if 'qualities' not in json_data:
        json_data['qualities'] = {'stream': [], 'video': [], 'clip': []}
        needs_save = True
    if 'sorting' not in json_data:
        json_data['sorting'] = _sorting_defaults
        needs_save = True
    if 'languages' not in json_data:
        json_data['languages'] = Language.ALL
        needs_save = True
    if 'languages' in json_data and isinstance(json_data['languages'], list):
        if len(json_data['languages']) == 1:
            json_data['languages'] = json_data['languages'][0]
        else:
            json_data['languages'] = Language.ALL
        needs_save = True
    if needs_save:
        storage.save(json_data)
    return json_data


def get_language():
    json_data = get_stored_json()
    language = json_data['languages']
    if language == 'all':
        language = ''
    return language


def change_language(language=Language.ALL):
    json_data = get_stored_json()
    language = Language.validate(language)
    json_data['languages'] = language
    storage.save(json_data)


def get_sort(for_type, key=None):
    json_data = get_stored_json()
    sorting = json_data['sorting'].get(for_type)
    if not sorting:
        return None
    if key and key in json_data['sorting'][for_type]:
        return json_data['sorting'][for_type][key]
    else:
        return json_data['sorting'][for_type]


def set_sort(for_type, sort_by, direction, period):
    json_data = get_stored_json()
    sorting = json_data['sorting'].get(for_type)
    if not sorting:
        if for_type in _sorting_defaults:
            json_data['sorting'][for_type] = _sorting_defaults[for_type]
        else:
            return False
    json_data['sorting'][for_type] = {'by': sort_by, 'direction': direction, 'period': period}
    storage.save(json_data)
    return True


def get_default_quality(content_type, target_id):
    json_data = get_stored_json()
    if content_type not in json_data['qualities']:
        json_data['qualities'][content_type] = []
    if any(str(target_id) in item for item in json_data['qualities'][content_type]):
        return next(item for item in json_data['qualities'][content_type] if str(target_id) in item)
    else:
        return None


def add_default_quality(content_type, target_id, name, quality):
    json_data = get_stored_json()
    current_quality = get_default_quality(content_type, target_id)
    if current_quality:
        current_quality = current_quality[target_id]['quality']
        if current_quality.lower() == quality.lower():
            return False
        else:
            index = next(index for index, item in enumerate(json_data['qualities'][content_type]) if str(target_id) in item)
            del json_data['qualities'][content_type][index]
    json_data['qualities'][content_type].append({target_id: {'name': name, 'quality': quality}})
    storage.save(json_data)
    return True


def remove_default_quality(content_type):
    json_data = get_stored_json()
    result = kodi.Dialog().select(i18n('remove_default_quality') % content_type,
                                  ['%s [%s]' % (user[user.keys()[0]]['name'], user[user.keys()[0]]['quality']) for user in json_data['qualities'][content_type]])
    if result == -1:
        return None
    else:
        result = json_data['qualities'][content_type].pop(result)
        storage.save(json_data)
        return result


def clear_list(list_type, list_name):
    json_data = get_stored_json()
    if (list_name in json_data) and (list_type in json_data[list_name]):
        json_data[list_name][list_type] = []
        storage.save(json_data)
        return True
    else:
        return False


def convert_duration(duration):
    payload = 0

    pattern = re.compile('(?:(?P<hours>[0-9]+)(?:h))?(?:(?P<minutes>[0-9]+)(?:m))?(?:(?P<seconds>[0-9]+)(?:s))?')
    match = re.search(pattern, duration)

    if match:
        hours = match.group('hours')
        minutes = match.group('minutes')
        seconds = match.group('seconds')
        if hours:
            payload += int(hours) * 3600
        if minutes:
            payload += int(minutes) * 60
        if seconds:
            payload += int(seconds)

    return payload


class TitleBuilder(object):
    class Templates(object):
        TITLE = u"{title}"
        STREAMER = u"{streamer}"
        STREAMER_TITLE = u"{streamer} - {title}"
        VIEWERS_STREAMER_TITLE = u"{viewers} - {streamer} - {title}"
        STREAMER_GAME_TITLE = u"{streamer} - {game} - {title}"
        GAME_VIEWERS_STREAMER_TITLE = u"[{game}] {viewers} | {streamer} - {title}"
        GAME_STREAMER_TITLE = u"[{game}] | {streamer} - {title}"
        BROADCASTER_LANGUAGE_STREAMER_TITLE = u"{broadcaster_language} | {streamer} - {title}"
        ELLIPSIS = u'...'

    def __init__(self, line_length):
        self.line_length = line_length

    def format_title(self, title_values):
        title_setting = int(kodi.get_setting('title_display'))
        template = self.get_title_template(title_setting, title_values)

        for key, value in title_values.items():
            title_values[key] = self.clean_title_value(value)
        title = template.format(**title_values)

        return self.truncate_title(title)

    @staticmethod
    def get_title_template(title_setting, title_values):
        options = {
            0: TitleBuilder.Templates.STREAMER_TITLE,
            1: TitleBuilder.Templates.VIEWERS_STREAMER_TITLE,
            2: TitleBuilder.Templates.TITLE,
            3: TitleBuilder.Templates.STREAMER,
            4: TitleBuilder.Templates.STREAMER_GAME_TITLE,
            5: TitleBuilder.Templates.GAME_VIEWERS_STREAMER_TITLE,
            6: TitleBuilder.Templates.BROADCASTER_LANGUAGE_STREAMER_TITLE,
            7: TitleBuilder.Templates.GAME_STREAMER_TITLE,
        }

        if title_setting == 1:
            if not title_values.get('viewers'):
                title_setting = 0
        elif title_setting == 4:
            if not title_values.get('game'):
                title_setting = 0
        elif title_setting == 5:
            if not title_values.get('game') and not title_values.get('viewers'):
                title_setting = 0
            elif title_values.get('game') and not title_values.get('viewers'):
                title_setting = 7
            elif not title_values.get('game') and title_values.get('viewers'):
                title_setting = 1
        elif title_setting == 6:
            if not title_values.get('broadcaster_language'):
                title_setting = 0

        return options.get(title_setting, TitleBuilder.Templates.STREAMER)

    @staticmethod
    def clean_title_value(value):
        if isinstance(value, str):
            try:
                value = value.decode('utf-8', 'ignore')
            except (UnicodeEncodeError, AttributeError) as e:
                pass
            value = value.replace(u'\r\n', u' ')
            value = value.replace(u'\n', u' ')
            value = value.strip()
            return value
        else:
            return value

    def truncate_title(self, title):
        truncate_setting = kodi.get_setting('title_truncate') == 'true'

        if truncate_setting:
            short_title = title[:self.line_length]
            ending = (title[self.line_length:] and TitleBuilder.Templates.ELLIPSIS)
            return short_title + ending
        return title
