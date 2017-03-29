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
from addon.googl_shorten import googl_url
from addon.error_handling import error_handler, TwitchException

i18n = utils.i18n

converter = JsonListItemConverter(LINE_LENGTH)
twitch = api.Twitch()


@DISPATCHER.register(MODES.MAIN)
@error_handler
def main():
    has_token = True if twitch.access_token else False
    kodi.set_content('files')
    context_menu = list()
    context_menu.extend(menu_items.clear_previews())
    kodi.create_item({'label': i18n('featured_streams'), 'path': {'mode': MODES.FEATUREDSTREAMS}, 'context_menu': context_menu})
    if has_token:
        kodi.create_item({'label': i18n('following'), 'path': {'mode': MODES.FOLLOWING}})
    kodi.create_item({'label': i18n('browse'), 'path': {'mode': MODES.BROWSE}, 'context_menu': context_menu})
    kodi.create_item({'label': i18n('search'), 'path': {'mode': MODES.SEARCH}, 'context_menu': context_menu})
    kodi.create_item({'label': i18n('settings'), 'path': {'mode': MODES.SETTINGS}})
    kodi.end_of_directory()


@DISPATCHER.register(MODES.BROWSE)
@error_handler
def browse():
    kodi.set_content('files')
    context_menu = list()
    context_menu.extend(menu_items.clear_previews())
    kodi.create_item({'label': i18n('live_channels'), 'path': {'mode': MODES.STREAMLIST, 'stream_type': 'live'}, 'context_menu': context_menu})
    kodi.create_item({'label': i18n('playlists'), 'path': {'mode': MODES.STREAMLIST, 'stream_type': 'playlist'}, 'context_menu': context_menu})
    kodi.create_item({'label': i18n('xbox_one'), 'path': {'mode': MODES.STREAMLIST, 'platform': 'xbox_one'}, 'context_menu': context_menu})
    kodi.create_item({'label': i18n('ps4'), 'path': {'mode': MODES.STREAMLIST, 'platform': 'ps4'}, 'context_menu': context_menu})
    kodi.create_item({'label': i18n('videos'), 'path': {'mode': MODES.CHANNELVIDEOS, 'channel_id': 'all'}})
    kodi.create_item({'label': i18n('clips'), 'path': {'mode': MODES.CLIPSLIST, 'trending': 'true'}})
    kodi.create_item({'label': i18n('communities'), 'path': {'mode': MODES.COMMUNITIES}})
    kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.GAMES}})
    kodi.end_of_directory()


@DISPATCHER.register(MODES.SEARCH)
@error_handler
def search():
    kodi.set_content('files')
    context_menu = list()
    context_menu.extend(menu_items.clear_previews())
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
        search_results(content=content, query=user_input)
    else:
        kodi.update_container(kodi.get_plugin_url({'mode': MODES.SEARCH}))


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
                channel = stream[Keys.CHANNEL]
                if not utils.is_blacklisted(channel[Keys.ID]):
                    kodi.create_item(converter.stream_to_listitem(stream))
            if results[Keys.TOTAL] > (offset + limit):
                kodi.create_item(utils.link_to_next_page({'mode': MODES.SEARCHRESULTS, 'content': content, 'query': query, 'index': index}))
            kodi.end_of_directory()
        else:
            kodi.update_container(kodi.get_plugin_url({'mode': MODES.SEARCH}))
    elif content == 'channels':
        kodi.set_content('files')
        index, offset, limit = utils.calculate_pagination_values(index)
        results = twitch.get_channel_search(query=query, offset=offset, limit=limit)
        if (results[Keys.TOTAL] > 0) and (Keys.CHANNELS in results):
            for channel in results[Keys.CHANNELS]:
                if not utils.is_blacklisted(channel[Keys.ID]):
                    kodi.create_item(converter.channel_to_listitem(channel))
            if results[Keys.TOTAL] > (offset + limit):
                kodi.create_item(utils.link_to_next_page({'mode': MODES.SEARCHRESULTS, 'content': content, 'query': query, 'index': index}))
            kodi.end_of_directory()
        else:
            kodi.update_container(kodi.get_plugin_url({'mode': MODES.SEARCH}))
    elif content == 'games':
        kodi.set_content('files')
        results = twitch.get_game_search(query=query)
        if (Keys.GAMES in results) and (results[Keys.GAMES]):
            for game in results[Keys.GAMES]:
                if not utils.is_blacklisted(game[Keys.ID], list_type='game'):
                    kodi.create_item(converter.game_to_listitem(game))
            kodi.end_of_directory()
        else:
            kodi.update_container(kodi.get_plugin_url({'mode': MODES.SEARCH}))
    elif content == 'id_url':
        kodi.set_content('videos')
        video_id = utils.extract_video_id(query)
        results = twitch.get_video_by_id(video_id)
        if video_id.startswith('a') or video_id.startswith('c') or video_id.startswith('v'):
            kodi.create_item(converter.video_list_to_listitem(results))
            kodi.end_of_directory()
        else:
            kodi.update_container(kodi.get_plugin_url({'mode': MODES.SEARCH}))


