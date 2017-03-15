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
from constants import MODES

i18n = utils.i18n


def run_plugin(label, queries):
    return [(label, 'RunPlugin(%s)' % kodi.get_plugin_url(queries))]


def update_container(label, queries):
    return [(label, 'Container.Update(%s)' % kodi.get_plugin_url(queries))]


def clear_previews():
    if kodi.get_setting('live_previews_enable') == 'true':
        return run_plugin(i18n('clear_live_preview'), {'mode': MODES.CLEARLIVEPREVIEWS, 'notify': utils.notify_refresh()})
    return []


def channel_videos(channel_id, display_name):
    return update_container(i18n('go_to') % '[COLOR white][B]%s[/B][/COLOR]' % display_name, {'mode': MODES.CHANNELVIDEOS, 'channel_id': channel_id})


def go_to_game(game):
    return update_container(i18n('go_to') % '[COLOR white][B]%s[/B][/COLOR]' % game, {'mode': MODES.GAMESTREAMS, 'game': game})


def refresh():
    return [(i18n('refresh'), 'Container.Refresh')]


def editfollow(channel_id, display_name):
    return update_container(i18n('follow_unfollow') % '[COLOR white][B]%s[/B][/COLOR]' % display_name, {'mode': MODES.EDITFOLLOW, 'channel_id': channel_id,
                                                                                                        'channel_name': display_name})
