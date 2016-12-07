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

from twitch import queries as twitch_queries
from twitch.api import v3 as twitch
from constants import Keys
import utils


class Twitch:
    api = twitch
    queries = twitch_queries
    oauth = utils.get_client_id_secret()

    def __init__(self):
        self.queries.CLIENT_ID = self.oauth['client_id']

    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_featured_streams(self):
        return self.api.streams.featured()

    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_top_games(self, offset, limit):
        return self.api.games.top(offset=offset, limit=limit)

    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_all_channels(self, offset, limit):
        return self.api.streams.all(offset=offset, limit=limit)

    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_followed_channels(self, name, offset, limit):
        return self.api.follows.by_user(name=name, limit=limit, offset=offset)

    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_channel_videos(self, name, offset, limit, broadcast_type):
        return self.api.videos.by_channel(name=name, limit=limit, offset=offset, broadcast_type=broadcast_type)

    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_game_streams(self, game, offset, limit):
        return self.api.streams.all(game=game, limit=limit, offset=offset)

    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_streams_by_channels(self, names, offset, limit):
        query = self.queries.ApiQuery('streams')
        query.add_param('offset', offset)
        query.add_param('limit', limit)
        query.add_param('channel', names)
        return query.execute()

    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_followed_games(self, name):
        query = self.queries.HiddenApiQuery('users/{0}/follows/games'.format(name))
        return query.execute()

    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_following_streams(self, username):
        following_channels = self._get_followed_channels(username)
        channels = sorted(following_channels, key=lambda k: k[Keys.DISPLAY_NAME])
        channel_names = ','.join([channel[Keys.NAME] for channel in channels])
        live = []
        limit = 100
        offset = 0

        while True:
            temp = self.get_streams_by_channels(channel_names, offset, limit)
            if len(temp) == 0:
                break
            for stream in temp[Keys.STREAMS]:
                live.append(stream)
            offset += limit
            if temp[Keys.TOTAL] <= offset:
                break

        channels = {Keys.LIVE: live, Keys.OTHERS: channels}
        return channels

    def _get_followed_channels(self, username):
        acc = []
        limit = 100
        offset = 0
        while True:
            temp = self.get_followed_channels(username, offset, limit)
            if len(temp) == 0:
                break
            for channel in temp[Keys.FOLLOWS]:
                acc.append(channel[Keys.CHANNEL])
            offset += limit
            if temp[Keys.TOTAL] <= offset:
                break

        return acc
