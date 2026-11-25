# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""The plugin: Twitch's pages as folders in Kodi's video window, and playback of what is picked there.

Addresses are plugin://plugin.video.twitch/<route>/?<params>; each route is a Plugin.route_<name> method.
Pages travel as their description (see pages), JSON in the 'desc' parameter."""
import json
import os
import urllib.parse

import xbmc
import xbmcgui
import xbmcplugin

from . import auth, compat, describe, follows, gql, http, kodi, pages, playback, players, signin, subscribe

BASE = 'plugin://%s/' % kodi.ADDON_ID
INLINE_MAX = 1  # a shelf this short is shown in place, not as a folder (a channel's "Live now")
PLAYABLE = ('live', 'video', 'clip')
CHANNEL_ITEMS = PLAYABLE + ('channel',)  # items about one channel: they get follow and subscribe entries
MENU_ART = {'home': 'live_channels.png', 'following': 'following.png', 'categories': 'games.png',
            'search': 'search.png', 'accounts': 'channels.png', 'settings': 'settings.png'}
ROUTE_ERRORS = (gql.GQLError, http.HTTPError, auth.AuthError, playback.PlaybackError)
SETTINGS = 5  # Kodi's "Settings"


# Addresses
def url_for(route, **params):
    """plugin://plugin.video.twitch/<route>/?<params>; dicts and lists travel as JSON."""
    query = {k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in params.items() if v is not None}
    return BASE + (route + '/' if route else '') + ('?' + urllib.parse.urlencode(query) if query else '')


def page_url(**desc):
    """The address of a page, from its description (see pages)."""
    return url_for('page', desc=desc)


def play_url(item):
    """The address that plays a stream, video or clip: play/?live=login, ?video=id or ?clip=slug."""
    return url_for('play', **{item['kind']: item['id']})


def _channel_url(login, title):
    return page_url(page='channel', login=login, title=title)


def _category_url(name, title):
    return page_url(page='category', name=name, title=title)


def item_url(item):
    """Where an item leads: playback, a channel or category page; None for kinds a listing doesn't show."""
    if item['kind'] in PLAYABLE:
        return play_url(item)
    if item['kind'] == 'channel':
        return _channel_url(item['login'], item['title'])
    if item['kind'] == 'category':
        return _category_url(item['id'], item['title'])
    if item['kind'] == 'scheduled':  # its category, when the schedule names one
        return _category_url(item['game'], item['game_title']) if item['game'] else url_for('noop')
    return None


def is_folder(item):
    """Whether an item opens a folder (a page) rather than playing or doing nothing."""
    return item['kind'] not in PLAYABLE and not (item['kind'] == 'scheduled' and not item['game'])


def error_message(exc):
    """What to tell the viewer when something failed: the sign-in, playback (Twitch's reason), or Twitch."""
    if isinstance(exc, auth.AuthError):
        return kodi.string(30073)
    if isinstance(exc, playback.PlaybackError):
        return kodi.formatted(30072, exc)
    return kodi.string(30070)


def _media(name):
    return os.path.join(kodi.ADDON_PATH, 'resources', 'media', name)


# Context menus of listed items
def _from_start_entry(item):
    """Play a live stream from the beginning of the broadcast, from its recording."""
    if item['kind'] != 'live':
        return []
    return [(kodi.string(30100), 'PlayMedia(%s)' % url_for('play', from_start=item['login']))]


def _go_to_entries(item):
    """Go to the channel and to the category of a stream, video or clip."""
    if item['kind'] not in PLAYABLE:
        return []
    entries = []
    if item.get('login'):
        entries.append((kodi.string(30037), 'Container.Update(%s)' % _channel_url(item['login'], item['channel'])))
    if item.get('game'):
        entries.append((kodi.string(30038), 'Container.Update(%s)' % _category_url(item['game'],
                                                                                    item['game_title'])))
    return entries


def _follow_entry(item):
    """Follow or unfollow the item's channel, while signed in. The listing doesn't know which it is (that would
    take a request per item), so the entry asks once it is picked."""
    if not auth.signed_in() or not item.get('login') or item['kind'] not in CHANNEL_ITEMS:
        return []
    return [(kodi.string(30094), 'RunPlugin(%s)' % url_for('follow', login=item['login'], name=item['channel']))]


