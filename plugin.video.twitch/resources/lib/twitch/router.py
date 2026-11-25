# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""The plugin: Twitch's pages as folders in Kodi's video window, and playback of what is picked there."""
import json
import os
import urllib.parse

import xbmc
import xbmcgui
import xbmcplugin

from . import auth, describe, follows, gql, http, kodi, pages, playback, signin, subscribe

BASE = 'plugin://%s/' % kodi.ADDON_ID
INLINE_MAX = 1  # a shelf this short is shown in place, not as a folder (a channel's "Live now")
PLAYABLE = ('live', 'video', 'clip')
MENU_ART = {'home': 'live_channels.png', 'following': 'following.png', 'categories': 'games.png',
            'search': 'search.png', 'accounts': 'channels.png', 'settings': 'settings.png'}


def url_for(route, **params):
    """plugin://plugin.video.twitch/<route>/?<params>; dicts and lists travel as JSON."""
    query = {k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in params.items() if v is not None}
    return BASE + (route + '/' if route else '') + ('?' + urllib.parse.urlencode(query) if query else '')


def play_url(item):
    return url_for('play', **{item['kind']: item['id']})


def item_url(item):
    """Where an item leads: playback, a channel or category page, or a search."""
    if item['kind'] in PLAYABLE:
        return play_url(item)
    if item['kind'] == 'channel':
        return url_for('page', desc={'page': 'channel', 'login': item['login'], 'title': item['title']})
    if item['kind'] == 'category':
        return url_for('page', desc={'page': 'category', 'name': item['id'], 'title': item['title']})
    if item['kind'] == 'scheduled':  # its category, when the schedule names one
        if not item['game']:
            return url_for('noop')
        return url_for('page', desc={'page': 'category', 'name': item['game'], 'title': item['game_title']})
    return None


def is_folder(item):
    return item['kind'] not in PLAYABLE and not (item['kind'] == 'scheduled' and not item['game'])


def error_message(exc):
    if isinstance(exc, auth.AuthError):
        return kodi.string(30073)
    if isinstance(exc, playback.PlaybackError):
        return kodi.formatted(30072, exc)
    return kodi.string(30070)


def _media(name):
    return os.path.join(kodi.ADDON_PATH, 'resources', 'media', name)


def _follow_entry(item):
    """Follow or unfollow the item's channel, while signed in. The listing doesn't know which it is (that would
    take a request per item), so the entry asks once it is picked."""
    if not auth.signed_in() or not item.get('login') or item['kind'] not in PLAYABLE + ('channel',):
        return []
    return [(kodi.string(30094), 'RunPlugin(%s)' % url_for('follow', login=item['login'], name=item['channel']))]


def _context_menu(item):
    """Go to the channel and the category of a stream, video or clip, and follow or unfollow its channel."""
    menu = []
    if item['kind'] in PLAYABLE and item.get('login'):
        menu.append((kodi.string(30037), 'Container.Update(%s)' % url_for(
            'page', desc={'page': 'channel', 'login': item['login'], 'title': item['channel']})))
    if item['kind'] in PLAYABLE and item.get('game'):
        menu.append((kodi.string(30038), 'Container.Update(%s)' % url_for(
            'page', desc={'page': 'category', 'name': item['game'], 'title': item['game_title']})))
    return _from_start_entry(item) + menu + _follow_entry(item) + _subscribe_entry(item)


def _from_start_entry(item):
    """Play a live stream from the beginning of the broadcast, from its recording."""
    if item['kind'] != 'live':
        return []
    return [(kodi.string(30100), 'PlayMedia(%s)' % url_for('play', from_start=item['login']))]


def _subscribe_entry(item):
    """A QR code of the channel's subscribe page, to subscribe on a phone."""
    if not item.get('login') or item['kind'] not in PLAYABLE + ('channel',):
        return []
    return [(kodi.string(30097), 'RunPlugin(%s)' % url_for('subscribe', login=item['login'], name=item['channel']))]


def _set_info(li, item):
    tag = li.getVideoInfoTag()
    tag.setTitle(item['title'])
    tag.setPlot(describe.plot(item))
    tag.setMediaType('video')
    if item.get('game_title'):
        tag.setGenres([item['game_title']])
    if item.get('channel') and item['kind'] in PLAYABLE:
        tag.setStudios([item['channel']])
    if item.get('duration'):
        tag.setDuration(item['duration'])
    if item.get('published'):
        tag.setPremiered(item['published'][:10])