@DISPATCHER.register(MODES.FOLLOWING)
@error_handler
def following():
    kodi.set_content('files')
    context_menu = list()
    context_menu.extend(menu_items.clear_previews())
    kodi.create_item({'label': i18n('live_channels'), 'path': {'mode': MODES.FOLLOWED, 'content': 'live', 'context_menu': context_menu}})
    kodi.create_item({'label': i18n('playlists'), 'path': {'mode': MODES.FOLLOWED, 'content': 'playlist', 'context_menu': context_menu}})
    kodi.create_item({'label': i18n('channels'), 'path': {'mode': MODES.FOLLOWED, 'content': 'channels'}})
    kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.FOLLOWED, 'content': 'games'}})
    kodi.create_item({'label': i18n('clips'), 'path': {'mode': MODES.FOLLOWED, 'content': 'clips'}})
    kodi.end_of_directory()


@DISPATCHER.register(MODES.FEATUREDSTREAMS)
@error_handler
def list_featured_streams():
    utils.refresh_previews()
    kodi.set_content('videos')
    streams = twitch.get_featured_streams(offset=0, limit=100)
    if Keys.FEATURED in streams:
        for stream in streams[Keys.FEATURED]:
            channel = stream[Keys.STREAM][Keys.CHANNEL]
            if not utils.is_blacklisted(channel[Keys.ID]):
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
            game = element[Keys.GAME]
            if not utils.is_blacklisted(game[Keys.ID], list_type='game'):
                kodi.create_item(converter.game_to_listitem(element[Keys.GAME]))
        if games[Keys.TOTAL] > (offset + limit):
            kodi.create_item(utils.link_to_next_page({'mode': MODES.GAMES, 'index': index}))
        kodi.end_of_directory()


@DISPATCHER.register(MODES.COMMUNITIES, kwargs=['cursor'])
@error_handler
def list_all_communities(cursor='MA=='):
    kodi.set_content('files')
    limit = utils.get_items_per_page()
    communities = twitch.get_top_communities(cursor, limit)
    if (communities[Keys.TOTAL] > 0) and (Keys.COMMUNITIES in communities):
        for element in communities[Keys.COMMUNITIES]:
            kodi.create_item(converter.community_to_listitem(element))
        if communities[Keys.CURSOR]:
            kodi.create_item(utils.link_to_next_page({'mode': MODES.COMMUNITIES, 'cursor': communities[Keys.CURSOR]}))
        kodi.end_of_directory()


@DISPATCHER.register(MODES.STREAMLIST, kwargs=['stream_type', 'index', 'platform'])
@error_handler
def list_streams(stream_type='live', index=0, platform='all'):
    utils.refresh_previews()
    kodi.set_content('videos')
    index, offset, limit = utils.calculate_pagination_values(index)

    streams = twitch.get_all_streams(stream_type, platform, offset, limit)
    if (streams[Keys.TOTAL] > 0) and (Keys.STREAMS in streams):
        for stream in streams[Keys.STREAMS]:
            channel = stream[Keys.CHANNEL]
            if not utils.is_blacklisted(channel[Keys.ID]):
                kodi.create_item(converter.stream_to_listitem(stream))
        if streams[Keys.TOTAL] > (offset + limit):
            kodi.create_item(utils.link_to_next_page({'mode': MODES.STREAMLIST, 'stream_type': stream_type, 'platform': platform, 'index': index}))
        kodi.end_of_directory()


