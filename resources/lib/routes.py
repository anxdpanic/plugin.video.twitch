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
from addon.common import kodi, cache
from addon import utils
from addon.converter import JsonListItemConverter
from twitch import queries as twitch_queries
from twitch.api import v3 as twitch

i18n = utils.i18n

converter = JsonListItemConverter(LINE_LENGTH)

__oauth = utils.get_client_id_secret()
twitch_queries.CLIENT_ID = __oauth['client_id']

cache_limit = int(kodi.get_setting('cache_expire_time')) / 60
cache.cache_enabled = cache_limit > 0


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
    kodi.create_item({'label': i18n('live_channels'), 'path': {'mode': MODES.FOLLOWEDLIVE}})
    kodi.create_item({'label': i18n('channels'), 'path': {'mode': MODES.FOLLOWEDCHANNELS}})
    kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.FOLLOWEDGAMES}})
    kodi.end_of_directory()


@DISPATCHER.register(MODES.FEATUREDSTREAMS)
def list_featured_streams():
    kodi.set_content('videos')

    @cache.cache_function(cache_limit=cache_limit)  # cache api response
    def get_featured():
        return twitch.streams.featured()

    streams = get_featured()
    for stream in streams[Keys.FEATURED]:
        kodi.create_item(converter.stream_to_listitem(stream[Keys.STREAM]))
    kodi.end_of_directory()


@DISPATCHER.register(MODES.GAMES, kwargs=['index'])
def list_games(index=0):
    kodi.set_content('files')
    index, offset, limit = utils.calculate_pagination_values(index)

    @cache.cache_function(cache_limit=cache_limit)  # cache api response
    def get_games(offset, limit):
        return twitch.games.top(offset=offset, limit=limit)

    games = get_games(offset, limit)
    for element in games[Keys.TOP]:
        kodi.create_item(converter.game_to_listitem(element[Keys.GAME]))
    kodi.create_item(utils.link_to_next_page({'mode': MODES.GAMES, 'index': index}))
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
        result = cache.reset_cache()
        if result:
            kodi.notify(msg=i18n('cache_reset_succeeded'), sound=False)
        else:
            kodi.notify(msg=i18n('cache_reset_failed'), sound=False)
