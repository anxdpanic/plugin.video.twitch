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
from addon.constants import DISPATCHER, MODES, LINE_LENGTH, LIVE_PREVIEW_TEMPLATE, SCOPES, Keys
from addon.googl_shorten import googl_url
from addon.error_handling import error_handler, TwitchException

i18n = utils.i18n

converter = JsonListItemConverter(LINE_LENGTH)
twitch = api.Twitch()


@DISPATCHER.register(MODES.MAIN)
@error_handler
def main():
    has_token = True if utils.get_oauth_token() else False
    kodi.set_content('files')
    context_menu = list()
    context_menu.extend(menu_items.clear_previews())
    kodi.create_item({'label': i18n('featured_streams'), 'path': {'mode': MODES.FEATUREDSTREAMS}, 'context_menu': context_menu})
    if has_token:
        kodi.create_item({'label': i18n('following'), 'path': {'mode': MODES.FOLLOWING}})
    kodi.create_item({'label': i18n('channels'), 'path': {'mode': MODES.CHANNELS}, 'context_menu': context_menu})
    kodi.create_item({'label': i18n('communities'), 'path': {'mode': MODES.COMMUNITIES}})
    kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.GAMES}})
    kodi.create_item({'label': i18n('search'), 'path': {'mode': MODES.SEARCH}, 'context_menu': context_menu})
    kodi.create_item({'label': i18n('settings'), 'path': {'mode': MODES.SETTINGS}})
    kodi.end_of_directory()


@DISPATCHER.register(MODES.SEARCH)
@error_handler
def search():
    kodi.set_content('files')
    kodi.create_item({'label': i18n('streams'), 'path': {'mode': MODES.NEWSEARCH, 'content': 'streams'}})
    kodi.create_item({'label': i18n('channels'), 'path': {'mode': MODES.NEWSEARCH, 'content': 'channels'}})
    kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.NEWSEARCH, 'content': 'games'}})
    kodi.create_item({'label': i18n('video_id_url'), 'path': {'mode': MODES.NEWSEARCH, 'content': 'id_url'}})
    kodi.end_of_directory()


@DISPATCHER.register(MODES.NEWSEARCH, args=['content'])
@error_handler
def new_search(content):
    kodi.set_content('files')
    user_input = kodi.get_keyboard(i18n('search'))
    if user_input:
        kodi.update_container(kodi.get_plugin_url({'mode': MODES.SEARCHRESULTS, 'content': content, 'query': user_input}))


@DISPATCHER.register(MODES.SEARCHRESULTS, args=['content', 'query'], kwargs=['index'])
@error_handler
def search_results(content, query, index=0):
    if content == 'streams':
        utils.refresh_previews()
        kodi.set_content('videos')
        index, offset, limit = utils.calculate_pagination_values(index)
        results = twitch.get_stream_search(query=query, offset=offset, limit=limit)
        if (results[Keys.TOTAL] > 0) and (Keys.STREAMS in results):
            for stream in results[Keys.STREAMS]:
                kodi.create_item(converter.stream_to_listitem(stream))
            if results[Keys.TOTAL] > (offset + limit):
                kodi.create_item(utils.link_to_next_page({'mode': MODES.SEARCHRESULTS, 'content': content, 'query': query, 'index': index}))
            kodi.end_of_directory()
        else:
            kodi.refresh_container()
    elif content == 'channels':
        kodi.set_content('files')
        index, offset, limit = utils.calculate_pagination_values(index)
        results = twitch.get_channel_search(query=query, offset=offset, limit=limit)
        if (results[Keys.TOTAL] > 0) and (Keys.CHANNELS in results):
            for channel in results[Keys.CHANNELS]:
                kodi.create_item(converter.channel_to_listitem(channel))
            if results[Keys.TOTAL] > (offset + limit):
                kodi.create_item(utils.link_to_next_page({'mode': MODES.SEARCHRESULTS, 'content': content, 'query': query, 'index': index}))
            kodi.end_of_directory()
        else:
            kodi.refresh_container()
    elif content == 'games':
        kodi.set_content('files')
        results = twitch.get_game_search(query=query)
        if Keys.GAMES in results:
            for game in results[Keys.GAMES]:
                kodi.create_item(converter.game_to_listitem(game))
            kodi.end_of_directory()
        else:
            kodi.refresh_container()
    elif content == 'id_url':
        kodi.set_content('videos')
        video_id = utils.extract_video_id(query)
        results = twitch.get_video_by_id(video_id)
        if video_id.startswith('a') or video_id.startswith('c') or video_id.startswith('v'):
            kodi.create_item(converter.video_list_to_listitem(results))
            kodi.end_of_directory()
        else:
            kodi.refresh_container()