def list_item(item):
    """A listing's entry for an item, and whether it is a folder."""
    label = item['title']
    if item['kind'] == 'live':
        label = '%s - %s' % (item['channel'], item['title']) if item['title'] != item['channel'] else label
    li = xbmcgui.ListItem(label, describe.meta_line(item), offscreen=True)
    art = {'thumb': item['thumb'], 'icon': item['thumb'], 'fanart': item.get('fanart') or ''}
    if item['kind'] == 'category' or item.get('poster'):
        art['poster'] = item['thumb']
    li.setArt(art)
    _set_info(li, item)
    if item['kind'] in PLAYABLE:
        li.setProperty('IsPlayable', 'true')
    li.addContextMenuItems(_context_menu(item))
    return li, is_folder(item)


def _stream_item(url, live, from_start=False):
    """An HLS stream for InputStream Adaptive. A broadcast still being recorded is a growing playlist, which
    ISA plays like a live stream from its end unless told to start at the beginning (from_start)."""
    li = xbmcgui.ListItem(path=url, offscreen=True)
    li.setMimeType(playback.HLS_MIME)
    li.setContentLookup(False)
    li.setProperty('inputstream', 'inputstream.adaptive')
    if kodi.setting_bool('ask_quality'):
        li.setProperty('inputstream.adaptive.stream_selection_type', 'ask-quality')
    if live:
        li.setProperty('inputstream.adaptive.live_delay', '8')
    if from_start:
        li.setProperty('inputstream.adaptive.play_timeshift_buffer', 'true')
    return li


def _clip_item(url):
    li = xbmcgui.ListItem(path=url, offscreen=True)
    li.setMimeType('video/mp4')
    li.setContentLookup(False)
    return li