def _subscribe_entry(item):
    """A QR code of the channel's subscribe page, to subscribe on a phone."""
    if not item.get('login') or item['kind'] not in CHANNEL_ITEMS:
        return []
    return [(kodi.string(30097), 'RunPlugin(%s)' % url_for('subscribe', login=item['login'], name=item['channel']))]


def _context_menu(item):
    """The context menu of a listed item, in the order the entries are shown."""
    return _from_start_entry(item) + _go_to_entries(item) + _follow_entry(item) + _subscribe_entry(item)


# Listed items
def _label(item):
    """The listing's label: a live stream is named by its channel first, as on Twitch's own lists."""
    if item['kind'] == 'live' and item['title'] != item['channel']:
        return '%s - %s' % (item['channel'], item['title'])
    return item['title']


def _art(item):
    """The item's pictures; upright ones (box art) are also the poster, for views that show posters."""
    art = {'thumb': item['thumb'], 'icon': item['thumb'], 'fanart': item.get('fanart') or ''}
    if item['kind'] == 'category' or item.get('poster'):
        art['poster'] = item['thumb']
    return art


def _set_info(li, item):
    """The item's video info: title, details text, category as genre, channel as studio, length and date."""
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
    li = xbmcgui.ListItem(_label(item), describe.meta_line(item), offscreen=True)
    li.setArt(_art(item))
    _set_info(li, item)
    if item['kind'] in PLAYABLE:
        li.setProperty('IsPlayable', 'true')
    li.addContextMenuItems(_context_menu(item))
    return li, is_folder(item)


# What playback resolves to
def _clip_item(url):
    """A clip's MP4 file, which Kodi plays on its own."""
    li = xbmcgui.ListItem(path=url, offscreen=True)
    li.setMimeType('video/mp4')
    li.setContentLookup(False)
    return li


def _playable(params):
    """The resolved item for play/?live=, ?video=, ?from_start= or ?clip=; PlaybackError for anything else."""
    if 'live' in params:
        return players.stream_item(playback.live_url(params['live']), live=True)
    if 'video' in params:
        return players.stream_item(playback.video_url(params['video']), live=False)
    if 'from_start' in params:
        return players.stream_item(playback.video_url(playback.recording_id(params['from_start'])), live=False,
                                   from_start=True)
    if 'clip' in params:
        return _clip_item(playback.clip_url(params['clip']))
    raise playback.PlaybackError('nothing to play')