@DISPATCHER.register(MODES.FOLLOWED, args=['content'], kwargs=['index', 'cursor'])
@error_handler
def list_followed(content, index=0, cursor='MA=='):
    user = twitch.get_user()
    user_id = user.get(Keys.ID, None)
    username = user.get(Keys.NAME, None)
    if user_id:
        if content == 'live' or content == 'playlist':
            if content == 'live':
                utils.refresh_previews()
            kodi.set_content('videos')
            index, offset, limit = utils.calculate_pagination_values(index)
            streams = twitch.get_followed_streams(stream_type=content, offset=offset, limit=limit)
            if (streams[Keys.TOTAL] > 0) and (Keys.STREAMS in streams):
                for stream in streams[Keys.STREAMS]:
                    channel = stream[Keys.CHANNEL]
                    if not utils.is_blacklisted(channel[Keys.ID]):
                        kodi.create_item(converter.stream_to_listitem(stream))
                if streams[Keys.TOTAL] > (offset + limit):
                    kodi.create_item(utils.link_to_next_page({'mode': MODES.FOLLOWED, 'content': content, 'index': index}))
                kodi.end_of_directory()
        elif content == 'channels':
            kodi.set_content('files')
            index, offset, limit = utils.calculate_pagination_values(index)
            channels = twitch.get_followed_channels(user_id=user_id, offset=offset, limit=limit)
            if (channels[Keys.TOTAL] > 0) and (Keys.FOLLOWS in channels):
                for follow in channels[Keys.FOLLOWS]:
                    channel = follow[Keys.CHANNEL]
                    if not utils.is_blacklisted(channel[Keys.ID]):
                        kodi.create_item(converter.channel_to_listitem(channel))
                if channels[Keys.TOTAL] > (offset + limit):
                    kodi.create_item(utils.link_to_next_page({'mode': MODES.FOLLOWED, 'content': content, 'index': index}))
                kodi.end_of_directory()
        elif content == 'games':
            if username:
                kodi.set_content('files')
                games = twitch.get_followed_games(username)
                if Keys.FOLLOWS in games:
                    for game in games[Keys.FOLLOWS]:
                        if not utils.is_blacklisted(game[Keys.ID], list_type='game'):
                            kodi.create_item(converter.game_to_listitem(game))
                    kodi.end_of_directory()
        elif content == 'clips':
            kodi.set_content('videos')
            limit = utils.get_items_per_page()
            clips = twitch.get_followed_clips(cursor=cursor, limit=limit)
            if Keys.CLIPS in clips and len(clips[Keys.CLIPS]) > 0:
                for clip in clips[Keys.CLIPS]:
                    kodi.create_item(converter.clip_to_listitem(clip))
                if clips[Keys.CURSOR]:
                    kodi.create_item(utils.link_to_next_page({'mode': MODES.FOLLOWED, 'content': content, 'cursor': clips[Keys.CURSOR]}))
                kodi.end_of_directory()


@DISPATCHER.register(MODES.CHANNELVIDEOS, args=['channel_id'], kwargs=['channel_name'])
@error_handler
def list_channel_video_types(channel_id, channel_name=None):
    kodi.set_content('files')
    kodi.create_item({'label': i18n('past_broadcasts'), 'path': {'mode': MODES.CHANNELVIDEOLIST, 'channel_id': channel_id, 'broadcast_type': 'archive'}})
    kodi.create_item({'label': i18n('uploads'), 'path': {'mode': MODES.CHANNELVIDEOLIST, 'channel_id': channel_id, 'broadcast_type': 'upload'}})
    kodi.create_item({'label': i18n('video_highlights'), 'path': {'mode': MODES.CHANNELVIDEOLIST, 'channel_id': channel_id, 'broadcast_type': 'highlight'}})
    if channel_id != 'all':
        if channel_name:
            kodi.create_item({'label': i18n('clips'), 'path': {'mode': MODES.CLIPSLIST, 'trending': 'true', 'channel_name': channel_name}})
        kodi.create_item({'label': i18n('collections'), 'path': {'mode': MODES.COLLECTIONS, 'channel_id': channel_id}})
    kodi.end_of_directory()


@DISPATCHER.register(MODES.COLLECTIONS, args=['channel_id'], kwargs=['cursor'])
@error_handler
def list_collections(channel_id, cursor='MA=='):
    kodi.set_content('files')
    limit = utils.get_items_per_page()
    collections = twitch.get_collections(channel_id, cursor, limit)

    if (Keys.COLLECTIONS in collections) and (len(collections[Keys.COLLECTIONS]) > 0):
        has_collections = False
        for collection in collections[Keys.COLLECTIONS]:
            if collection[Keys.ITEMS_COUNT] > 0:
                has_collections = True
        if has_collections:
            for collection in collections[Keys.COLLECTIONS]:
                if collection[Keys.ITEMS_COUNT] > 0:
                    kodi.create_item(converter.collection_to_listitem(collection))
            if collections[Keys.CURSOR]:
                kodi.create_item(utils.link_to_next_page({'mode': MODES.COLLECTIONS, 'channel_id': channel_id, 'cursor': collections[Keys.CURSOR]}))
            kodi.end_of_directory()


