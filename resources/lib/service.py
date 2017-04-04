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

from ast import literal_eval
from itertools import izip_longest
from urllib2 import quote, unquote
from addon.common import kodi, log_utils
from addon.constants import Keys
from addon.utils import BlacklistFilter, i18n
from addon import api
import xbmc

blacklist_filter = BlacklistFilter()


def grouped(items):
    args = [iter(items)] * 3
    return izip_longest(fillvalue='', *args)


def notify_live():
    notify = kodi.get_setting('live_notify') == 'true'
    audible = False
    if notify:
        audible = kodi.get_setting('live_notify_audible') == 'true'
    return notify, audible


def get_followed_streams(twitch_api):
    streams = {Keys.TOTAL: 0}
    offset = 0
    all_followed = {Keys.STREAMS: []}
    while (streams[Keys.TOTAL] > (offset - 100)) or (not xbmc.abortRequested):
        if offset > 0:
            kodi.sleep(1000)
        streams = twitch_api.get_followed_streams(stream_type='live', offset=offset, limit=100)
        if (streams[Keys.TOTAL] > 0) and (Keys.STREAMS in streams):
            for stream in streams[Keys.STREAMS]:
                all_followed[Keys.STREAMS].append(stream)
            if streams[Keys.TOTAL] <= offset:
                break
            else:
                offset += 100
    filtered = \
        blacklist_filter.by_type(all_followed, Keys.STREAMS, parent_keys=[Keys.CHANNEL], id_key=Keys._ID, list_type='user')
    filtered = \
        blacklist_filter.by_type(filtered, Keys.STREAMS, game_key=Keys.GAME, list_type='game')
    followed_tuples = [(stream[Keys.CHANNEL][Keys._ID], stream[Keys.CHANNEL][Keys.NAME], stream[Keys.CHANNEL][Keys.DISPLAY_NAME]) for stream in filtered[Keys.STREAMS]]
    return followed_tuples


def set_online_followed(value):
    builtin = 'SetProperty({key}, {value}, 10000)'
    kodi.execute_builtin(builtin.format(key='%s-online_followers' % kodi.get_id(), value=quote(str(value))))


def get_online_followed():
    result = unquote(kodi.get_info_label('Window(10000).Property({key})'.format(key='%s-online_followers' % kodi.get_id())))
    if result:
        return literal_eval(result)
    else:
        return result


# ---------------------------------------------------------------------------------------


start_time = -1
sleep_time = 500
delay_time = 300000

log_utils.log('Service: Start', log_utils.LOGNOTICE)

while not xbmc.abortRequested:
    if (start_time != -1) and (start_time <= delay_time):
        start_time += sleep_time
    else:
        start_time = 0
        twitch = api.Twitch()
        has_token = True if twitch.access_token else False
        do_notification, make_audible = notify_live()
        if has_token and do_notification:
            current_live = get_followed_streams(twitch)
            if xbmc.abortRequested: break  # if aborted during api requests
            current_online = get_online_followed()
            if not current_online:
                log_utils.log('Service: Now online |%s|' % current_live, log_utils.LOGDEBUG)
                set_online_followed(value=current_live)
                names = [display_name for _id, name, display_name in current_live]
                triplets = grouped(names)
                for followed_names in triplets:
                    message = ', '.join(followed_names)
                    message = message.rstrip(', ').rstrip(', ')
                    kodi.notify(i18n('currently_live'), message, sound=make_audible)
            else:
                log_utils.log('Service: Was online |%s|' % current_online, log_utils.LOGDEBUG)
                current_online = [match for match in current_online if match in current_live]
                new_online = [match for match in current_live if match not in current_online]
                log_utils.log('Service: New online |%s|' % new_online, log_utils.LOGDEBUG)
                names = [display_name for _id, name, display_name in new_online]
                triplets = grouped(names)
                for followed_names in triplets:
                    message = ', '.join(followed_names)
                    message = message.rstrip(', ').rstrip(', ')
                    kodi.notify(i18n('went_live'), message, sound=make_audible)
                current_online += new_online
                log_utils.log('Service: Now online |%s|' % current_online, log_utils.LOGDEBUG)
                set_online_followed(current_online)
    kodi.sleep(sleep_time)

log_utils.log('Service: Shutdown', log_utils.LOGNOTICE)
