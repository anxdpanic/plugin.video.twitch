# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""The add-on's pages as shelves (rows of items), shared by the plugin listings and the TV interface.

A page is described by a dict, {'page': 'home'} or {'page': 'channel', 'login': ...}, so it can travel in a
plugin URL. Loading it runs the first batch of every GraphQL shelf, and the page's own details, in one
request; the followed-channel shelves come from Helix on their own.

What Twitch answered is cached briefly (PAGE_TTL), per account, so coming back to a listing doesn't fetch
it again; the shelf titles are worded afresh each time, so a language change shows at once."""
import json

from . import auth, gql, http, kodi, lists, parser

PAGE_TTL = 120  # seconds: back to a listing within this time shows it as it was
SEARCH_HISTORY = 20  # past searches kept
STATE = 'state.json'

# page -> [(list key, keys of the page's description passed on to the list, title string id, round pictures)]
# A key 'list:TYPE' passes TYPE as the list's 'type' parameter.
SHELVES = {
    'home': [('followed_live', (), 30010, False), ('top_streams', (), 30011, False), ('top_games', (), 30012, False)],
    'following': [('followed_live', (), 30013, False), ('follows', (), 30015, True),
                  ('followed_games', (), 30016, False)],
    'categories': [('top_games', (), 30012, False)],
    'category': [('game_streams', ('name',), 30018, False), ('game_clips', ('name',), 30019, False),
                 ('game_videos', ('name',), 30020, False)],
    'channel': [('channel_live', ('login',), 30021, False), ('channel_schedule', ('login',), 30103, False),
                ('channel_videos:ARCHIVE', ('login',), 30022, False),
                ('channel_videos:HIGHLIGHT', ('login',), 30023, False),
                ('channel_videos:UPLOAD', ('login',), 30024, False), ('channel_clips', ('login',), 30025, False)],
    'search': [('search_streams', ('q',), 30026, False), ('search_channels', ('q',), 30015, True),
               ('search_games', ('q',), 30003, False)],
}
TITLES = {'home': 30001, 'following': 30002, 'categories': 30003}  # pages whose title isn't in the description
SHELF_ERRORS = (http.HTTPError, auth.AuthError, gql.GQLError)


# What a page has
def _split_key(key):
    """'channel_videos:ARCHIVE' -> ('channel_videos', {'type': 'ARCHIVE'})."""
    name, _, video_type = key.partition(':')
    return name, ({'type': video_type} if video_type else {})


def _list_page_spec(desc):
    """The one shelf of a 'list' page (a single list opened on its own)."""
    return [{'list': desc['list'], 'params': desc.get('params') or {}, 'title': desc.get('title') or '',
             'avatars': bool(desc.get('avatars'))}]


def shelf_specs(desc):
    """The shelves a page has: [{'list', 'params', 'title', 'avatars'}], leaving out the ones that need an
    account while signed out."""
    if desc['page'] == 'list':
        return _list_page_spec(desc)
    specs = []
    for key, wanted, title_id, avatars in SHELVES.get(desc['page'], []):
        name, params = _split_key(key)
        if lists.get(name).signed_in and not auth.signed_in():
            continue
        params.update({k: desc[k] for k in wanted})
        specs.append({'list': name, 'params': params, 'title': kodi.string(title_id), 'avatars': avatars})
    return specs


def title_of(desc):
    """The page's title: worded by the add-on for the main pages, else the name it was opened with."""
    if desc['page'] in TITLES:
        return kodi.string(TITLES[desc['page']])
    return desc.get('title') or desc.get('q') or desc.get('login') or desc.get('name') or ''


def empty_message(desc):
    """What a page with nothing on it says: the personal page needs an account."""
    if desc['page'] == 'following' and not auth.signed_in():
        return kodi.string(30017)
    return kodi.string(30027)


# The page's own details (a channel's or a category's)
def _header_query(desc):
    """The query for the page's own details; None for pages that have none."""
    if desc['page'] == 'channel':
        return 'query{user(login:%s){%s}}' % (lists.literal(desc['login']), lists.USER)
    if desc['page'] == 'category':
        return 'query{game(name:%s){%s}}' % (lists.literal(desc['name']), lists.GAME)
    return None


def _read_header(desc, data):
    """The page's own details as an item, from the reply to _header_query; None when Twitch has none."""
    if desc['page'] == 'channel' and data.get('user'):
        return parser.channel(data['user'])
    if desc['page'] == 'category' and data.get('game'):
        return parser.category(data['game'])
    return None


