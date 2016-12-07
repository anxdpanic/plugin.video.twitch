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

from addon.constants import DISPATCHER, MODES, LINE_LENGTH, Keys
from addon.common import kodi
from addon import utils, api
from addon.converter import JsonListItemConverter

i18n = utils.i18n

converter = JsonListItemConverter(LINE_LENGTH)
twitch = api.Twitch()


@DISPATCHER.register(MODES.MAIN)
def main():
    kodi.set_content('files')
    kodi.create_item({'label': i18n('featured_streams'), 'path': {'mode': MODES.FEATUREDSTREAMS}})
    kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.GAMES}})
    kodi.create_item({'label': i18n('channels'), 'path': {'mode': MODES.CHANNELS}})
    kodi.create_item({'label': i18n('following'), 'path': {'mode': MODES.FOLLOWING}})
    kodi.create_item({'label': i18n('search'), 'path': {'mode': MODES.SEARCH}})
    kodi.create_item({'label': i18n('settings'), 'path': {'mode': MODES.SETTINGS}})
    kodi.end_of_directory()


@DISPATCHER.register(MODES.FOLLOWING)
def following():
    kodi.set_content('files')
    kodi.create_item({'label': i18n('live_channels'), 'path': {'mode': MODES.FOLLOWED, 'content': 'live'}})
    kodi.create_item({'label': i18n('channels'), 'path': {'mode': MODES.FOLLOWED, 'content': 'channels'}})
    kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.FOLLOWED, 'content': 'games'}})
    kodi.end_of_directory()


@DISPATCHER.register(MODES.FEATUREDSTREAMS)
def list_featured_streams():
    kodi.set_content('videos')

    streams = twitch.get_featured_streams()
    for stream in streams[Keys.FEATURED]:
        kodi.create_item(converter.stream_to_listitem(stream[Keys.STREAM]))

    kodi.end_of_directory()


@DISPATCHER.register(MODES.GAMES, kwargs=['index'])
def list_all_games(index=0):
    kodi.set_content('files')
    index, offset, limit = utils.calculate_pagination_values(index)

    games = twitch.get_top_games(offset, limit)
    for element in games[Keys.TOP]:
        kodi.create_item(converter.game_to_listitem(element[Keys.GAME]))

    kodi.create_item(utils.link_to_next_page({'mode': MODES.GAMES, 'index': index}))
    kodi.end_of_directory()


@DISPATCHER.register(MODES.CHANNELS, kwargs=['index'])
def list_all_channels(index=0):
    kodi.set_content('files')
    index, offset, limit = utils.calculate_pagination_values(index)

    streams = twitch.get_all_channels(offset, limit)
    for stream in streams[Keys.STREAMS]:
        kodi.create_item(converter.stream_to_listitem(stream))

    kodi.create_item(utils.link_to_next_page({'mode': MODES.CHANNELS, 'index': index}))
    kodi.end_of_directory()


@DISPATCHER.register(MODES.FOLLOWED, args=['content'])
def list_followed(content):
    username = utils.get_username()
    if username:
        if content == 'live':
            kodi.set_content('videos')
            streams = twitch.get_following_streams(username)
            for stream in streams[Keys.LIVE]:
                kodi.create_item(converter.stream_to_listitem(stream))
            kodi.end_of_directory()
        elif content == 'channels':
            kodi.set_content('files')
            streams = twitch.get_following_streams(username)
            for follower in streams[Keys.OTHERS]:
                kodi.create_item(converter.followers_to_listitem(follower))
            kodi.end_of_directory()
        elif content == 'games':
            kodi.set_content('files')
            games = twitch.get_followed_games(username)
            for game in games[Keys.FOLLOWS]:
                kodi.create_item(converter.game_to_listitem(game))
            kodi.end_of_directory()


@DISPATCHER.register(MODES.CHANNELVIDEOS, args=['name'])
def list_channel_video_types(name):
    kodi.set_content('files')
    kodi.create_item({'label': i18n('past_broadcasts'), 'path': {'mode': MODES.CHANNELVIDEOLIST, 'name': name, 'broadcast_type': 'archive'}})
    kodi.create_item({'label': i18n('uploads'), 'path': {'mode': MODES.CHANNELVIDEOLIST, 'name': name, 'broadcast_type': 'upload'}})
    kodi.create_item({'label': i18n('video_highlights'), 'path': {'mode': MODES.CHANNELVIDEOLIST, 'name': name, 'broadcast_type': 'highlight'}})
    kodi.end_of_directory()


@DISPATCHER.register(MODES.CHANNELVIDEOLIST, args=['name', 'broadcast_type'], kwargs=['index'])
def list_channel_videos(name, broadcast_type, index=0):
    index = int(index)
    limit = utils.get_items_per_page()
    offset = index * limit
    kodi.set_content('videos')
    videos = twitch.get_channel_videos(name, offset, limit, broadcast_type)
    for video in videos[Keys.VIDEOS]:
        kodi.create_item(converter.video_list_to_listitem(video))
    if videos[Keys.TOTAL] > (offset + limit):
        kodi.create_item(utils.link_to_next_page({'mode': MODES.CHANNELVIDEOLIST, 'name': name, 'broadcast_type': broadcast_type, 'index': index}))
    kodi.end_of_directory()


@DISPATCHER.register(MODES.SETTINGS, kwargs=['refresh'])
def settings(refresh=True):
    kodi.show_settings()
    if refresh:
        kodi.refresh_container()


@DISPATCHER.register(MODES.RESETCACHE)
def reset_cache():
    confirmed = kodi.Dialog().yesno(i18n('confirm'), i18n('cache_reset_confirm'))
    if confirmed:
        result = utils.cache.reset_cache()
        if result:
            kodi.notify(msg=i18n('cache_reset_succeeded'), sound=False)
        else:
            kodi.notify(msg=i18n('cache_reset_failed'), sound=False)