@DISPATCHER.register(MODES.FOLLOWING)
@error_handler
def following():
    kodi.set_content('files')
    context_menu = list()
    context_menu.extend(menu_items.clear_previews())
    kodi.create_item({'label': i18n('live_channels'), 'path': {'mode': MODES.FOLLOWED, 'content': 'live', 'context_menu': context_menu}})
    kodi.create_item({'label': i18n('channels'), 'path': {'mode': MODES.FOLLOWED, 'content': 'channels'}})
    kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.FOLLOWED, 'content': 'games'}})
    kodi.end_of_directory()


@DISPATCHER.register(MODES.FEATUREDSTREAMS)
@error_handler
def list_featured_streams():
    utils.refresh_previews()
    kodi.set_content('videos')

    streams = twitch.get_featured_streams()
    if Keys.FEATURED in streams:
        for stream in streams[Keys.FEATURED]:
            kodi.create_item(converter.stream_to_listitem(stream[Keys.STREAM]))
        kodi.end_of_directory()


@DISPATCHER.register(MODES.GAMES, kwargs=['index'])
@error_handler
def list_all_games(index=0):
    kodi.set_content('files')
    index, offset, limit = utils.calculate_pagination_values(index)

    games = twitch.get_top_games(offset, limit)
    if (games[Keys.TOTAL] > 0) and (Keys.TOP in games):
        for element in games[Keys.TOP]:
            kodi.create_item(converter.game_to_listitem(element[Keys.GAME]))
        if games[Keys.TOTAL] > (offset + limit):
            kodi.create_item(utils.link_to_next_page({'mode': MODES.GAMES, 'index': index}))
        kodi.end_of_directory()


@DISPATCHER.register(MODES.COMMUNITIES, kwargs=['index'])
@error_handler
def list_all_communities(index=0):
    kodi.set_content('files')
    index, offset, limit = utils.calculate_pagination_values(index)
    communities = twitch.get_top_communities(index, limit)
    if (communities[Keys.TOTAL] > 0) and (Keys.COMMUNITIES in communities):
        for element in communities[Keys.COMMUNITIES]:
            kodi.create_item(converter.community_to_listitem(element))
        if communities[Keys.TOTAL] > (offset + limit):
            kodi.create_item(utils.link_to_next_page({'mode': MODES.COMMUNITIES, 'index': index}))
        kodi.end_of_directory()


@DISPATCHER.register(MODES.CHANNELS, kwargs=['index'])
@error_handler
def list_all_channels(index=0):
    utils.refresh_previews()
    kodi.set_content('videos')
    index, offset, limit = utils.calculate_pagination_values(index)

    streams = twitch.get_all_channels(offset, limit)
    if (streams[Keys.TOTAL] > 0) and (Keys.STREAMS in streams):
        for stream in streams[Keys.STREAMS]:
            kodi.create_item(converter.stream_to_listitem(stream))
        if streams[Keys.TOTAL] > (offset + limit):
            kodi.create_item(utils.link_to_next_page({'mode': MODES.CHANNELS, 'index': index}))
        kodi.end_of_directory()


