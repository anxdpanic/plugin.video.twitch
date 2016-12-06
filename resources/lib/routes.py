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

from addon.strings import STRINGS
from addon.constants import DISPATCHER, MODES
from addon.common import kodi

translations = kodi.Translations(STRINGS)
i18n = translations.i18n


@DISPATCHER.register(MODES.MAIN)
def main():
    kodi.create_item({'label': i18n('featured_streams'), 'path': {'mode': MODES.FEATUREDSTREAMS}})
    kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.GAMES}})
    kodi.create_item({'label': i18n('channels'), 'path': {'mode': MODES.CHANNELS}})
    kodi.create_item({'label': i18n('following'), 'path': {'mode': MODES.FOLLOWING}})
    kodi.create_item({'label': i18n('search'), 'path': {'mode': MODES.SEARCH}})
    kodi.create_item({'label': i18n('settings'), 'path': {'mode': MODES.SETTINGS}})
    kodi.end_of_directory()


@DISPATCHER.register(MODES.FOLLOWING)
def following():
    kodi.create_item({'label': i18n('live_channels'), 'path': {'mode': MODES.FOLLOWEDLIVE}})
    kodi.create_item({'label': i18n('channels'), 'path': {'mode': MODES.FOLLOWEDCHANNELS}})
    kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.FOLLOWEDGAMES}})
    kodi.end_of_directory()
