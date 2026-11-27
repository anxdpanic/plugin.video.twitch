# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""The TV interface's window: a navigation rail, the focused tile's details, and rows of tiles.

Kodi can't add rows to a window as it runs, so the window has two row lists: the focused row and a peek at the
next. Moving up or down fills them with other rows of the screen; each row keeps its tiles and the tile it
was on, so coming back to a row is instant.

Screens stack up as pages are opened (a channel from Home, a category from the channel, ...); Back takes the
top one off, and picking a rail entry starts the stack again from that page."""
import traceback

import xbmc
import xbmcgui

from .. import auth, follows, gql, http, kodi, pages, playback, router, signin, subscribe
from . import items, model

RAIL = 100  # control ids in resources/tv/twitch-tv.xml
ROWS = (200, 201)  # the focused row, and the peek at the next
MORE_AT = 6  # load more of a row once the focus is this close to its end

ACTION_LEFT, ACTION_RIGHT, ACTION_UP, ACTION_DOWN = 1, 2, 3, 4
ACTION_BACK = (9, 10, 92)  # parent dir, previous menu, back
ACTION_CONTEXT = (11, 117)  # info, context menu
ERRORS = (gql.GQLError, http.HTTPError, auth.AuthError, playback.PlaybackError)
SETTINGS = 5  # Kodi's "Settings"


def rail_entries():
    """The rail: Search, the pages, then the account (with its picture) and settings."""
    account = auth.active_account()[1]
    return [
        {'id': 'search', 'title': kodi.string(30004), 'icon': 'search'},
        {'id': 'home', 'title': kodi.string(30001), 'icon': 'home', 'desc': {'page': 'home'}},
        {'id': 'following', 'title': kodi.string(30002), 'icon': 'following', 'desc': {'page': 'following'}},
        {'id': 'categories', 'title': kodi.string(30003), 'icon': 'gaming', 'desc': {'page': 'categories'}},
        {'id': 'accounts', 'title': account['name'] if account else kodi.string(30006), 'icon': 'account',
         'avatar': (account or {}).get('avatar', '')},
        {'id': 'settings', 'title': xbmc.getLocalizedString(SETTINGS), 'icon': 'settings'},
    ]


def _search_actions(past):
    """The search screen's first row: New search, and Clear search history when there is one."""
    actions = [{'kind': 'action', 'id': 'new_search', 'title': kodi.string(30029), 'icon': 'search',
                'target': 'new_search', 'plot': kodi.string(30034)}]
    if past:
        actions.append({'kind': 'action', 'id': 'clear_searches', 'title': kodi.string(30030), 'icon': 'clear',
                        'target': 'clear_searches', 'plot': kodi.string(30033)})
    return actions


def _past_searches_row(past):
    """The past searches, each a tile with its words written large."""
    return model.Row(kodi.string(30031), [{'kind': 'query', 'id': query, 'title': query,
                                           'plot': kodi.formatted(30035, query)} for query in past])


def search_rows():
    """The search screen: the actions, then the past searches (when there are any)."""
    past = pages.searches()
    rows = [model.Row(kodi.string(30004), _search_actions(past))]
    if past:
        rows.append(_past_searches_row(past))
    return rows


def _screen(desc):
    return model.Screen(desc, pages.load, pages.more)