@DISPATCHER.register(MODES.FOLLOWED, args=['content'])
@error_handler
def list_followed(content):
    user = twitch.get_user()
    user_id = user.get(Keys.ID, None)
    username = user.get(Keys.NAME, None)
    if user_id:
        if content == 'live':
            utils.refresh_previews()
            kodi.set_content('videos')
            streams = twitch.get_following_streams(user_id)
            if Keys.LIVE in streams:
                for stream in streams[Keys.LIVE]:
                    kodi.create_item(converter.stream_to_listitem(stream))
                kodi.end_of_directory()
        elif content == 'channels':
            kodi.set_content('files')
            streams = twitch.get_following_streams(user_id)
            if Keys.OTHERS in streams:
                for followed in streams[Keys.OTHERS]:
                    kodi.create_item(converter.channel_to_listitem(followed))
                kodi.end_of_directory()
        elif content == 'games':
            if username:
                kodi.set_content('files')
                games = twitch.get_followed_games(username)
                if Keys.FOLLOWS in games:
                    for game in games[Keys.FOLLOWS]:
                        kodi.create_item(converter.game_to_listitem(game))
                    kodi.end_of_directory()


@DISPATCHER.register(MODES.CHANNELVIDEOS, args=['channel_id'])
@error_handler
def list_channel_video_types(channel_id):
    kodi.set_content('files')
    kodi.create_item({'label': i18n('past_broadcasts'), 'path': {'mode': MODES.CHANNELVIDEOLIST, 'channel_id': channel_id, 'broadcast_type': 'archive'}})
    kodi.create_item({'label': i18n('uploads'), 'path': {'mode': MODES.CHANNELVIDEOLIST, 'channel_id': channel_id, 'broadcast_type': 'upload'}})
    kodi.create_item({'label': i18n('video_highlights'), 'path': {'mode': MODES.CHANNELVIDEOLIST, 'channel_id': channel_id, 'broadcast_type': 'highlight'}})
    kodi.end_of_directory()


@DISPATCHER.register(MODES.CHANNELVIDEOLIST, args=['channel_id', 'broadcast_type'], kwargs=['index'])
@error_handler
def list_channel_videos(channel_id, broadcast_type, index=0):
    kodi.set_content('videos')
    index, offset, limit = utils.calculate_pagination_values(index)

    videos = twitch.get_channel_videos(channel_id, offset, limit, broadcast_type)
    if (videos[Keys.TOTAL] > 0) and (Keys.VIDEOS in videos):
        for video in videos[Keys.VIDEOS]:
            kodi.create_item(converter.video_list_to_listitem(video))
        if videos[Keys.TOTAL] > (offset + limit):
            kodi.create_item(utils.link_to_next_page({'mode': MODES.CHANNELVIDEOLIST, 'channel_id': channel_id, 'broadcast_type': broadcast_type, 'index': index}))
        kodi.end_of_directory()


@DISPATCHER.register(MODES.GAMESTREAMS, args=['game'], kwargs=['index'])
@error_handler
def list_game_streams(game, index=0):
    utils.refresh_previews()
    kodi.set_content('videos')
    index, offset, limit = utils.calculate_pagination_values(index)

    streams = twitch.get_game_streams(game=game, offset=offset, limit=limit)
    if (streams[Keys.TOTAL] > 0) and (Keys.STREAMS in streams):
        for stream in streams[Keys.STREAMS]:
            kodi.create_item(converter.stream_to_listitem(stream))
        if streams[Keys.TOTAL] > (offset + limit):
            kodi.create_item(utils.link_to_next_page({'mode': MODES.GAMESTREAMS, 'game': game, 'index': index}))
        kodi.end_of_directory()