class Plugin:
    def __init__(self, argv):
        self.base = argv[0]
        self.handle = int(argv[1]) if len(argv) > 1 and argv[1].lstrip('-').isdigit() else -1
        query = argv[2][1:] if len(argv) > 2 and argv[2].startswith('?') else ''
        self.params = dict(urllib.parse.parse_qsl(query))
        self.route = urllib.parse.urlsplit(self.base).path.strip('/')

    def param_json(self, key, default=None):
        try:
            return json.loads(self.params[key])
        except (KeyError, ValueError):
            return default

    def dispatch(self):
        handler = getattr(self, 'route_' + (self.route or 'root'), None)
        if handler is None:
            kodi.log('unknown route %r' % self.route)
            return self._end(False)
        try:
            return handler()
        except (gql.GQLError, http.HTTPError, auth.AuthError, playback.PlaybackError) as exc:
            kodi.log('%s failed: %s' % (self.route or 'root', exc))
            self._notify(error_message(exc), error=True)
            if self.route == 'play':
                xbmcplugin.setResolvedUrl(self.handle, False, xbmcgui.ListItem(offscreen=True))
            elif self.handle >= 0:
                self._end(False)
        return None

    def _end(self, succeeded=True, cache=False):
        if self.handle >= 0:
            xbmcplugin.endOfDirectory(self.handle, succeeded=succeeded, cacheToDisc=cache)

    @staticmethod
    def _notify(message, error=False):
        xbmcgui.Dialog().notification(kodi.ADDON.getAddonInfo('name'), message,
                                      xbmcgui.NOTIFICATION_ERROR if error else xbmcgui.NOTIFICATION_INFO, 4000)

    def _add(self, url, li, folder):
        xbmcplugin.addDirectoryItem(self.handle, url, li, folder)

    def _add_menu(self, label, url, art_name, folder=True):
        li = xbmcgui.ListItem(label, offscreen=True)
        icon = art_name if os.path.isabs(art_name) else _media(art_name)
        li.setArt({'icon': icon, 'thumb': icon, 'fanart': _media('fanart.jpg')})
        self._add(url, li, folder)

    # Routes
    def route_root(self):
        self._add_menu(kodi.string(30005), url_for('tv'),
                       os.path.join(kodi.ADDON_PATH, 'resources', 'tv', 'media', 'icon.png'), folder=False)
        self._add_menu(kodi.string(30004), url_for('search_list'), MENU_ART['search'])
        for page in ('home', 'following', 'categories'):
            self._add_menu(pages.title_of({'page': page}), url_for('page', desc={'page': page}), MENU_ART[page])
        account = auth.active_account()[1]
        self._add_menu(account['name'] if account else kodi.string(30006), url_for('accounts'),
                       MENU_ART['accounts'], folder=False)
        self._add_menu(xbmc.getLocalizedString(5), url_for('settings'), MENU_ART['settings'], folder=False)
        self._end()

    def route_page(self):
        desc = self.param_json('desc', {'page': 'home'})
        page = pages.load(desc)
        shelves = page['shelves']
        if not shelves:
            self._notify(page['message'])
        if len(shelves) == 1:
            self._render_items(shelves[0]['items'])
            self._add_next(shelves[0], shelves[0]['cursor'])
        else:
            for shelf in shelves:
                if len(shelf['items']) <= INLINE_MAX:
                    self._render_items(shelf['items'])
                else:
                    self._add_shelf_folder(shelf, page['header'])
        self._finish()

    def route_shelf(self):
        shelf = self.param_json('shelf', {})
        items, cursor = pages.more(shelf, self.params.get('cursor'))
        self._render_items(items)
        self._add_next(shelf, cursor)
        self._finish()

    def _finish(self):
        xbmcplugin.setContent(self.handle, 'videos')
        self._end()

    def _shelf_ref(self, shelf):
        return {'list': shelf['list'], 'params': shelf['params'], 'title': shelf['title']}

    def _add_shelf_folder(self, shelf, header):
        """A page's shelf as a folder, with the art of its first item."""
        first = shelf['items'][0]
        li = xbmcgui.ListItem(shelf['title'], offscreen=True)
        fanart = (header or {}).get('fanart') or first.get('fanart') or _media('fanart.jpg')
        li.setArt({'thumb': first['thumb'], 'icon': first['thumb'], 'fanart': fanart})
        self._add(url_for('shelf', shelf=self._shelf_ref(shelf)), li, True)

    def _add_next(self, shelf, cursor):
        if not cursor:
            return
        li = xbmcgui.ListItem(kodi.string(30028), offscreen=True)
        li.setArt({'icon': 'DefaultFolder.png', 'fanart': _media('fanart.jpg')})
        self._add(url_for('shelf', shelf=self._shelf_ref(shelf), cursor=cursor), li, True)

    def _render_items(self, items):
        for item in items:
            url = item_url(item)
            if url:
                li, folder = list_item(item)
                self._add(url, li, folder)

    def route_search_list(self):
        """New search, then the past searches."""
        li = xbmcgui.ListItem(kodi.string(30029), offscreen=True)
        li.setArt({'icon': _media('search.png'), 'thumb': _media('search.png')})
        # Not a folder: Kodi runs it like a script, so its jump to the results isn't undone by Kodi going back
        # from a folder that listed nothing.
        self._add(url_for('search'), li, False)
        for query in pages.searches():
            li = xbmcgui.ListItem(query, offscreen=True)
            li.setArt({'icon': _media('search.png'), 'thumb': _media('search.png')})
            li.addContextMenuItems([(kodi.string(30032), 'RunPlugin(%s)' % url_for('search_remove', q=query)),
                                    (kodi.string(30030), 'RunPlugin(%s)' % url_for('search_clear'))])
            self._add(url_for('page', desc={'page': 'search', 'q': query}), li, True)
        self._end()

    def route_search(self):
        """New search: ask, then open the results at an address that holds the query. Listing them here would
        leave this address (no query) in Kodi's history, and coming back to it would ask again."""
        query = self.params.get('q') or xbmcgui.Dialog().input(kodi.string(30004))
        self._end(False)
        if query:
            pages.remember_search(query)
            xbmc.executebuiltin('Container.Update(%s)' % url_for('page', desc={'page': 'search', 'q': query}))

    def route_search_remove(self):
        pages.forget_search(self.params.get('q', ''))
        xbmc.executebuiltin('Container.Refresh')

    def route_search_clear(self):
        if xbmcgui.Dialog().yesno(kodi.string(30030), kodi.string(30033)):
            pages.clear_searches()
            xbmc.executebuiltin('Container.Refresh')

    def route_play(self):
        if 'live' in self.params:
            li = _stream_item(playback.live_url(self.params['live']), live=True)
        elif 'video' in self.params:
            li = _stream_item(playback.video_url(self.params['video']), live=False)
        elif 'from_start' in self.params:
            li = _stream_item(playback.video_url(playback.recording_id(self.params['from_start'])), live=False,
                              from_start=True)
        elif 'clip' in self.params:
            li = _clip_item(playback.clip_url(self.params['clip']))
        else:
            raise playback.PlaybackError('nothing to play')
        xbmcplugin.setResolvedUrl(self.handle, True, li)

    def route_follow(self):
        if follows.ask_and_change(self.params['login'], self.params.get('name') or self.params['login']):
            xbmc.executebuiltin('Container.Refresh')

    def route_subscribe(self):
        subscribe.show(self.params['login'], self.params.get('name') or self.params['login'])

    def route_noop(self):
        """An entry with nothing to open (a scheduled stream without a category)."""

    def route_tv(self):
        xbmc.executebuiltin('RunScript(%s)' % kodi.ADDON_ID)

    def route_accounts(self):
        if signin.accounts_menu():
            xbmc.executebuiltin('Container.Refresh')

    def route_sign_in(self):
        if signin.sign_in():
            xbmc.executebuiltin('Container.Refresh')

    def route_sign_out(self):
        if signin.sign_out():
            xbmc.executebuiltin('Container.Refresh')

    def route_settings(self):
        kodi.ADDON.openSettings()


def run(argv):
    Plugin(argv).dispatch()
