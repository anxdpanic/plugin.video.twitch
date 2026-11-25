# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""The TV window's tiles and rail entries, from the pages' items."""
import os

import xbmcgui

from .. import describe, kodi

LIVE_COLOR = 'FFEB0400'
BADGE_COLOR = 'E6000000'
ICONS = os.path.join(kodi.ADDON_PATH, 'resources', 'tv', 'media')


def icon(name):
    return os.path.join(ICONS, 'icon_%s.png' % name)


def rail_item(entry):
    li = xbmcgui.ListItem(entry['title'], offscreen=True)
    if entry.get('avatar'):
        li.setArt({'icon': entry['avatar']})
        li.setProperty('round', '1')
    else:
        li.setArt({'icon': icon(entry['icon'])})
    li.setProperty('tint', 'FFFFFFFF')
    return li


def _badge(li, text, color=BADGE_COLOR):
    li.setProperty('badge', text)
    li.setProperty('badge_color', color)


def media_tile(item):
    """A live stream, past broadcast or clip: its preview, a LIVE or length badge, and the details text."""
    li = xbmcgui.ListItem(item['title'], offscreen=True)
    li.setLabel2(describe.meta_line(item))
    li.setArt({'thumb': item['thumb'], 'fanart': item['fanart'] or item['thumb']})
    li.setProperty('plot', describe.plot(item))
    if item['kind'] == 'live':
        _badge(li, kodi.string(30039), LIVE_COLOR)
    elif item.get('duration'):
        _badge(li, describe.format_time(item['duration']))
    return li


def channel_tile(item):
    li = xbmcgui.ListItem(item['title'], offscreen=True)
    li.setLabel2(describe.meta_line(item))
    li.setArt({'thumb': item['thumb'], 'fanart': item['fanart']})
    li.setProperty('plot', describe.plot(item))
    li.setProperty('round', '1')
    if item['live']:
        _badge(li, kodi.string(30039), LIVE_COLOR)
    return li


def category_tile(item):
    """A category: its box art standing upright in the tile."""
    li = xbmcgui.ListItem(item['title'], offscreen=True)
    li.setLabel2(describe.meta_line(item))
    li.setArt({'thumb': item['thumb']})
    li.setProperty('plot', describe.plot(item))
    li.setProperty('poster', '1')
    return li


def action_tile(item):
    """A thing to do rather than a page (New search, Clear search history): an icon on a plain tile."""
    li = xbmcgui.ListItem(item['title'], offscreen=True)
    li.setArt({'icon': icon(item['icon'])})
    li.setProperty('icon_tile', '1')
    li.setProperty('plot', item.get('plot', ''))
    return li


def query_tile(item):
    """A past search, its words written large on the tile."""
    li = xbmcgui.ListItem(item['title'], offscreen=True)
    li.setProperty('text_tile', '1')
    li.setProperty('plot', item.get('plot', ''))
    return li


TILES = {'live': media_tile, 'video': media_tile, 'clip': media_tile, 'channel': channel_tile,
         'category': category_tile, 'action': action_tile, 'query': query_tile}


def tile(item):
    return TILES[item['kind']](item)