@DISPATCHER.register(MODES.COMMUNITYSTREAMS, args=['community_id'], kwargs=['index'])
@error_handler
def list_community_streams(community_id, index=0):
    utils.refresh_previews()
    kodi.set_content('videos')
    index, offset, limit = utils.calculate_pagination_values(index)

    streams = twitch.get_community_streams(community_id=community_id, offset=offset, limit=limit)
    if (streams[Keys.TOTAL] > 0) and (Keys.STREAMS in streams):
        for stream in streams[Keys.STREAMS]:
            kodi.create_item(converter.stream_to_listitem(stream))
        if streams[Keys.TOTAL] > (offset + limit):
            kodi.create_item(utils.link_to_next_page({'mode': MODES.GAMESTREAMS, 'community_id': community_id, 'index': index}))
        kodi.end_of_directory()


@DISPATCHER.register(MODES.PLAY, kwargs=['name', 'channel_id', 'video_id', 'source', 'use_player'])
@error_handler
def play(name=None, channel_id=None, video_id=None, source=True, use_player=False):
    if (name is None or channel_id is None) and (video_id is None): return
    videos = item_dict = None
    if video_id:
        videos = twitch.get_vod(video_id)
        result = twitch.get_video_by_id(video_id)
        item_dict = converter.video_to_playitem(result)
    elif name and channel_id:
        videos = twitch.get_live(name)
        result = twitch.get_channel_stream(channel_id)[Keys.STREAMS][0]
        item_dict = converter.stream_to_playitem(result)
    if item_dict and videos:
        if source:
            source = kodi.get_setting('video_quality') == '0'
        play_url = twitch.get_video_for_quality(videos, source)
        if play_url:
            item_dict['path'] = play_url
            playback_item = kodi.create_item(item_dict, add=False)
            if use_player:
                kodi.Player().play(item_dict['path'], playback_item)
            else:
                kodi.set_resolved_url(playback_item)
            user = twitch.get_user()
            username = user.get(Keys.NAME, None)
            if username:
                utils.exec_irc_script(username, name)


@DISPATCHER.register(MODES.EDITFOLLOW, args=['channel_id', 'channel_name'])
@error_handler
def edit_user_follows(channel_id, channel_name):
    try:
        result = twitch.follow_status(channel_id)
        is_following = True
    except TwitchException as error:
        if '404' not in error.message: raise
        is_following = False

    if is_following:
        result = twitch.unfollow(channel_id)
        kodi.notify(msg=i18n('unfollowed') % channel_name, sound=False)
    else:
        result = twitch.follow(channel_id)
        kodi.notify(msg=i18n('now_following') % channel_name, sound=False)


@DISPATCHER.register(MODES.SETTINGS, kwargs=['refresh'])
@error_handler
def settings(refresh=True):
    kodi.show_settings()
    if refresh:
        kodi.refresh_container()


@DISPATCHER.register(MODES.RESETCACHE)
@error_handler
def reset_cache():
    confirmed = kodi.Dialog().yesno(i18n('confirm'), i18n('cache_reset_confirm'))
    if confirmed:
        result = utils.cache.reset_cache()
        if result:
            kodi.notify(msg=i18n('cache_reset_succeeded'), sound=False)
        else:
            kodi.notify(msg=i18n('cache_reset_failed'), sound=False)


@DISPATCHER.register(MODES.CLEARLIVEPREVIEWS, kwargs=['notify'])
@error_handler
def clear_live_previews(notify=True):
    utils.TextureCacheCleaner().remove_like(LIVE_PREVIEW_TEMPLATE, notify)


@DISPATCHER.register(MODES.INSTALLIRCCHAT)
@error_handler
def install_ircchat():
    if kodi.get_kodi_version().major > 16:
        kodi.execute_builtin('InstallAddon(script.ircchat)')
    else:
        kodi.execute_builtin('RunPlugin(plugin://script.ircchat/)')


@DISPATCHER.register(MODES.TOKENURL)
@error_handler
def get_token_url():
    request_url = twitch.client.prepare_request_uri(scope=SCOPES)
    try:
        short_url = googl_url(request_url)
    except:
        short_url = None
    prompt_url = short_url if short_url else request_url
    result = kodi.Dialog().ok(heading=i18n('authorize_heading'), line1=i18n('authorize_message'),
                              line2=' %s' % prompt_url)
    kodi.show_settings()