class Plugin:
    """One run of the plugin: the route and parameters of the address Kodi called it with."""

    def __init__(self, argv):
        self.base = argv[0]
        self.handle = int(argv[1]) if len(argv) > 1 and argv[1].lstrip('-').isdigit() else -1
        query = argv[2][1:] if len(argv) > 2 and argv[2].startswith('?') else ''
        self.params = dict(urllib.parse.parse_qsl(query))
        self.route = urllib.parse.urlsplit(self.base).path.strip('/')

    def param_json(self, key, default=None):
        """A parameter that travels as JSON (a page's description, a shelf)."""
        try:
            return json.loads(self.params[key])
        except (KeyError, ValueError):
            return default

    def _take_old_address(self):
        """An earlier version's ?mode=... address (see compat): run this version's route for it instead."""
        route, params = compat.translate(self.params)
        self.route = route
        self.params = {k: json.dumps(v) if isinstance(v, dict) else str(v)
                       for k, v in params.items() if v is not None}

    def dispatch(self):
        """Run the route; when Twitch fails it, tell the viewer and end the call the way Kodi waits for."""
        try:
            if not self.route and self.params.get('mode'):
                self._take_old_address()
            handler = getattr(self, 'route_' + (self.route or 'root'), None)
            if handler is None:
                kodi.log('unknown route %r' % self.route)
                return self._end(False)
            return handler()
        except ROUTE_ERRORS as exc:
            self._fail(exc)
        return None

    def _fail(self, exc):
        """A route failed: say why, and let Kodi stop waiting (for playback, or for a folder's listing)."""
        kodi.log('%s failed: %s' % (self.route or 'root', exc))
        self._notify(error_message(exc), error=True)
        if self.route == 'play':
            xbmcplugin.setResolvedUrl(self.handle, False, xbmcgui.ListItem(offscreen=True))
        else:
            self._end(False)

    # Building a listing
    def _end(self, succeeded=True, cache=False):
        """Finish a folder's listing (when Kodi called for one: a script-like run has no handle)."""
        if self.handle >= 0:
            xbmcplugin.endOfDirectory(self.handle, succeeded=succeeded, cacheToDisc=cache)

    def _finish(self):
        """Finish a listing of Twitch's items, for views made for videos."""
        xbmcplugin.setContent(self.handle, 'videos')
        self._end()

    @staticmethod
    def _notify(message, error=False):
        xbmcgui.Dialog().notification(kodi.ADDON.getAddonInfo('name'), message,
                                      xbmcgui.NOTIFICATION_ERROR if error else xbmcgui.NOTIFICATION_INFO, 4000)

    def _add(self, url, li, folder):
        xbmcplugin.addDirectoryItem(self.handle, url, li, folder)

    def _add_menu(self, label, url, art, folder=True):
        """A main-menu entry; `art` is a file in resources/media, or a full path."""
        li = xbmcgui.ListItem(label, offscreen=True)
        icon = art if os.path.isabs(art) else _media(art)
        li.setArt({'icon': icon, 'thumb': icon, 'fanart': _media('fanart.jpg')})
        self._add(url, li, folder)

    def _render_items(self, items):
        """List items, leaving out the kinds a listing doesn't show."""
        for item in items:
            url = item_url(item)
            if url:
                li, folder = list_item(item)
                self._add(url, li, folder)

    @staticmethod
    def _shelf_ref(shelf):
        """What a shelf's folder needs to load it: its list, the list's parameters and its title."""
        return {'list': shelf['list'], 'params': shelf['params'], 'title': shelf['title']}

    def _add_shelf_folder(self, shelf, header):
        """A page's shelf as a folder, with the art of its first item (and the page's fanart, when it has one)."""
        first = shelf['items'][0]
        li = xbmcgui.ListItem(shelf['title'], offscreen=True)
        fanart = (header or {}).get('fanart') or first.get('fanart') or _media('fanart.jpg')
        li.setArt({'thumb': first['thumb'], 'icon': first['thumb'], 'fanart': fanart})
        self._add(url_for('shelf', shelf=self._shelf_ref(shelf)), li, True)

    def _add_next(self, shelf, cursor):
        """"Next page" at the end of a list that goes on."""
        if not cursor:
            return
        li = xbmcgui.ListItem(kodi.string(30028), offscreen=True)
        li.setArt({'icon': 'DefaultFolder.png', 'fanart': _media('fanart.jpg')})
        self._add(url_for('shelf', shelf=self._shelf_ref(shelf), cursor=cursor), li, True)

    def _render_page(self, page):
        """A page with one shelf lists that shelf's items; a page of several lists each shelf as a folder,
        except a shelf of one item (a channel's live stream), which is shown in place."""
        shelves = page['shelves']
        if len(shelves) == 1:
            self._render_items(shelves[0]['items'])
            self._add_next(shelves[0], shelves[0]['cursor'])
            return
        for shelf in shelves:
            if len(shelf['items']) <= INLINE_MAX:
                self._render_items(shelf['items'])
            else:
                self._add_shelf_folder(shelf, page['header'])

    # Routes
    def route_root(self):
        """The main menu: the TV interface, search, the pages, the account and settings."""
        self._add_menu(kodi.string(30005), url_for('tv'),
                       os.path.join(kodi.ADDON_PATH, 'resources', 'tv', 'media', 'icon.png'), folder=False)
        self._add_menu(kodi.string(30004), url_for('search_list'), MENU_ART['search'])
        for page in ('home', 'following', 'categories'):
            self._add_menu(pages.title_of({'page': page}), page_url(page=page), MENU_ART[page])
        account = auth.active_account()[1]
        self._add_menu(account['name'] if account else kodi.string(30006), url_for('accounts'),
                       MENU_ART['accounts'], folder=False)
        self._add_menu(xbmc.getLocalizedString(SETTINGS), url_for('settings'), MENU_ART['settings'], folder=False)
        self._end()

    def route_page(self):
        """A page (see pages): its shelves, or a notification of why it is empty."""
        page = pages.load(self.param_json('desc', {'page': 'home'}))
        if not page['shelves']:
            self._notify(page['message'])
        self._render_page(page)
        self._finish()

    def route_shelf(self):
        """A shelf on its own: a batch of its items, and "Next page" when it goes on."""
        shelf = self.param_json('shelf', {})
        items, cursor = pages.more(shelf, self.params.get('cursor'))
        self._render_items(items)
        self._add_next(shelf, cursor)
        self._finish()

    def _add_new_search(self):
        """"New search". Not a folder: Kodi runs it like a script, so its jump to the results isn't undone by
        Kodi going back from a folder that listed nothing."""
        li = xbmcgui.ListItem(kodi.string(30029), offscreen=True)
        li.setArt({'icon': _media('search.png'), 'thumb': _media('search.png')})
        self._add(url_for('search'), li, False)

    def _add_past_search(self, query):
        """A past search, opening its results, with entries to remove it or clear them all."""
        li = xbmcgui.ListItem(query, offscreen=True)
        li.setArt({'icon': _media('search.png'), 'thumb': _media('search.png')})
        li.addContextMenuItems([(kodi.string(30032), 'RunPlugin(%s)' % url_for('search_remove', q=query)),
                                (kodi.string(30030), 'RunPlugin(%s)' % url_for('search_clear'))])
        self._add(page_url(page='search', q=query), li, True)

    def route_search_list(self):
        """New search, then the past searches."""
        self._add_new_search()
        for query in pages.searches():
            self._add_past_search(query)
        self._end()

    def route_search(self):
        """New search: ask, then open the results at an address that holds the query. Listing them here would
        leave this address (no query) in Kodi's history, and coming back to it would ask again."""
        query = self.params.get('q') or xbmcgui.Dialog().input(kodi.string(30004))
        self._end(False)
        if query:
            pages.remember_search(query)
            xbmc.executebuiltin('Container.Update(%s)' % page_url(page='search', q=query))

    def route_search_remove(self):
        """Remove a past search (from its context menu) and show the list without it."""
        pages.forget_search(self.params.get('q', ''))
        xbmc.executebuiltin('Container.Refresh')

    def route_search_clear(self):
        """Clear the search history once the viewer confirms."""
        if xbmcgui.Dialog().yesno(kodi.string(30030), kodi.string(30033)):
            pages.clear_searches()
            xbmc.executebuiltin('Container.Refresh')

    def route_play(self):
        """Resolve a stream, video or clip for Kodi's player; with t=<seconds>, start a video there."""
        xbmcplugin.setResolvedUrl(self.handle, True, _playable(self.params))
        if self.params.get('t') and 'video' in self.params:
            players.start_at(self.params['video'], float(self.params['t']))

    def route_follow(self):
        """Follow or unfollow a channel (from a context menu), asking first; the listing shows the change."""
        if follows.ask_and_change(self.params['login'], self.params.get('name') or self.params['login']):
            xbmc.executebuiltin('Container.Refresh')

    def route_subscribe(self):
        subscribe.show(self.params['login'], self.params.get('name') or self.params['login'])

    def route_noop(self):
        """An entry with nothing to open (a scheduled stream without a category)."""

    def route_tv(self):
        """The TV interface, which is the add-on's script (tv.py)."""
        xbmc.executebuiltin('RunScript(%s)' % kodi.ADDON_ID)

    def route_accounts(self):
        """The accounts dialog (the main menu's account entry, or the settings' Switch account)."""
        if signin.accounts_menu():
            xbmc.executebuiltin('Container.Refresh')

    def route_sign_in(self):
        """Sign in (the settings' Sign in button)."""
        if signin.sign_in():
            xbmc.executebuiltin('Container.Refresh')

    def route_sign_out(self):
        """Sign out of the active account (the settings' Sign out button)."""
        if signin.sign_out():
            xbmc.executebuiltin('Container.Refresh')

    def route_settings(self):
        kodi.ADDON.openSettings()


def run(argv):
    """The plugin's entry point (default.py): argv is Kodi's (address, handle, query)."""
    Plugin(argv).dispatch()
