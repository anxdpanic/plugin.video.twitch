# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2024 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import utils, menu_items
from ..addon.common import kodi
from ..addon.constants import Keys, LINE_LENGTH, MODES
from ..addon.converter import JsonListItemConverter
from ..addon.watch_history import get_watch_history
from ..addon.utils import i18n


def route(api, content_type=None):
    """Display watch history
    
    Args:
        api: Twitch API instance
        content_type: 'stream', 'video', 'clip' or None for all
    """
    converter = JsonListItemConverter(LINE_LENGTH)
    watch_history = get_watch_history()
    
    kodi.set_view('videos', set_sort=False)
    
    # Get history items
    items = watch_history.list(content_type=content_type)
    
    if not items:
        # Show empty message
        kodi.create_item({
            'label': i18n('no_watch_history'),
            'path': kodi.get_plugin_url({'mode': MODES.MAIN}),
            'is_folder': True,
            'is_playable': False
        })
        kodi.end_of_directory()
        return
    
    for item in items:
        context_menu = []
        
        # Remove from history context menu
        context_menu.append((
            i18n('remove_from_history'),
            'RunPlugin(%s)' % kodi.get_plugin_url({
                'mode': MODES.CLEARWATCHHISTORY,
                'content_type': item['content_type'],
                'content_id': item['content_id']
            })
        ))
        
        if item['content_type'] == 'stream':
            # Live stream - play channel
            label = '[COLOR orange][LIVE][/COLOR] %s' % item['channel_name']
            if item['title']:
                label += ' - %s' % item['title']
            if item['game_name']:
                label += ' [%s]' % item['game_name']
            
            list_item = {
                'label': label,
                'path': kodi.get_plugin_url({
                    'mode': MODES.PLAY,
                    'channel_id': item['channel_id'],
                    'channel_name': item['channel_name']
                }),
                'context_menu': context_menu,
                'is_playable': True,
                'info': {
                    'plot': '%s\n%s' % (item['title'], item['game_name']) if item['game_name'] else item['title'],
                    'mediatype': 'video'
                }
            }
            if item['thumbnail']:
                list_item['art'] = {
                    'thumb': item['thumbnail'],
                    'poster': item['thumbnail'],
                    'icon': item['thumbnail']
                }
            kodi.create_item(list_item)
            
        elif item['content_type'] == 'video':
            # VOD
            label = item['channel_name']
            if item['title']:
                label += ' - %s' % item['title']
            if item['duration']:
                label += ' (%s)' % item['duration']
            
            list_item = {
                'label': label,
                'path': kodi.get_plugin_url({
                    'mode': MODES.PLAY,
                    'video_id': item['content_id']
                }),
                'context_menu': context_menu,
                'is_playable': True,
                'info': {
                    'plot': '%s\n%s' % (item['title'], item['game_name']) if item['game_name'] else item['title'],
                    'mediatype': 'video',
                    'duration': item['duration'] if item['duration'] else ''
                }
            }
            if item['thumbnail']:
                list_item['art'] = {
                    'thumb': item['thumbnail'],
                    'poster': item['thumbnail'],
                    'icon': item['thumbnail']
                }
            kodi.create_item(list_item)
            
        elif item['content_type'] == 'clip':
            # Clip
            label = item['channel_name']
            if item['title']:
                label += ' - %s' % item['title']
            
            list_item = {
                'label': label,
                'path': kodi.get_plugin_url({
                    'mode': MODES.PLAY,
                    'slug': item['content_id']
                }),
                'context_menu': context_menu,
                'is_playable': True,
                'info': {
                    'plot': item['title'],
                    'mediatype': 'video'
                }
            }
            if item['thumbnail']:
                list_item['art'] = {
                    'thumb': item['thumbnail'],
                    'poster': item['thumbnail'],
                    'icon': item['thumbnail']
                }
            kodi.create_item(list_item)
    
    # Add clear history option at the end
    kodi.create_item({
        'label': '[COLOR red]%s[/COLOR]' % i18n('clear_watch_history'),
        'path': kodi.get_plugin_url({'mode': MODES.CLEARWATCHHISTORY, 'clear_all': 'true'}),
        'is_folder': False,
        'is_playable': False,
        'context_menu': []
    })
    
    kodi.end_of_directory()
