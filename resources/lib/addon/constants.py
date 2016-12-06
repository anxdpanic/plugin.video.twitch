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

from common import kodi
from common.url_dispatcher import URL_Dispatcher


def __enum(**enums):
    return type('Enum', (), enums)


DISPATCHER = URL_Dispatcher()

ADDON_DATA_DIR = kodi.translate_path('special://profile/addon_data/{0!s}/'.format(kodi.get_id()))

MODES = __enum(
    MAIN='main',
    FEATUREDSTREAMS='featured_streams',
    GAMES='games',
    CHANNELS='channels',
    FOLLOWING='following',
    SEARCH='search',
    SETTINGS='settings',
    FOLLOWEDCHANNELS='followed_channels',
    FOLLOWEDLIVE='followed_live',
    FOLLOWEDGAMES='followed_games'
)

ICONS = __enum(
    ADDON=kodi.translate_path('special://home/addons/{0!s}/icon.png'.format(kodi.get_id())),
    KODI=kodi.translate_path('special://xbmc/media/icon256x256.png'),
)