@DISPATCHER.register(MODES.COLLECTIONVIDEOLIST, args=['collection_id'])
@error_handler
def list_collection_videos(collection_id):
    kodi.set_content('videos')
    videos = twitch.get_collection_videos(collection_id)
    if (Keys.ITEMS in videos) and (len(videos[Keys.ITEMS]) > 0):
        for video in videos[Keys.ITEMS]:
            kodi.create_item(converter.collection_video_to_listitem(video))
        kodi.end_of_directory()


@DISPATCHER.register(MODES.CLIPSLIST, kwargs=['cursor', 'channel_name'])
@error_handler
def list_clips(cursor='MA==', channel_name=None):
    kodi.set_content('videos')
    limit = utils.get_items_per_page()
    clips = twitch.get_top_clips(cursor, limit, channel=channel_name)

    if Keys.CLIPS in clips and len(clips[Keys.CLIPS]) > 0:
        for clip in clips[Keys.CLIPS]:
            kodi.create_item(converter.clip_to_listitem(clip))
        if clips[Keys.CURSOR]:
            item_dict = {'mode': MODES.CLIPSLIST, 'cursor': clips[Keys.CURSOR]}
            if channel_name:
                item_dict['channel_name'] = channel_name
            kodi.create_item(utils.link_to_next_page(item_dict))
        kodi.end_of_directory()


@DISPATCHER.register(MODES.CHANNELVIDEOLIST, args=['channel_id', 'broadcast_type'], kwargs=['index'])
@error_handler
def list_channel_videos(channel_id, broadcast_type, index=0):
    kodi.set_content('videos')
    index, offset, limit = utils.calculate_pagination_values(index)
    if channel_id == 'all':
        videos = twitch.get_top_videos(offset, limit, broadcast_type)
    else:
        videos = twitch.get_channel_videos(channel_id, offset, limit, broadcast_type)
    if Keys.VODS in videos or ((videos[Keys.TOTAL] > 0) and (Keys.VIDEOS in videos)):
        key = Keys.VODS if Keys.VODS in videos else Keys.VIDEOS
        for video in videos[key]:
            kodi.create_item(converter.video_list_to_listitem(video))
        if Keys.VODS in videos or videos[Keys.TOTAL] > (offset + limit):
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
            channel = stream[Keys.CHANNEL]
            if not utils.is_blacklisted(channel[Keys.ID]):
                kodi.create_item(converter.stream_to_listitem(stream))
        if streams[Keys.TOTAL] > (offset + limit):
            kodi.create_item(utils.link_to_next_page({'mode': MODES.COMMUNITYSTREAMS, 'community_id': community_id, 'index': index}))
        kodi.end_of_directory()


@DISPATCHER.register(MODES.PLAY, kwargs=['name', 'channel_id', 'video_id', 'slug', 'source', 'use_player'])
@error_handler
def play(name=None, channel_id=None, video_id=None, slug=None, source=True, use_player=False):
    videos = item_dict = quality = None
    if video_id:
        result = twitch.get_video_by_id(video_id)
        video_id = result[Keys.ID]
        videos = twitch.get_vod(video_id)
        item_dict = converter.video_to_playitem(result)
        channel_id = result[Keys.CHANNEL][Keys.ID]
        quality = utils.get_default_quality(channel_id)
        if quality:
            quality = quality[channel_id]['quality']
    elif name and channel_id:
        quality = utils.get_default_quality(channel_id)
        if quality:
            quality = quality[channel_id]['quality']
        videos = twitch.get_live(name)
        result = twitch.get_channel_stream(channel_id)[Keys.STREAM]
        item_dict = converter.stream_to_playitem(result)
    elif slug:
        videos = twitch.get_clip(slug)
        result = twitch.get_clip_by_slug(slug)
        item_dict = converter.clip_to_playitem(result)
    if item_dict and videos:
        if source:
            use_source = kodi.get_setting('video_quality') == '0'
        else:
            use_source = False

        play_url = converter.get_video_for_quality(videos, source=use_source, quality=quality)

        if play_url:
            item_dict['path'] = play_url
            playback_item = kodi.create_item(item_dict, add=False)
            if use_player:
                kodi.Player().play(item_dict['path'], playback_item)
            else:
                kodi.set_resolved_url(playback_item)
            if utils.irc_enabled() and twitch.access_token:
                user = twitch.get_user()
                username = user.get(Keys.NAME, None)
                if username:
                    utils.exec_irc_script(username, name)