class TVWindow(xbmcgui.WindowXML):
    """The TV interface's window (modal: tv.open_window runs it until Back leaves it)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entries = []  # the rail's entries (rail_entries)
        self.stack = []  # the screens opened, the shown one last
        self.top = 0  # the shown screen's focused row
        self.current_entry = None  # id of the rail entry the stack started from, marked on the rail

    # Kodi's callbacks
    def onInit(self):  # noqa: N802 (Kodi API)
        try:
            self._init()
        except Exception:
            # Kodi only prints a callback's error when debug logging is on; keep it in the log either way.
            kodi.log_error('TV interface failed to open: ' + traceback.format_exc())
            raise

    def onAction(self, action):  # noqa: N802
        """Back anywhere; on the rows: up and down move between rows, right loads more of a row near its
        end, and Menu or Info opens the tile's menu. Kodi itself moves within a row and to the rail."""
        action_id = action.getId()
        focus = self.getFocusId()
        if action_id in ACTION_BACK:
            self._back(focus)
        elif focus == ROWS[0] and action_id == ACTION_DOWN:
            self._move(1)
        elif focus == ROWS[0] and action_id == ACTION_UP:
            self._move(-1)
        elif focus == ROWS[0] and action_id == ACTION_RIGHT:
            self._more_items()
        elif focus == ROWS[0] and action_id in ACTION_CONTEXT:
            self._context_menu()

    def onClick(self, control_id):  # noqa: N802
        """OK on a rail entry opens it; OK on a tile plays or opens it."""
        if control_id == RAIL:
            self._click_rail()
        elif control_id == ROWS[0]:
            self._click_tile()

    # Opening and coming back
    def _init(self):
        """The window was (re)built: the first time, open the start page; after playback or a dialog (Kodi
        builds the window again), show what was there."""
        if self.stack:
            self._restore()
        else:
            self._start()

    def _start(self):
        """Fill the rail and open Following when signed in, Home otherwise."""
        self.entries = rail_entries()
        self._fill_rail()
        start = 'following' if auth.signed_in() else 'home'
        self._guarded(self._open_entry, next(e for e in self.entries if e['id'] == start))

    def _restore(self):
        """Show again what was shown before Kodi rebuilt the window."""
        self._fill_rail()
        self._show_rows()
        if not self.screen.rows:
            self.setFocusId(RAIL)  # the layout focuses the rows, and an empty page has none

    def _restart(self):
        """Another account: start again from its first page."""
        self.stack = []
        self.current_entry = None
        self._init()

    # The rail
    def _fill_rail(self):
        """Put the entries on the rail, marking and selecting the one the shown page came from."""
        rail = self.getControl(RAIL)
        rail.reset()
        current = 0
        for index, entry in enumerate(self.entries):
            li = items.rail_item(entry)
            if entry['id'] == self.current_entry:
                li.setProperty('current', '1')
                current = index
            rail.addItem(li)
        rail.selectItem(current)  # the rail opens on the page being shown

    def _click_rail(self):
        position = self.getControl(RAIL).getSelectedPosition()
        if 0 <= position < len(self.entries):
            self._guarded(self._open_entry, self.entries[position])

    def _open_entry(self, entry):
        """A rail entry: the search screen, the accounts dialog, the settings, or a page."""
        if entry['id'] == 'search':
            self._push(model.LocalScreen(entry['title'], search_rows), replace=True, entry='search')
        elif entry['id'] == 'accounts':
            if signin.accounts_menu():
                self._restart()
        elif entry['id'] == 'settings':
            kodi.ADDON.openSettings()
            kodi.refresh()
        else:
            self._push(_screen(entry['desc']), replace=True, entry=entry['id'])

    # Screens
    @property
    def screen(self):
        """The screen shown, or None before the first one opens."""
        return self.stack[-1] if self.stack else None

    def _row(self, slot):
        """The row in a slot (0 is the focused one, 1 the peek below it), or None past the last row."""
        screen = self.screen
        if not screen or self.top + slot >= len(screen.rows):
            return None
        return screen.rows[self.top + slot]

    def _focused_position(self):
        return self.getControl(ROWS[0]).getSelectedPosition()

    def _remember_position(self):
        """Note the focused row and tile of the shown screen, so Back returns to them."""
        if not self.stack:
            return
        self.screen.top = self.top
        row = self._row(0)
        if row:
            row.pos = self._focused_position()

    def _open(self, screen):
        """Load a screen and the rows below its first one, showing "Loading" meanwhile."""
        self._busy(True)
        try:
            screen.open()
            screen.ensure(0)
        finally:
            self._busy(False)

    def _push(self, screen, replace=False, entry=None):
        """Open a screen on top of the shown one; with `replace`, as the start of a new stack from the rail
        entry `entry`."""
        self._open(screen)
        self._remember_position()
        if replace:
            self.stack = []
            self.current_entry = entry
            self._fill_rail()
        self.stack.append(screen)
        self.top = 0
        self._show_rows()
        self.setFocusId(ROWS[0] if screen.rows else RAIL)

    def _back(self, focus):
        """Back: from the rail, leave; on a screen opened from another, go back to that one (at the row and
        tile it was on); on the first screen, go to the rail."""
        if focus == RAIL or not self.stack:
            self.close()
        elif len(self.stack) > 1:
            self.stack.pop()
            screen = self.screen
            if hasattr(screen, 'refresh'):  # the search screen: a search just made goes to the top
                screen.refresh()
            self.top = min(screen.top, max(len(screen.rows) - 1, 0))
            self._show_rows()
        else:
            self.setFocusId(RAIL)

    def _reload(self):
        """Load the shown screen again (the page cache was cleared), keeping the focused row where it can."""
        fresh = _screen(self.screen.desc).open()
        fresh.ensure(self.top)
        self.stack[-1] = fresh
        self.top = min(self.top, max(len(fresh.rows) - 1, 0))
        self._show_rows()

    # The rows
    def _fill_row(self, slot, control_id):
        """Show a slot's row in its list control: its title, its tiles (built the first time) and, for the
        focused row, the tile it was on."""
        control = self.getControl(control_id)
        control.reset()
        row = self._row(slot)
        self.setProperty('row%d.title' % slot, row.title if row else '')
        if not row:
            return
        if row.listitems is None:
            row.listitems = [items.tile(i) for i in row.items]
        control.addItems(row.listitems)
        control.selectItem(row.pos if slot == 0 else 0)

    def _show_rows(self):
        """Show the screen's title, its message when it is empty, and the two rows from the focused one."""
        screen = self.screen
        self.setProperty('screen.title', screen.title if screen else '')
        self.setProperty('message', screen.message if screen and not screen.rows else '')
        for slot, control_id in enumerate(ROWS):
            self._fill_row(slot, control_id)

    def _move(self, step):
        """Move the focus a row up (-1) or down (1), loading more rows first when the end is near."""
        screen = self.screen
        index = self.top + step
        if not screen or index < 0:
            return
        if index + model.LOOKAHEAD >= len(screen.rows) and screen.can_grow():
            self._guarded(screen.ensure, index)
        if index >= len(screen.rows):
            return
        row = self._row(0)
        if row:
            row.pos = self._focused_position()
        self.top = index
        self._show_rows()

    def _more_items(self):
        """Near the end of a shelf's row, load its next batch and add the tiles to the row in place."""
        row = self._row(0)
        if not row or not row.cursor or self._focused_position() < len(row.items) - MORE_AT:
            return
        fresh = self._guarded(self.screen.more_items, row) or []
        if fresh:
            new = [items.tile(i) for i in fresh]
            row.listitems.extend(new)
            self.getControl(ROWS[0]).addItems(new)

    # Tiles
    def _focused_item(self):
        """The item of the focused tile, or None."""
        row = self._row(0)
        position = self._focused_position()
        return row.items[position] if row and 0 <= position < len(row.items) else None

    def _click_tile(self):
        """OK on a tile: remember it as the row's focused tile, then play or open it."""
        item = self._focused_item()
        if item:
            self._row(0).pos = self._focused_position()  # back from playback, the window is rebuilt on this tile
            self._guarded(self._activate, item)

    def _activate(self, item):
        """What OK on a tile does: run a search action, search again, play, or open a page."""
        kind = item['kind']
        if kind == 'action':
            self._search_action(item['target'])
        elif kind == 'query':
            self._search(item['title'])
        elif kind in router.PLAYABLE:
            xbmc.executebuiltin('PlayMedia(%s)' % router.play_url(item))
        elif kind == 'channel':
            self._open_channel(item['login'], item['title'])
        elif kind == 'category':
            self._open_category(item['id'], item['title'])
        elif kind == 'scheduled' and item['game']:
            self._open_category(item['game'], item['game_title'])

    def _open_channel(self, login, title):
        self._push(_screen({'page': 'channel', 'login': login, 'title': title}))

    def _open_category(self, name, title):
        self._push(_screen({'page': 'category', 'name': name, 'title': title}))

    # A tile's context menu
    def _context_menu(self):
        """The focused tile's menu; the picked entry runs guarded, like everything that reaches Twitch."""
        item = self._focused_item()
        choices = self._guarded(self._choices, item) if item else None
        if not choices:
            return
        choice = xbmcgui.Dialog().contextmenu([label for label, _ in choices])
        if choice >= 0:
            self._guarded(choices[choice][1])

    def _choices(self, item):
        """[(label, action)] for a tile's context menu: a past search's, or one about a channel's content."""
        if item['kind'] == 'query':
            return self._query_choices(item)
        if item['kind'] not in router.CHANNEL_ITEMS:
            return []
        return (self._choose_quality_choice(item) + self._from_start_choice(item) + self._go_to_choices(item)
                + self._follow_choice(item) + self._subscribe_choice(item))

    def _query_choices(self, item):
        """A past search's menu: remove it, or clear them all."""
        return [(kodi.string(30032), lambda: self._forget(item['title'])),
                (kodi.string(30030), lambda: self._search_action('clear_searches'))]

    @staticmethod
    def _choose_quality_choice(item):
        """Play (choose quality): pick the quality this once."""
        if item['kind'] not in router.PLAYABLE:
            return []
        return [(kodi.string(30120), lambda: xbmc.executebuiltin('PlayMedia(%s)' % router.choose_quality_url(item)))]

    @staticmethod
    def _from_start_choice(item):
        if item['kind'] != 'live':
            return []
        return [(kodi.string(30100), lambda: xbmc.executebuiltin(
            'PlayMedia(%s)' % router.url_for('play', from_start=item['login'])))]

    def _go_to_choices(self, item):
        """Go to the tile's channel and category, unless that is the page already shown."""
        desc = self.screen.desc if self.screen else {}
        choices = []
        if item['kind'] != 'channel' and item.get('login') and desc.get('login') != item['login']:
            choices.append((kodi.string(30037), lambda: self._open_channel(item['login'], item['channel'])))
        if item.get('game') and desc.get('name') != item['game']:
            choices.append((kodi.string(30038), lambda: self._open_category(item['game'], item['game_title'])))
        return choices

    def _follow_choice(self, item):
        """Follow or Unfollow the tile's channel, as it stands now (one lookup when the menu opens)."""
        if not auth.signed_in() or not item.get('login'):
            return []
        try:
            user_id, following = follows.status(item['login'])
        except ERRORS as exc:  # the rest of the menu still works without it
            kodi.log('TV interface: no follow status for %s: %s' % (item['login'], exc))
            return []
        label = kodi.formatted(30091 if following else 30090, item['channel'])
        return [(label, lambda: self._change_follow(user_id, following, item['channel']))]

    @staticmethod
    def _subscribe_choice(item):
        if not item.get('login'):
            return []
        return [(kodi.string(30097), lambda: subscribe.show(item['login'], item['channel']))]

    def _change_follow(self, user_id, following, name):
        """Follow or unfollow; Following and Home list the followed channels, so they are loaded again."""
        follows.change(user_id, following, name)
        if self.screen and self.screen.desc.get('page') in ('following', 'home'):
            self._reload()

    # Search
    def _search_action(self, action):
        """New search: ask, then search. Clear search history: confirm, then clear."""
        if action == 'new_search':
            query = xbmcgui.Dialog().input(kodi.string(30004))
            if query:
                self._search(query)
        elif action == 'clear_searches' and xbmcgui.Dialog().yesno(kodi.string(30030), kodi.string(30033)):
            pages.clear_searches()
            self._refresh_search()

    def _search(self, query):
        """Open the results of a search, remembering it."""
        pages.remember_search(query)
        self._push(_screen({'page': 'search', 'q': query, 'title': query}))

    def _forget(self, query):
        pages.forget_search(query)
        self._refresh_search()

    def _refresh_search(self):
        """Show the search screen again after its history changed."""
        screen = self.screen
        if hasattr(screen, 'refresh'):
            screen.refresh()
            self.top = min(self.top, max(len(screen.rows) - 1, 0))
            self._show_rows()

    def _busy(self, on):
        """Show or hide the "Loading" badge."""
        self.setProperty('busy', kodi.string(30036) if on else '')

    def _guarded(self, func, *args):
        """Run func, showing a short message instead of failing when Twitch can't be reached."""
        self._busy(True)
        try:
            return func(*args)
        except ERRORS as exc:
            kodi.log('TV interface: %s' % exc)
            xbmcgui.Dialog().notification(kodi.ADDON.getAddonInfo('name'), router.error_message(exc),
                                          xbmcgui.NOTIFICATION_ERROR, 4000)
        finally:
            self._busy(False)
        return None