# Fetching
def _fetch_batched(desc, specs):
    """The first batches of the GraphQL shelves, and the page header, in one request:
    ({shelf index: [items, cursor]}, header item or None)."""
    indexes = [i for i, s in enumerate(specs) if lists.get(s['list']).batched]
    queries = [lists.get(specs[i]['list']).query(specs[i]['params']) for i in indexes]
    header_query = _header_query(desc)
    if header_query:
        queries.append(header_query)
    replies = gql.batch([(text, None) for text in queries])
    results = {i: list(lists.get(specs[i]['list']).read(data)) for i, data in zip(indexes, replies)}
    return results, _read_header(desc, replies[-1]) if header_query else None


def _fetch_alone(spec):
    """A shelf fetched on its own (the followed channels, from Helix). If it fails, it is left empty so the
    rest of the page still shows."""
    try:
        return list(lists.get(spec['list']).fetch(spec['params']))
    except SHELF_ERRORS as exc:
        kodi.log('shelf %s failed: %s' % (spec['list'], exc))
        return [[], None]


def _fetch(desc, specs):
    """{'batches': [[items, cursor] per shelf], 'header': item or None}: what Twitch has for the page."""
    if not specs:
        return {'batches': [], 'header': None}
    results, header = _fetch_batched(desc, specs)
    batches = [results[i] if i in results else _fetch_alone(spec) for i, spec in enumerate(specs)]
    return {'batches': batches, 'header': header}


def _cache_key(*parts):
    """A cache key of the active account (pages differ between accounts) and the parts given."""
    return (auth.active_account()[0] or 'guest') + ':' + json.dumps(parts, sort_keys=True)


def _cached_fetch(desc, specs, use_cache):
    """_fetch, from the cache when it was done within PAGE_TTL for the same account and shelves."""
    key = _cache_key('page', desc, [s['list'] for s in specs])
    fetched = kodi.Cache.get(key, PAGE_TTL) if use_cache else None
    if fetched is None:
        fetched = _fetch(desc, specs)
        kodi.Cache.set(key, fetched)
    return fetched


def _filled_shelves(specs, batches):
    """The shelves with their first batch, leaving out the empty ones."""
    shelves = [dict(spec, items=items, cursor=cursor) for spec, (items, cursor) in zip(specs, batches)]
    return [s for s in shelves if s['items']]


def load(desc, use_cache=True):
    """{'title', 'shelves': [{'list', 'params', 'title', 'avatars', 'items', 'cursor'}], 'header', 'message'};
    `message` says why a page is empty, and is '' when it isn't."""
    specs = shelf_specs(desc)
    fetched = _cached_fetch(desc, specs, use_cache)
    shelves = _filled_shelves(specs, fetched['batches'])
    return {'title': title_of(desc), 'shelves': shelves, 'header': fetched['header'],
            'message': '' if shelves else empty_message(desc)}


def _fetch_more(shelf, cursor):
    """The batch after `cursor`; its cursor is None when Twitch hands back the same one (the list has ended)."""
    items, next_cursor = lists.get(shelf['list']).fetch(shelf['params'], after=cursor)
    return items, next_cursor if next_cursor != cursor else None


def more(shelf, cursor):
    """The next batch of a shelf: (items, cursor of the batch after it or None), cached like pages."""
    key = _cache_key('more', shelf['list'], shelf['params'], cursor)
    cached = kodi.Cache.get(key, PAGE_TTL)
    if cached is not None:
        return cached[0], cached[1]
    items, next_cursor = _fetch_more(shelf, cursor)
    kodi.Cache.set(key, [items, next_cursor])
    return items, next_cursor


# Search history, newest first
def _state():
    return kodi.load_json(STATE, {})


def _save_history(history):
    state = _state()
    state['search_history'] = history
    kodi.save_json(STATE, state)


def searches():
    """The past searches, newest first."""
    return _state().get('search_history', [])


def remember_search(query):
    """Put a search at the top of the history (once, whatever its case), keeping SEARCH_HISTORY of them."""
    history = [q for q in searches() if q.lower() != query.lower()]
    _save_history([query] + history[:SEARCH_HISTORY - 1])


def forget_search(query):
    _save_history([q for q in searches() if q != query])


def clear_searches():
    _save_history([])
