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

from addon import utils, api, menu_items
from addon.common import kodi
from addon.converter import JsonListItemConverter
from addon.constants import DISPATCHER, MODES, LINE_LENGTH, LIVE_PREVIEW_TEMPLATE, Keys

i18n = utils.i18n

converter = JsonListItemConverter(LINE_LENGTH)
twitch = api.Twitch()


@DISPATCHER.register(MODES.MAIN)
def main():
    kodi.set_content('files')
    context_menu = list()
    context_menu.extend(menu_items.clear_previews())
    kodi.create_item({'label': i18n('featured_streams'), 'path': {'mode': MODES.FEATUREDSTREAMS}, 'context_menu': context_menu})
    kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.GAMES}})
    kodi.create_item({'label': i18n('channels'), 'path': {'mode': MODES.CHANNELS}, 'context_menu': context_menu})
    kodi.create_item({'label': i18n('following'), 'path': {'mode': MODES.FOLLOWING}})
    kodi.create_item({'label': i18n('search'), 'path': {'mode': MODES.SEARCH}, 'context_menu': context_menu})
    kodi.create_item({'label': i18n('settings'), 'path': {'mode': MODES.SETTINGS}})
    kodi.end_of_directory()


@DISPATCHER.register(MODES.SEARCH)
def search():
    kodi.set_content('files')
    kodi.create_item({'label': i18n('streams'), 'path': {'mode': MODES.NEWSEARCH, 'content': 'streams'}})
    kodi.create_item({'label': i18n('channels'), 'path': {'mode': MODES.NEWSEARCH, 'content': 'channels'}})
    kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.NEWSEARCH, 'content': 'games'}})
    kodi.create_item({'label': i18n('video_id_url'), 'path': {'mode': MODES.NEWSEARCH, 'content': 'id_url'}})
    kodi.end_of_directory()


@DISPATCHER.register(MODES.NEWSEARCH, args=['content'])
def new_search(content):
    kodi.set_content('files')
    user_input = kodi.get_keyboard(i18n('search'))
    if user_input:
        kodi.update_container(kodi.get_plugin_url({'mode': MODES.SEARCHRESULTS, 'content': content, 'query': user_input}))


@DISPATCHER.register(MODES.SEARCHRESULTS, args=['content', 'query'], kwargs=['index'])
def search_results(content, query, index=0):
    if content == 'streams':
        utils.refresh_previews()
        kodi.set_content('videos')
        index, offset, limit = utils.calculate_pagination_values(index)
        results = twitch.get_stream_search(query=query, offset=offset, limit=limit)
        for stream in results[Keys.STREAMS]:
            kodi.create_item(converter.stream_to_listitem(stream))
        if results[Keys.TOTAL] > (offset + limit):
            kodi.create_item(utils.link_to_next_page({'mode': MODES.SEARCHRESULTS, 'content': content, 'query': query, 'index': index}))
        kodi.end_of_directory()
    elif content == 'channels':
        kodi.set_content('files')
        index, offset, limit = utils.calculate_pagination_values(index)
        results = twitch.get_channel_search(query=query, offset=offset, limit=limit)
        for channel in results[Keys.CHANNELS]:
            kodi.create_item(converter.channel_to_listitem(channel))
        if results[Keys.TOTAL] > (offset + limit):
            kodi.create_item(utils.link_to_next_page({'mode': MODES.SEARCHRESULTS, 'content': content, 'query': query, 'index': index}))
        kodi.end_of_directory()
    elif content == 'games':
        kodi.set_content('files')
        results = twitch.get_game_search(query=query)
        for game in results[Keys.GAMES]:
            kodi.create_item(converter.game_to_listitem(game))
        kodi.end_of_directory()
    elif content == 'id_url':
        kodi.set_content('videos')
        video_id = utils.extract_video_id(query)
        results = twitch.get_video_by_id(video_id)
        if video_id.startswith('a') or video_id.startswith('c') or video_id.startswith('v'):
            kodi.create_item(converter.video_list_to_listitem(results))
            kodi.end_of_directory()


@DISPATCHER.register(MODES.FOLLOWING)
def following():
    kodi.set_content('files')
    context_menu = list()
    context_menu.extend(menu_items.clear_previews())
    kodi.create_item({'label': i18n('live_channels'), 'path': {'mode': MODES.FOLLOWED, 'content': 'live', 'context_menu': context_menu}})
    kodi.create_item({'label': i18n('channels'), 'path': {'mode': MODES.FOLLOWED, 'content': 'channels'}})
    kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.FOLLOWED, 'content': 'games'}})
    kodi.end_of_directory()


