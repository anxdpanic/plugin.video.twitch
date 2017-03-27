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
from error_handling import api_error_handler
from constants import Keys, SCOPES
from twitch import queries as twitch_queries
from twitch import oauth
from twitch.api import v5 as twitch
from twitch.api import usher
from base64 import b64encode

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

    @api_error_handler
    @utils.cache.cache_function(cache_limit=1)
    def get_user(self):
        return self.api.users.user()

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_featured_streams(self):
        return self.api.streams.featured()

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_top_games(self, offset, limit):
        return self.api.games.top(offset=offset, limit=limit)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_top_communities(self, index, limit):
        return self.api.communities.top(cursor=b64encode(str(index)), limit=limit)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_all_channels(self, offset, limit):
        return self.api.streams.all(offset=offset, limit=limit)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_all_teams(self, offset, limit):
        return self.api.teams.active(offset=offset, limit=limit)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_followed_channels(self, user_id, offset, limit):
        return self.api.users.follows(user_id=user_id, limit=limit, offset=offset)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_channel_videos(self, channel_id, offset, limit, broadcast_type):
        return self.api.channels.videos(channel_id=channel_id, limit=limit, offset=offset, broadcast_type=broadcast_type)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_game_streams(self, game, offset, limit):
        return self.api.streams.all(game=game, limit=limit, offset=offset)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_community_streams(self, community_id, offset, limit):
        return self.api.streams.all(community_id=community_id, limit=limit, offset=offset)

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
    def follow_status(self, channel_id):
        user = self.get_user()
        user_id = user.get(Keys.ID)
        return self.api.users.follow_status(user_id=user_id, target_id=channel_id)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def follow(self, channel_id):
        user = self.get_user()
        user_id = user.get(Keys.ID)
        return self.api.users.follow(user_id=user_id, target_id=channel_id)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def unfollow(self, channel_id):
        user = self.get_user()
        user_id = user.get(Keys.ID)
        return self.api.users.unfollow(user_id=user_id, target_id=channel_id)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def blocks(self, offset, limit):
        user = self.get_user()
        user_id = user.get(Keys.ID)
        return self.api.users.blocks(user_id=user_id, limit=limit, offset=offset)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def block_user(self, target_id):
        user = self.get_user()
        user_id = user.get(Keys.ID)
        return self.api.users.add_block(user_id=user_id, target_id=target_id)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def unblock_user(self, target_id):
        user = self.get_user()
        user_id = user.get(Keys.ID)
        return self.api.users.del_block(user_id=user_id, target_id=target_id)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_video_by_id(self, video_id):
        return self.api.videos.by_id(video_id=video_id)

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
        query = self.queries.HiddenApiQuery('users/{0}/follows/games'.format(name))
        return query.execute()

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_followed_streams(self, stream_type, offset, limit):
        return self.api.streams.followed(stream_type=stream_type, limit=limit, offset=offset)

    @api_error_handler
    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_vod(self, video_id):
        return self.usher.video(video_id)

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
                user_blocks.append((user[Keys.USER][Keys.ID], user[Keys.USER][Keys.DISPLAY_NAME]))
            offset += limit
            if temp[Keys.TOTAL] <= offset:
                break

        return user_blocks
