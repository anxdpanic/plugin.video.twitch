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
from constants import CLIENT_ID, CLIENT_SECRET, MODES, LIVE_PREVIEW_TEMPLATE, Images
from tccleaner import TextureCacheCleaner

translations = kodi.Translations(STRINGS)
i18n = translations.i18n

cache = cache
cache_limit = int(kodi.get_setting('cache_expire_time')) / 60
cache.cache_enabled = cache_limit > 0


def get_client_id_secret():
    settings_id = kodi.get_setting('oauth_client_id')
    settings_secret = kodi.get_setting('oauth_client_secret')
    stripped_id = settings_id.strip()
    stripped_secret = settings_secret.strip()
    if settings_id != stripped_id:
        settings_id = stripped_id
        kodi.set_setting('oauth_client_id', settings_id)
    if settings_secret != stripped_secret:
        settings_secret = stripped_secret
        kodi.set_setting('oauth_client_secret', settings_secret)

    if settings_id and settings_secret:
        return {'client_id': settings_id.decode('utf-8'), 'secret': settings_secret.decode('utf-8')}
    else:
        return {'client_id': b64decode(CLIENT_ID).decode('utf-8'), 'secret': b64decode(CLIENT_SECRET).decode('utf-8')}


def get_oauth_token(token_only=True):
    oauth_token = kodi.get_setting('oauth_token')
    if not oauth_token or not oauth_token.strip():
        kodi.show_settings()
        oauth_token = kodi.get_setting('oauth_token')
    stripped_token = oauth_token.strip()
    if oauth_token != stripped_token:
        oauth_token = stripped_token
        kodi.set_setting('oauth_token', oauth_token)
    if oauth_token:
        if token_only:
            oauth_token = oauth_token.replace('oauth:', '')
        else:
            if not oauth_token.lower().startswith('oauth:'):
                oauth_token = 'oauth:{0}'.format(oauth_token)
    return oauth_token.decode('utf-8')


def get_username():
    username = kodi.get_setting('username').lower()
    if not username or not username.strip():
        kodi.notify(kodi.get_name(), i18n('username_required'), sound=False)
        kodi.show_settings()
        username = kodi.get_setting('username')
    formatted_username = username.lower().strip()
    if username != formatted_username:
        username = formatted_username
        kodi.set_setting('username', username)

    return username


def get_items_per_page():
    return int(kodi.get_setting('items_per_page'))


def calculate_pagination_values(index):
    index = int(index)
    limit = get_items_per_page()
    offset = index * limit
    return index, offset, limit


def get_video_quality(quality=''):
    """
    :param quality: string int/int: qualities[quality]
    qualities
    0 = Source, 1 = 1080p60, 2 = 1080p30, 3 = 720p60, 4 = 720p30, 5 = 540p30, 6 = 480p30, 7 = 360p30, 8 = 240p30, 9 = 144p30
    -1 = Choose quality dialog
    * any other value for quality will use add-on setting
    i18n: 0 - 9
    """
    qualities = {'-1': -1, '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9}
    i18n_qualities = [i18n('source'), i18n('1080p60'), i18n('1080p30'), i18n('720p60'), i18n('720p30'),
                      i18n('540p30'), i18n('480p30'), i18n('360p30'), i18n('240p30'), i18n('144p30')]
    try:
        quality = int(quality)
        if 9 >= quality >= 0:
            chosen_quality = str(quality)
        elif quality == -1:
            chosen_quality = str(kodi.Dialog().select(i18n('play_choose_quality'), i18n_qualities))
        else:
            raise ValueError
    except ValueError:
        chosen_quality = kodi.get_setting('video')

    if chosen_quality == '-1':
        # chosen_quality == '-1' if dialog was cancelled
        return int(chosen_quality)
    else:
        return qualities.get(chosen_quality, sys.maxint)


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


def exec_irc_script(channel):
    if kodi.get_setting('irc_enable') != 'true':
        return
    username = kodi.get_setting('irc_username')
    password = get_oauth_token(token_only=False)
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


def context_clear_previews():
    context_menu = []
    if kodi.get_setting('live_previews_enable') == 'true':
        context_menu.extend([(i18n('clear_live_preview'), 'RunPlugin(%s)' %
                              kodi.get_plugin_url({'mode': MODES.CLEARLIVEPREVIEWS, 'notify': notify_refresh()}))])
    return context_menu


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
