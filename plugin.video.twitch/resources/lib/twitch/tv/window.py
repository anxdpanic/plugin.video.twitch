# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""The TV interface's window: a navigation rail, the focused tile's details, and rows of tiles.

Kodi can't add rows to a window as it runs, so the window has two row lists: the focused row and a peek at the
next. Moving up or down fills them with other rows of the screen; each row keeps its tiles and the tile it
was on, so coming back to a row is instant."""
import traceback

import xbmc
import xbmcgui

from .. import auth, follows, gql, http, kodi, pages, playback, router, signin, subscribe
from . import items, model

RAIL = 100
ROWS = (200, 201)
MORE_AT = 6  # load more of a row once the focus is this close to its end

ACTION_LEFT, ACTION_RIGHT, ACTION_UP, ACTION_DOWN = 1, 2, 3, 4
ACTION_BACK = (9, 10, 92)  # parent dir, previous menu, back
ACTION_CONTEXT = (11, 117)  # info, context menu
ERRORS = (gql.GQLError, http.HTTPError, auth.AuthError, playback.PlaybackError)


def rail_entries():
    """The rail: Search, the pages, then the account and settings."""
    account = auth.active_account()[1]
    return [
        {'id': 'search', 'title': kodi.string(30004), 'icon': 'search'},
        {'id': 'home', 'title': kodi.string(30001), 'icon': 'home', 'desc': {'page': 'home'}},
        {'id': 'following', 'title': kodi.string(30002), 'icon': 'following', 'desc': {'page': 'following'}},
        {'id': 'categories', 'title': kodi.string(30003), 'icon': 'gaming', 'desc': {'page': 'categories'}},
        {'id': 'accounts', 'title': account['name'] if account else kodi.string(30006), 'icon': 'account',
         'avatar': (account or {}).get('avatar', '')},
        {'id': 'settings', 'title': xbmc.getLocalizedString(5), 'icon': 'settings'},
    ]


class TVWindow(xbmcgui.WindowXML):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entries = []
        self.stack = []
        self.top = 0
        self.current_entry = None

    def onInit(self):  # noqa: N802 (Kodi API)
        try:
            self._init()
        except Exception:
            # Kodi only prints a callback's error when debug logging is on; keep it in the log either way.
            kodi.log_error('TV interface failed to open: ' + traceback.format_exc())
            raise

    def _init(self):
        if self.stack:  # back from playback or a dialog: Kodi rebuilt the window
            self._fill_rail()
            self._show_rows()
            if not self.screen.rows:
                self.setFocusId(RAIL)  # the layout focuses the rows, and an empty page has none
            return
        self.entries = rail_entries()
        self._fill_rail()
        start = 'following' if auth.signed_in() else 'home'
        self._guarded(self._open_entry, next(e for e in self.entries if e['id'] == start))

    def onAction(self, action):  # noqa: N802
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
        if control_id == RAIL:
            position = self.getControl(RAIL).getSelectedPosition()
            if 0 <= position < len(self.entries):
                self._guarded(self._open_entry, self.entries[position])
        elif control_id == ROWS[0]:
            row = self._row(0)
            position = self.getControl(ROWS[0]).getSelectedPosition()
            if row and 0 <= position < len(row.items):
                row.pos = position  # back from playback, the window is rebuilt on this tile
                self._guarded(self._activate, row.items[position])

    # The rail
    def _fill_rail(self):
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

    def _open_entry(self, entry):
        if entry['id'] == 'search':
            self._push(model.LocalScreen(entry['title'], self._search_rows), replace=True, entry='search')
        elif entry['id'] == 'accounts':
            if signin.accounts_menu():
                self._restart()
        elif entry['id'] == 'settings':
            kodi.ADDON.openSettings()
            kodi.refresh()
        else:
            self._push(self._screen(entry['desc']), replace=True, entry=entry['id'])

    def _restart(self):
        """Another account: start again from its first page."""
        self.stack = []
        self.current_entry = None
        self._init()

    # Screens
    @staticmethod
    def _screen(desc):
        return model.Screen(desc, pages.load, pages.more)

    def _push(self, screen, replace=False, entry=None):
        self._busy(True)
        try:
            screen.open()
            screen.ensure(0)
        finally:
            self._busy(False)
        if self.stack:
            self.stack[-1].top = self.top
            row = self._row(0)
            if row:  # Back comes to this tile, however the new screen was opened
                row.pos = self.getControl(ROWS[0]).getSelectedPosition()
        if replace:
            self.stack = []
            self.current_entry = entry
            self._fill_rail()
        self.stack.append(screen)
        self.top = 0
        self._show_rows()
        self.setFocusId(ROWS[0] if screen.rows else RAIL)

    def _back(self, focus):
        if focus == RAIL or not self.stack:
            self.close()
        elif len(self.stack) > 1:
            self.stack.pop()
            screen = self.stack[-1]
            if hasattr(screen, 'refresh'):  # the search screen: a search just made goes to the top
                screen.refresh()
            self.top = min(screen.top, max(len(screen.rows) - 1, 0))
            self._show_rows()
        else:
            self.setFocusId(RAIL)

    @property
    def screen(self):
        return self.stack[-1] if self.stack else None

    def _row(self, slot):
        screen = self.screen
        if not screen or self.top + slot >= len(screen.rows):
            return None
        return screen.rows[self.top + slot]

    def _show_rows(self):
        screen = self.screen
        self.setProperty('screen.title', screen.title if screen else '')
        self.setProperty('message', screen.message if screen and not screen.rows else '')
        for slot, control_id in enumerate(ROWS):
            control = self.getControl(control_id)
            control.reset()
            row = self._row(slot)
            self.setProperty('row%d.title' % slot, row.title if row else '')
            if not row:
                continue
            if row.listitems is None:
                row.listitems = [items.tile(i) for i in row.items]
            control.addItems(row.listitems)
            control.selectItem(row.pos if slot == 0 else 0)

    def _move(self, step):
        screen = self.screen
        if not screen:
            return
        index = self.top + step
        if index < 0:
            return
        if index + model.LOOKAHEAD >= len(screen.rows) and screen.can_grow():
            self._guarded(screen.ensure, index)
        if index >= len(screen.rows):
            return
        row = self._row(0)
        if row:
            row.pos = self.getControl(ROWS[0]).getSelectedPosition()
        self.top = index
        self._show_rows()

    def _more_items(self):
        row = self._row(0)
        control = self.getControl(ROWS[0])
        if not row or not row.cursor or control.getSelectedPosition() < len(row.items) - MORE_AT:
            return
        fresh = self._guarded(self.screen.more_items, row) or []
        if fresh:
            new = [items.tile(i) for i in fresh]
            row.listitems.extend(new)
            control.addItems(new)

    # Picking a tile
    def _activate(self, item):
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

    def _open_channel(self, login, title):
        self._push(self._screen({'page': 'channel', 'login': login, 'title': title}))

    def _open_category(self, name, title):
        self._push(self._screen({'page': 'category', 'name': name, 'title': title}))

    def _context_menu(self):
        row = self._row(0)
        position = self.getControl(ROWS[0]).getSelectedPosition()
        if not row or not 0 <= position < len(row.items):
            return
        item = row.items[position]
        choices = self._guarded(self._choices, item) or []
        if not choices:
            return
        choice = xbmcgui.Dialog().contextmenu([label for label, _ in choices])
        if choice >= 0:
            self._guarded(choices[choice][1])

    def _choices(self, item):
        """[(label, action)] for a tile's context menu."""
        if item['kind'] == 'query':
            return [(kodi.string(30032), lambda: self._forget(item['title'])),
                    (kodi.string(30030), lambda: self._search_action('clear_searches'))]
        if item['kind'] not in router.PLAYABLE + ('channel',):
            return []
        desc = self.screen.desc if self.screen else {}
        choices = []
        if item['kind'] != 'channel' and item.get('login') and desc.get('login') != item['login']:
            choices.append((kodi.string(30037), lambda: self._open_channel(item['login'], item['channel'])))
        if item.get('game') and desc.get('name') != item['game']:
            choices.append((kodi.string(30038), lambda: self._open_category(item['game'], item['game_title'])))
        return choices + self._follow_choice(item) + self._subscribe_choice(item)

    @staticmethod
    def _subscribe_choice(item):
        if not item.get('login'):
            return []
        return [(kodi.string(30097), lambda: subscribe.show(item['login'], item['channel']))]

    def _follow_choice(self, item):
        """Follow or Unfollow the tile's channel, as it stands now (one lookup when the menu opens)."""
        if not auth.signed_in() or not item.get('login'):
            return []
        user_id, following = follows.status(item['login'])
        label = kodi.formatted(30091 if following else 30090, item['channel'])
        return [(label, lambda: self._change_follow(user_id, following, item['channel']))]

    def _change_follow(self, user_id, following, name):
        follows.change(user_id, following, name)
        screen = self.screen
        if screen and screen.desc.get('page') in ('following', 'home'):  # their rows list the followed channels
            fresh = self._screen(screen.desc).open()
            fresh.ensure(self.top)
            self.stack[-1] = fresh
            self.top = min(self.top, max(len(fresh.rows) - 1, 0))
            self._show_rows()

    # Search
    @staticmethod
    def _search_rows():
        """The search screen: New search (and Clear when there is something to clear), then past searches."""
        past = pages.searches()
        actions = [{'kind': 'action', 'id': 'new_search', 'title': kodi.string(30029), 'icon': 'search',
                    'target': 'new_search', 'plot': kodi.string(30034)}]
        if past:
            actions.append({'kind': 'action', 'id': 'clear_searches', 'title': kodi.string(30030), 'icon': 'clear',
                            'target': 'clear_searches', 'plot': kodi.string(30033)})
        rows = [model.Row(kodi.string(30004), actions)]
        if past:
            rows.append(model.Row(kodi.string(30031), [
                {'kind': 'query', 'id': query, 'title': query, 'plot': kodi.formatted(30035, query)}
                for query in past]))
        return rows

    def _search_action(self, action):
        if action == 'new_search':
            query = xbmcgui.Dialog().input(kodi.string(30004))
            if query:
                self._search(query)
        elif action == 'clear_searches' and xbmcgui.Dialog().yesno(kodi.string(30030), kodi.string(30033)):
            pages.clear_searches()
            self._refresh_search()

    def _search(self, query):
        pages.remember_search(query)
        self._push(self._screen({'page': 'search', 'q': query, 'title': query}))

    def _forget(self, query):
        pages.forget_search(query)
        self._refresh_search()

    def _refresh_search(self):
        screen = self.screen
        if hasattr(screen, 'refresh'):
            screen.refresh()
            self.top = min(self.top, max(len(screen.rows) - 1, 0))
            self._show_rows()

    # Helpers
    def _busy(self, on):
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
