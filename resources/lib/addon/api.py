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

import utils
from common import kodi
from error_handling import api_error_handler
from constants import Keys, SCOPES
from twitch import queries as twitch_queries
from twitch import oauth
from twitch.api import usher
from twitch.api import v5 as twitch

i18n = utils.i18n


class Twitch:
    api = twitch
    usher = usher
    queries = twitch_queries
    client_id = utils.get_client_id()
    access_token = utils.get_oauth_token(token_only=True, required=False)
    required_scopes = SCOPES

    def __init__(self):
        self.queries.CLIENT_ID = self.client_id
        self.queries.OAUTH_TOKEN = self.access_token
        self.client = oauth.MobileClient(self.client_id)
        if self.access_token:
            token_check = self.root()
            if not token_check['token']['valid']:
                self.queries.OAUTH_TOKEN = ''
                self.access_token = ''
                result = kodi.Dialog().ok(heading=i18n('oauth_token'), line1=i18n('invalid_token'),
                                          line2=i18n('get_new_oauth_token') % (i18n('settings'), i18n('login'), i18n('get_oauth_token')))
            else:
                if token_check['token']['client_id'] == self.client_id:
                    if token_check['token']['authorization']:
                        scopes = token_check['token']['authorization']['scopes']
                        missing_scopes = [value for value in self.required_scopes if value not in scopes]
                        if len(missing_scopes) > 0:
                            self.queries.OAUTH_TOKEN = ''
                            self.access_token = ''
                            result = kodi.Dialog().ok(heading=i18n('oauth_token'), line1=i18n('missing_scopes') % missing_scopes,
                                                      line2=i18n('get_new_oauth_token') % (i18n('settings'), i18n('login'), i18n('get_oauth_token')))
                else:
                    self.queries.OAUTH_TOKEN = ''
                    self.access_token = ''
                    result = kodi.Dialog().ok(heading=i18n('oauth_token'), line1=i18n('client_id_mismatch'),
                                              line2=i18n('get_new_oauth_token') % (i18n('settings'), i18n('login'), i18n('get_oauth_token')))

    @api_error_handler
    @utils.cache.cache_function(cache_limit=1)
    def root(self):
        return self.api.root()

    @api_error_handler
    @utils.cache.cache_function(cache_limit=1)
    def get_user(self):
        return self.api.users.user()

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_featured_streams(self, offset, limit):
        return self.api.streams.get_featured(offset=offset, limit=limit)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_top_games(self, offset, limit):
        return self.api.games.get_top(offset=offset, limit=limit)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_top_communities(self, cursor, limit):
        return self.api.communities.get_top(cursor=cursor, limit=limit)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_collections(self, channel_id, cursor, limit):
        return self.api.collections.get_collections(channel_id=channel_id, cursor=cursor, limit=limit)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_all_streams(self, stream_type, platform, offset, limit):
        return self.api.streams.get_all(stream_type=stream_type, platform=platform, offset=offset, limit=limit)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_all_teams(self, offset, limit):
        return self.api.teams.get_active(offset=offset, limit=limit)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_followed_channels(self, user_id, offset, limit):
        return self.api.users.get_follows(user_id=user_id, limit=limit, offset=offset)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_top_videos(self, offset, limit, broadcast_type, period='week'):
        return self.api.videos.get_top(limit=limit, offset=offset, broadcast_type=broadcast_type, period=period)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_followed_clips(self, cursor, limit, trending='true'):
        return self.api.clips.get_followed(limit=limit, cursor=cursor, trending=trending)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_top_clips(self, cursor, limit, channel=None, game=None, period='week', trending='true'):
        return self.api.clips.get_top(limit=limit, cursor=cursor, channels=channel, games=game, period=period, trending=trending)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_channel_videos(self, channel_id, offset, limit, broadcast_type):
        return self.api.channels.get_videos(channel_id=channel_id, limit=limit, offset=offset, broadcast_type=broadcast_type)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_collection_videos(self, collection_id):
        return self.api.collections.by_id(collection_id=collection_id, include_all='false')

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_game_streams(self, game, offset, limit):
        return self.api.streams.get_all(game=game, limit=limit, offset=offset)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_community_streams(self, community_id, offset, limit):
        return self.api.streams.get_all(community_id=community_id, limit=limit, offset=offset)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_channel_search(self, query, offset, limit):
        return self.api.search.channels(query=query, limit=limit, offset=offset)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_stream_search(self, query, offset, limit):
        return self.api.search.streams(query=query, limit=limit, offset=offset)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_game_search(self, query):
        return self.api.search.games(query=query)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def check_follow(self, channel_id):
        user = self.get_user()
        user_id = user.get(Keys._ID)
        return self.api.users.check_follows(user_id=user_id, channel_id=channel_id)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def follow(self, channel_id):
        user = self.get_user()
        user_id = user.get(Keys._ID)
        return self.api.users.follow_channel(user_id=user_id, channel_id=channel_id)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def unfollow(self, channel_id):
        user = self.get_user()
        user_id = user.get(Keys._ID)
        return self.api.users.unfollow_channel(user_id=user_id, channel_id=channel_id)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def check_follow_game(self, game_name):
        user = self.get_user()
        username = user.get(Keys.NAME)
        return self.api.games.check_follows(username=username, name=game_name)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def follow_game(self, game_name):
        user = self.get_user()
        username = user.get(Keys.NAME)
        return self.api.games.follow(username=username, name=game_name)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def unfollow_game(self, game_name):
        user = self.get_user()
        username = user.get(Keys.NAME)
        return self.api.games.unfollow(username=username, name=game_name)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def blocks(self, offset, limit):
        user = self.get_user()
        user_id = user.get(Keys._ID)
        return self.api.users.get_blocks(user_id=user_id, limit=limit, offset=offset)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def block_user(self, target_id):
        user = self.get_user()
        user_id = user.get(Keys._ID)
        return self.api.users.block_user(user_id=user_id, target_id=target_id)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def unblock_user(self, target_id):
        user = self.get_user()
        user_id = user.get(Keys._ID)
        return self.api.users.unblock_user(user_id=user_id, target_id=target_id)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_video_by_id(self, video_id):
        return self.api.videos.by_id(video_id=video_id)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_clip_by_slug(self, slug):
        return self.api.clips.by_slug(slug=slug)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_channel_stream(self, channel_id):
        return self.api.streams.by_id(channel_id=channel_id, stream_type='all')

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_streams_by_channels(self, names, offset, limit):
        query = self.queries.ApiQuery('streams')
        query.add_param('offset', offset)
        query.add_param('limit', limit)
        query.add_param('channel', names)
        return query.execute()

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_followed_games(self, name):
        return self.api.games.get_followed(username=name)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_followed_streams(self, stream_type, offset, limit):
        return self.api.streams.get_followed(stream_type=stream_type, limit=limit, offset=offset)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_vod(self, video_id):
        return self.usher.video(video_id)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_clip(self, slug):
        return self.usher.clip(slug)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_live(self, name):
        return self.usher.live(name)

    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_user_blocks(self):
        limit = 100
        offset = 0

        user_blocks = []
        while True:
            temp = self.blocks(offset, limit)
            if len(temp[Keys.BLOCKS]) == 0:
                break
            for user in temp[Keys.BLOCKS]:
                user_blocks.append((user[Keys.USER][Keys._ID], user[Keys.USER][Keys.DISPLAY_NAME]))
            offset += limit
            if temp[Keys.TOTAL] <= offset:
                break

        return user_blocks