@DISPATCHER.register(MODES.EDITFOLLOW, kwargs=['channel_id', 'channel_name', 'game_name'])
@error_handler
def edit_user_follows(channel_id=None, channel_name=None, game_name=None):
    if (channel_id is None or channel_name is None) and game_name is None:
        return
    try:
        if not game_name:
            result = twitch.check_follow(channel_id)
        else:
            result = twitch.check_follow_game(game_name)
        is_following = True
    except TwitchException as error:
        if '404' not in error.message: raise
        is_following = False

    if not game_name:
        display_name = channel_name
    else:
        display_name = game_name

    if is_following:
        confirmed = kodi.Dialog().yesno(i18n('toggle_follow'), i18n('unfollow_confirm') % display_name)
        if confirmed:
            if not game_name:
                result = twitch.unfollow(channel_id)
            else:
                result = twitch.unfollow_game(game_name)
            kodi.notify(msg=i18n('unfollowed') % display_name, sound=False)
    else:
        confirmed = kodi.Dialog().yesno(i18n('toggle_follow'), i18n('follow_confirm') % display_name)
        if confirmed:
            if not game_name:
                result = twitch.follow(channel_id)
            else:
                result = twitch.follow_game(game_name)
            kodi.notify(msg=i18n('now_following') % display_name, sound=False)


@DISPATCHER.register(MODES.EDITBLOCK, args=['target_id', 'name'])
@error_handler
def edit_user_blocks(target_id, name):
    try:
        block_list = twitch.get_user_blocks()
    except TwitchException as error:
        if 'no results' not in error.message.lower(): raise
        block_list = []

    is_blocked = any(target_id == blocked_id for blocked_id, blocked_name in block_list)

    if is_blocked:
        confirmed = kodi.Dialog().yesno(i18n('toggle_block'), i18n('unblock_confirm') % name)
        if confirmed:
            result = twitch.unblock_user(target_id)
            kodi.notify(msg=i18n('unblocked') % name, sound=False)
    else:
        confirmed = kodi.Dialog().yesno(i18n('toggle_block'), i18n('block_confirm') % name)
        if confirmed:
            result = twitch.block_user(target_id)
            kodi.notify(msg=i18n('blocked') % name, sound=False)


@DISPATCHER.register(MODES.EDITBLACKLIST, kwargs=['list_type', 'target_id', 'name', 'remove'])
@error_handler
def edit_blacklist(list_type='user', target_id=None, name=None, remove=False):
    if not remove:
        if not target_id or not name: return
        result = utils.add_blacklist(target_id, name, list_type)
        if result:
            kodi.notify(msg=i18n('blacklisted') % name, sound=False)
    else:
        result = utils.remove_blacklist(list_type)
        if result:
            kodi.notify(msg=i18n('removed_from_blacklist') % result[1], sound=False)


@DISPATCHER.register(MODES.EDITQUALITIES, kwargs=['video_id', 'target_id', 'name', 'remove'])
@error_handler
def edit_qualities(target_id=None, name=None, video_id=None, remove=False):
    if not remove:
        if not target_id or not name: return
        if video_id:
            videos = twitch.get_vod(video_id)
        else:
            videos = twitch.get_live(name)
        quality, url = converter.select_video_for_quality(videos, return_label=True)
        result = utils.add_default_quality(target_id, name, quality)
        if result:
            kodi.notify(msg=i18n('default_quality_set') % (quality, name), sound=False)
    else:
        result = utils.remove_default_quality()
        if result:
            kodi.notify(msg=i18n('removed_default_quality') % result[result.keys()[0]]['name'], sound=False)


@DISPATCHER.register(MODES.CLEARLIST, args=['list_type', 'list_name'])
@error_handler
def clear_list(list_type, list_name):
    confirmed = kodi.Dialog().yesno(i18n('clear_list'), i18n('confirm_clear') % (list_type, list_name))
    if confirmed:
        result = utils.clear_list(list_type, list_name)
        if result:
            kodi.notify(msg=i18n('cleared_list') % (list_type, list_name), sound=False)


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
    redirect_uri = utils.get_redirect_uri()
    request_url = twitch.client.prepare_request_uri(redirect_uri=redirect_uri, scope=twitch.required_scopes)
    try:
        short_url = googl_url(request_url)
    except:
        short_url = None
    prompt_url = short_url if short_url else request_url
    result = kodi.Dialog().ok(heading=i18n('authorize_heading'), line1=i18n('authorize_message'),
                              line2=' %s' % prompt_url)
    kodi.show_settings()
