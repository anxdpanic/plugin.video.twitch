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
from constants import Keys
from twitch import queries as twitch_queries
from twitch.api import v3 as twitch
from twitch.api import usher


class Twitch:
    api = twitch
    usher = usher
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
    def get_all_teams(self, offset, limit):
        return self.api.teams.active(offset=offset, limit=limit)

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
    def get_channel_search(self, query, offset, limit):
        return self.api.search.channels(query=query, limit=limit, offset=offset)

    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_stream_search(self, query, offset, limit):
        return self.api.search.streams(query=query, limit=limit, offset=offset)

    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_game_search(self, query):
        return self.api.search.games(query=query)

    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_video_by_id(self, video_id):
        return self.api.videos.by_id(identification=video_id)

    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_channel_stream(self, name):
        return self.api.streams.all(channel=name)

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
    def get_vod(self, video_id):
        return self.usher._vod(video_id)

    @utils.cache.cache_function(cache_limit=utils.cache_limit)
    def get_live(self, name):
        return self.usher.live(name)

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

    @staticmethod
    def get_video_for_quality(videos, quality_index):
        quality_list_stream = ['Source', '1080p60', '1080p30', '720p60', '720p30', '540p30', '480p30', '360p30', '240p30', '144p30']
        old_quality_list_stream = ['Source', 'High', 'Medium', 'Low', 'Mobile']
        new_videos = dict()

        def _coerce_quality(q):
            if q == 'live':
                return 'Source'
            elif q not in quality_list:  # non-standard quality naming, attempt to coerce
                if q.endswith('p'):  # '1080p'
                    return q + '30'  # '1080p30' is in qualityList
                else:
                    q = q.split(None, 1)  # '1080p60 - source' -> ['1080p60', ' - source']
                    if q:
                        return q[0]  # '1080p60' is in qualityList
            return q

        def _get_old_quality(q_idx):
            if q_idx <= 2:
                return 0
            elif q_idx <= 4:
                return 1
            elif q_idx <= 6:
                return 2
            elif q_idx <= 7:
                return 3
            else:
                return 4

        quality_list = quality_list_stream
        if '360p' not in videos and '360p30' not in videos:
            quality_index = _get_old_quality(quality_index)
            quality_list = old_quality_list_stream

        for video_quality, url in videos.items():
            video_quality = _coerce_quality(video_quality)
            if video_quality in quality_list:  # check for quality in list before using it
                quality_int = quality_list.index(video_quality)
                new_videos[quality_int] = url

        best_distance = len(quality_list) + 1

        if (quality_index in new_videos) and (best_distance == len(quality_list) + 1):
            # selected quality is available
            return new_videos[quality_index]
        else:
            # not available, calculate differences to available qualities
            # return lowest difference / lower quality if same distance
            best_distance = len(quality_list) + 1

            best_match = None
            qualities = sorted(new_videos, reverse=True)
            for quality in qualities:
                new_distance = abs(quality_index - quality)
                if new_distance < best_distance:
                    best_distance = new_distance
                    best_match = quality

            return new_videos[best_match]

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
