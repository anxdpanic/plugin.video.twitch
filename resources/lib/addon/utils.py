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

import sys
import time
from datetime import datetime
from base64 import b64decode
from common import kodi, cache
from strings import STRINGS
from tccleaner import TextureCacheCleaner
from constants import CLIENT_ID, REDIRECT_URI, LIVE_PREVIEW_TEMPLATE, Images

translations = kodi.Translations(STRINGS)
i18n = translations.i18n

cache = cache
cache_limit = int(kodi.get_setting('cache_expire_time')) / 60
cache.cache_enabled = cache_limit > 0


def get_redirect_uri():
    settings_id = kodi.get_setting('oauth_redirecturi')
    stripped_id = settings_id.strip()
    if settings_id != stripped_id:
        settings_id = stripped_id
        kodi.set_setting('oauth_redirecturi', settings_id)
    if settings_id:
        return settings_id.decode('utf-8')
    else:
        return REDIRECT_URI.decode('utf-8')


def get_client_id():
    settings_id = kodi.get_setting('oauth_clientid')
    stripped_id = settings_id.strip()
    if settings_id != stripped_id:
        settings_id = stripped_id
        kodi.set_setting('oauth_clientid', settings_id)
    if settings_id:
        return settings_id.decode('utf-8')
    else:
        return b64decode(CLIENT_ID).decode('utf-8')


def get_oauth_token(token_only=True, required=False):
    oauth_token = kodi.get_setting('oauth_token')
    if not oauth_token or not oauth_token.strip():
        if not required: return ''
        kodi.notify(kodi.get_name(), i18n('token_required'), sound=False)
        kodi.show_settings()
        oauth_token = kodi.get_setting('oauth_token')
    stripped_token = oauth_token.strip()
    if oauth_token != stripped_token:
        oauth_token = stripped_token
        kodi.set_setting('oauth_token', oauth_token)
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
    return oauth_token.decode('utf-8')


def get_items_per_page():
    return int(kodi.get_setting('items_per_page'))


def calculate_pagination_values(index):
    index = int(index)
    limit = get_items_per_page()
    offset = index * limit
    return index, offset, limit


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
    queries['index'] += 1
    return {'label': i18n('next_page'),
            'art': the_art(),
            'path': kodi.get_plugin_url(queries)}


def exec_irc_script(username, channel):
    if kodi.get_setting('irc_enable') != 'true':
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
    if kodi.get_setting('live_previews_enable') != 'true':
        return
    if kodi.get_setting('refresh_previews') == 'true':
        refresh_interval = int(kodi.get_setting('refresh_interval')) * 60
        if get_refresh_diff() >= refresh_interval:
            set_refresh_stamp()
            TextureCacheCleaner().remove_like(LIVE_PREVIEW_TEMPLATE, notify_refresh())


def set_refresh_stamp():
    builtin = 'SetProperty({key}, {value}, 10000)'
    kodi.execute_builtin(builtin.format(key='%s-lpr_stamp' % kodi.get_id(), value=datetime.now()))


def get_refresh_stamp():
    return kodi.get_info_label('Window(10000).Property({key})'.format(key='%s-lpr_stamp' % kodi.get_id()))


def get_refresh_diff():
    stamp_format = '%Y-%m-%d %H:%M:%S.%f'
    current_datetime = datetime.now()
    current_stamp = get_refresh_stamp()
    if not current_stamp: return 86400  # 24 hrs
    stamp_datetime = datetime(*(time.strptime(current_stamp, stamp_format)[0:6]))  # datetime.strptime has issues
    time_delta = current_datetime - stamp_datetime
    total_seconds = 0
    if time_delta:
        total_seconds = ((time_delta.seconds + time_delta.days * 24 * 3600) * 10 ** 6) / 10 ** 6
    return total_seconds


def extract_video_id(url):
    video_id = url  # http://twitch.tv/a/v/12345678?t=9m1s
    idx = video_id.find('?')
    if idx >= 0:
        video_id = video_id[:idx]  # https://twitch.tv/a/v/12345678
    idx = video_id.rfind('/')
    if idx >= 0:
        video_id = video_id[:idx] + video_id[idx + 1:]  # https://twitch.tv/a/v12345678
    idx = video_id.rfind('/')
    if idx >= 0:
        video_id = video_id[idx + 1:]  # v12345678
    if video_id.startswith("videos"):  # videos12345678
        video_id = "v" + video_id[6:]  # v12345678
    return video_id


class TitleBuilder(object):
    class Templates(object):
        TITLE = u"{title}"
        STREAMER = u"{streamer}"
        STREAMER_TITLE = u"{streamer} - {title}"
        VIEWERS_STREAMER_TITLE = u"{viewers} - {streamer} - {title}"
        STREAMER_GAME_TITLE = u"{streamer} - {game} - {title}"
        GAME_VIEWERS_STREAMER_TITLE = u"[{game}] {viewers} | {streamer} - {title}"
        ELLIPSIS = u'...'

    def __init__(self, line_length):
        self.line_length = line_length

    def format_title(self, title_values):
        title_setting = int(kodi.get_setting('title_display'))
        template = self.get_title_template(title_setting)

        for key, value in title_values.iteritems():
            title_values[key] = self.clean_title_value(value)
        title = template.format(**title_values)

        return self.truncate_title(title)

    @staticmethod
    def get_title_template(title_setting):
        options = {0: TitleBuilder.Templates.STREAMER_TITLE,
                   1: TitleBuilder.Templates.VIEWERS_STREAMER_TITLE,
                   2: TitleBuilder.Templates.TITLE,
                   3: TitleBuilder.Templates.STREAMER,
                   4: TitleBuilder.Templates.STREAMER_GAME_TITLE,
                   5: TitleBuilder.Templates.GAME_VIEWERS_STREAMER_TITLE}
        return options.get(title_setting, TitleBuilder.Templates.STREAMER)

    @staticmethod
    def clean_title_value(value):
        if isinstance(value, basestring):
            return unicode(value).replace('\r\n', ' ').strip()
        else:
            return value

    def truncate_title(self, title):
        truncate_setting = kodi.get_setting('title_truncate') == 'true'

        if truncate_setting:
            short_title = title[:self.line_length]
            ending = (title[self.line_length:] and TitleBuilder.Templates.ELLIPSIS)
            return short_title + ending
        return title
