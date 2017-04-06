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

import xbmc
from common import kodi, log_utils

ID = kodi.get_id()


class TwitchPlayer(xbmc.Player):
    window = kodi.Window(10000)
    player_keys = {
        'twitch_playing': ID + '-twitch_playing'
    }
    seek_keys = {
        'seek_time': ID + '-seek_time',
    }

    def __init__(self, *args, **kwargs):
        log_utils.log('Player: Start', log_utils.LOGDEBUG)
        self.reset()

    def reset(self):
        self.reset_player()
        self.reset_seek()

    def reset_seek(self):
        for k in self.seek_keys.keys():
            self.window.clearProperty(key=self.seek_keys[k])

    def reset_player(self):
        for k in self.player_keys.keys():
            self.window.clearProperty(key=self.player_keys[k])

    def onPlayBackStarted(self):
        is_playing = self.window.getProperty(key=self.player_keys['twitch_playing']) == 'True'
        seek_time = self.window.getProperty(key=self.seek_keys['seek_time'])
        log_utils.log('Player: |onPlayBackStarted| isTwitch |{0}| SeekTime |{1}|'.format(is_playing, seek_time), log_utils.LOGDEBUG)
        if not is_playing:
            self.reset_seek()
        else:
            if seek_time:
                seek_time = float(seek_time)
                self.seekTime(seek_time)

    def onPlayBackStopped(self):
        log_utils.log('Player: |onPlayBackStopped|', log_utils.LOGDEBUG)
        self.reset()

    def onPlayBackEnded(self):
        log_utils.log('Player: |onPlayBackEnded|', log_utils.LOGDEBUG)
        self.reset()
