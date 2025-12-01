# -*- coding: utf-8 -*-
"""
    Copyright (C) 2012-2024 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

import datetime
import json
import sqlite3

import xbmcvfs

from .common import kodi


class WatchHistory:
    """Stores recently watched streams and VODs"""
    
    def __init__(self, max_items=50):
        path = 'special://profile/addon_data/plugin.video.twitch/history/'
        filename = ''.join([path, 'watch_history.sqlite'])

        self.path = kodi.translate_path(path)
        self.filename = kodi.translate_path(filename)

        self.database = None
        self.cursor = None

        self._max_items = max_items
        self._table_name = 'watch_history_01'

        self.create_table()

    def open(self):
        if not xbmcvfs.exists(self.path):
            xbmcvfs.mkdirs(self.path)

        self.database = sqlite3.connect(self.filename, check_same_thread=False, 
                                         detect_types=sqlite3.PARSE_DECLTYPES, timeout=1)
        self.database.isolation_level = None

        self.cursor = self.database.cursor()
        self.cursor.execute('PRAGMA journal_mode=MEMORY')
        self.cursor.execute('PRAGMA busy_timeout=20000')

        self.cursor.execute('BEGIN')

    def close(self):
        self.cursor.execute('COMMIT')
        self.cursor.execute('VACUUM')

        self.database.commit()

        self.cursor.close()
        self.cursor = None

        self.database.close()
        self.database = None

    def create_table(self):
        # Store: content_type (stream/video/clip), content_id, channel_id, channel_name, 
        #        title, thumbnail, game_name, timestamp
        query = '''CREATE TABLE IF NOT EXISTS %s (
            content_type TEXT,
            content_id TEXT,
            channel_id TEXT,
            channel_name TEXT,
            title TEXT,
            thumbnail TEXT,
            game_name TEXT,
            duration TEXT,
            time TIMESTAMP,
            PRIMARY KEY (content_type, content_id)
        )''' % self._table_name

        self.open()
        self.execute(query)
        self.close()

    def execute(self, query, values=[]):
        ret_val = self.cursor.execute(query, values)
        return ret_val

    def list(self, content_type=None, limit=None):
        """Get list of recently watched items
        
        Args:
            content_type: 'stream', 'video', 'clip' or None for all
            limit: Maximum number of items to return
            
        Returns:
            List of dicts with watch history data
        """
        results = []
        
        if content_type:
            query = 'SELECT content_type, content_id, channel_id, channel_name, title, thumbnail, game_name, duration, time FROM %s WHERE content_type = ? ORDER BY time DESC' % self._table_name
            values = [content_type]
        else:
            query = 'SELECT content_type, content_id, channel_id, channel_name, title, thumbnail, game_name, duration, time FROM %s ORDER BY time DESC' % self._table_name
            values = []
        
        if limit:
            query += ' LIMIT ?'
            values.append(limit)

        self.open()
        ret_vals = self.execute(query, values)
        if ret_vals:
            for item in ret_vals:
                results.append({
                    'content_type': item[0],
                    'content_id': item[1],
                    'channel_id': item[2],
                    'channel_name': item[3],
                    'title': item[4],
                    'thumbnail': item[5],
                    'game_name': item[6],
                    'duration': item[7],
                    'time': item[8]
                })
        self.close()
        return results

    def clear(self):
        """Clear all watch history"""
        query = 'DELETE FROM %s' % self._table_name

        self.open()
        self.execute(query)
        self.close()

        self.create_table()

    def add(self, content_type, content_id, channel_id, channel_name, title, 
            thumbnail='', game_name='', duration=''):
        """Add or update a watch history entry
        
        Args:
            content_type: 'stream', 'video', or 'clip'
            content_id: The unique ID (channel_id for streams, video_id for VODs)
            channel_id: The channel/broadcaster ID
            channel_name: The channel/broadcaster display name
            title: The stream/video title
            thumbnail: URL to thumbnail image
            game_name: Name of the game being played
            duration: Duration string for VODs
        """
        timestamp = datetime.datetime.now()
        
        query = '''REPLACE INTO %s 
            (content_type, content_id, channel_id, channel_name, title, thumbnail, game_name, duration, time) 
            VALUES(?,?,?,?,?,?,?,?,?)''' % self._table_name

        self.open()
        self.execute(query, [content_type, content_id, channel_id, channel_name, 
                            title, thumbnail, game_name, duration, timestamp])
        self.close()
        
        # Cleanup old entries
        self._cleanup()

    def remove(self, content_type, content_id):
        """Remove a specific entry from watch history"""
        query = 'DELETE FROM %s WHERE content_type = ? AND content_id = ?' % self._table_name

        self.open()
        self.execute(query, [content_type, content_id])
        self.close()

    def _cleanup(self):
        """Remove old entries beyond max_items"""
        query = '''DELETE FROM %s WHERE rowid NOT IN 
            (SELECT rowid FROM %s ORDER BY time DESC LIMIT ?)''' % (self._table_name, self._table_name)

        self.open()
        self.execute(query, [self._max_items])
        self.close()


# Global instance
_watch_history = None


def get_watch_history():
    """Get the global WatchHistory instance"""
    global _watch_history
    if _watch_history is None:
        from . import utils
        max_items = utils.get_watch_history_size()
        _watch_history = WatchHistory(max_items=max_items)
    return _watch_history