@DISPATCHER.register(MODES.FEATUREDSTREAMS)
def list_featured_streams():
    utils.refresh_previews()
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
    if games[Keys.TOTAL] > (offset + limit):
        kodi.create_item(utils.link_to_next_page({'mode': MODES.GAMES, 'index': index}))
    kodi.end_of_directory()


@DISPATCHER.register(MODES.CHANNELS, kwargs=['index'])
def list_all_channels(index=0):
    utils.refresh_previews()
    kodi.set_content('videos')
    index, offset, limit = utils.calculate_pagination_values(index)

    streams = twitch.get_all_channels(offset, limit)
    for stream in streams[Keys.STREAMS]:
        kodi.create_item(converter.stream_to_listitem(stream))
    if streams[Keys.TOTAL] > (offset + limit):
        kodi.create_item(utils.link_to_next_page({'mode': MODES.CHANNELS, 'index': index}))
    kodi.end_of_directory()


@DISPATCHER.register(MODES.FOLLOWED, args=['content'])
def list_followed(content):
    username = utils.get_username()
    if username:
        if content == 'live':
            utils.refresh_previews()
            kodi.set_content('videos')
            streams = twitch.get_following_streams(username)
            for stream in streams[Keys.LIVE]:
                kodi.create_item(converter.stream_to_listitem(stream))
            kodi.end_of_directory()
        elif content == 'channels':
            kodi.set_content('files')
            streams = twitch.get_following_streams(username)
            for followed in streams[Keys.OTHERS]:
                kodi.create_item(converter.channel_to_listitem(followed))
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
    kodi.set_content('videos')
    index, offset, limit = utils.calculate_pagination_values(index)

    videos = twitch.get_channel_videos(name, offset, limit, broadcast_type)
    for video in videos[Keys.VIDEOS]:
        kodi.create_item(converter.video_list_to_listitem(video))
    if videos[Keys.TOTAL] > (offset + limit):
        kodi.create_item(utils.link_to_next_page({'mode': MODES.CHANNELVIDEOLIST, 'name': name, 'broadcast_type': broadcast_type, 'index': index}))
    kodi.end_of_directory()


@DISPATCHER.register(MODES.GAMESTREAMS, args=['game'], kwargs=['index'])
def list_game_streams(game, index=0):
    utils.refresh_previews()
    kodi.set_content('videos')
    index, offset, limit = utils.calculate_pagination_values(index)

    streams = twitch.get_game_streams(game=game, offset=offset, limit=limit)
    for stream in streams[Keys.STREAMS]:
        kodi.create_item(converter.stream_to_listitem(stream))
    if streams[Keys.TOTAL] > (offset + limit):
        kodi.create_item(utils.link_to_next_page({'mode': MODES.GAMESTREAMS, 'game': game, 'index': index}))
    kodi.end_of_directory()


@DISPATCHER.register(MODES.PLAY, kwargs=['name', 'video_id', 'quality', 'use_player'])
def play(name=None, video_id=None, quality=-2, use_player=False):
    if (name is None) and (video_id is None): return
    video_quality = utils.get_video_quality(quality)
    if video_quality != -1:
        videos = item_dict = None
        if video_id:
            videos = twitch.get_vod(video_id)
            result = twitch.get_video_by_id(video_id)
            item_dict = converter.video_to_playitem(result)
        elif name:
            videos = twitch.get_live(name)
            result = twitch.get_channel_stream(name)[Keys.STREAMS][0]
            item_dict = converter.stream_to_playitem(result)
        if item_dict and videos:
            item_dict['path'] = twitch.get_video_for_quality(videos, video_quality)
            playback_item = kodi.create_item(item_dict, add=False)
            if use_player:
                kodi.Player().play(item_dict['path'], playback_item)
            else:
                kodi.set_resolved_url(playback_item)


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


@DISPATCHER.register(MODES.CLEARLIVEPREVIEWS, kwargs=['notify'])
def clear_live_previews(notify=True):
    utils.TextureCacheCleaner().remove_like(LIVE_PREVIEW_TEMPLATE, notify)
