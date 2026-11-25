# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""What the TV interface shows, as rows: no Kodi calls here, so it can be tested on its own."""
GRID_COLUMNS = 4  # tiles per row when a page is a single list (categories, a "see all")
LOOKAHEAD = 2  # rows kept loaded below the focused one


class Row:
    def __init__(self, title, items, shelf=None, cursor=None, grid=False, avatars=False):
        self.title = title
        self.items = items
        self.shelf = shelf  # the page's shelf this row shows, to load more of it
        self.cursor = cursor  # continues this row with more items (shelf rows only)
        self.grid = grid
        self.avatars = avatars  # a row of channels, shown as round pictures
        self.pos = 0  # the tile that had focus, restored when the row comes back
        self.listitems = None  # built by the window the first time the row is shown


class Screen:
    """One page as rows. A page of shelves (Home, a channel, a category) gives a row per shelf, each going
    on to the right as the focus nears its end; a page that is a single list is cut into rows of GRID_COLUMNS
    tiles and loads more of the list as the focus nears the last row."""

    def __init__(self, desc, load, more):
        self.desc = desc
        self._load = load  # desc -> page (pages.load)
        self._more = more  # (shelf, cursor) -> (items, cursor) (pages.more)
        self.title = ''
        self.rows = []
        self.header = None
        self.message = ''
        self.grid = None  # {'shelf', 'items', 'cursor'} when the page is a single list
        self.top = 0

    def open(self):
        page = self._load(self.desc)
        self.title = page['title']
        self.header = page['header']
        self.message = page['message']
        self.rows = []
        shelves = page['shelves']
        if len(shelves) == 1:
            self.grid = {'shelf': shelves[0], 'items': [], 'cursor': None}
            self._add_grid_items(shelves[0]['items'], shelves[0]['cursor'])
        else:
            self.rows = [Row(s['title'], list(s['items']), s, s['cursor'], avatars=s['avatars']) for s in shelves]
        return self

    def can_grow(self):
        return bool(self.grid and self.grid['cursor'])

    def ensure(self, index):
        """Load more of a single list until there are LOOKAHEAD rows below `index`, or nothing more."""
        while index + LOOKAHEAD >= len(self.rows) and self.can_grow():
            grid = self.grid
            before = len(grid['items'])
            items, cursor = self._more(grid['shelf'], grid['cursor'])
            self._add_grid_items(items, cursor)
            if len(grid['items']) == before:
                grid['cursor'] = None  # a batch with nothing new: stop rather than ask again and again

    def _add_grid_items(self, items, cursor):
        grid = self.grid
        seen = {i['id'] for i in grid['items']}
        for item in items:
            if item['id'] not in seen:
                grid['items'].append(item)
                seen.add(item['id'])
        grid['cursor'] = cursor
        # Rows already full keep their state; the last, part-filled one is cut again.
        full = [r for r in self.rows if len(r.items) == GRID_COLUMNS]
        del self.rows[len(full):]
        title = grid['shelf']['title'] if self.desc.get('page') != 'list' else ''
        for offset in range(len(full) * GRID_COLUMNS, len(grid['items']), GRID_COLUMNS):
            chunk = grid['items'][offset:offset + GRID_COLUMNS]
            self.rows.append(Row(title if offset == 0 else '', chunk, grid=True, avatars=grid['shelf']['avatars']))

    def more_items(self, row):
        """The next items of a shelf's row (it scrolls on to the right); [] when it has no more."""
        if row.grid or not row.cursor:
            return []
        items, cursor = self._more(row.shelf, row.cursor)
        row.cursor = cursor if cursor != row.cursor else None
        seen = {i['id'] for i in row.items}
        fresh = [i for i in items if i['id'] not in seen]
        row.items.extend(fresh)
        return fresh


class LocalScreen(Screen):
    """A screen made here rather than fetched from Twitch (the search screen). build() returns its rows,
    and is asked again whenever the screen comes back into view, so it shows what changed meanwhile."""

    def __init__(self, title, build):
        super().__init__({'page': None}, None, None)
        self.title = title
        self._build = build

    def open(self):
        self.rows = self._build()
        return self

    refresh = open

    def can_grow(self):
        return False
