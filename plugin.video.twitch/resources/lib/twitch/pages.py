# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""The add-on's pages as shelves (rows of items), shared by the plugin listings and the TV interface.

A page is described by a dict, {'page': 'home'} or {'page': 'channel', 'login': ...}, so it can travel in a
plugin URL. Loading it runs the first batch of every shelf in one request."""
import json

from . import auth, gql, kodi, lists, parser

PAGE_TTL = 120  # seconds: back to a listing within this time shows it as it was

# page -> [(list key, params from the page's description, title string id, round pictures)]
SHELVES = {
    'home': [('followed_live', (), 30010, False), ('top_streams', (), 30011, False), ('top_games', (), 30012, False)],
    'following': [('followed_live', (), 30013, False), ('follows', (), 30015, True),
                  ('followed_games', (), 30016, False)],
    'categories': [('top_games', (), 30012, False)],
    'category': [('game_streams', ('name',), 30018, False), ('game_clips', ('name',), 30019, False),
                 ('game_videos', ('name',), 30020, False)],
    'channel': [('channel_live', ('login',), 30021, False), ('channel_videos:ARCHIVE', ('login',), 30022, False),
                ('channel_videos:HIGHLIGHT', ('login',), 30023, False),
                ('channel_videos:UPLOAD', ('login',), 30024, False), ('channel_clips', ('login',), 30025, False)],
    'search': [('search_streams', ('q',), 30026, False), ('search_channels', ('q',), 30015, True),
               ('search_games', ('q',), 30003, False)],
}
TITLES = {'home': 30001, 'following': 30002, 'categories': 30003}


def _split_key(key):
    """'channel_videos:ARCHIVE' -> ('channel_videos', {'type': 'ARCHIVE'})."""
    name, _, video_type = key.partition(':')
    return name, ({'type': video_type} if video_type else {})


def shelf_specs(desc):
    """The shelves a page has: [{'list', 'params', 'title', 'avatars'}], leaving out the ones that need an
    account while signed out."""
    if desc['page'] == 'list':
        return [{'list': desc['list'], 'params': desc.get('params') or {}, 'title': desc.get('title') or '',
                 'avatars': bool(desc.get('avatars'))}]
    specs = []
    for key, wanted, title_id, avatars in SHELVES.get(desc['page'], []):
        name, params = _split_key(key)
        if lists.get(name).signed_in and not auth.signed_in():
            continue
        params.update({k: desc[k] for k in wanted})
        specs.append({'list': name, 'params': params, 'title': kodi.string(title_id), 'avatars': avatars})
    return specs


def _header_query(desc):
    """The query for a page's own details (a channel's or category's), and how to read it; None for others."""
    if desc['page'] == 'channel':
        return 'query{user(login:%s){%s}}' % (lists.literal(desc['login']), lists.USER), \
            lambda data: parser.channel(data['user']) if data.get('user') else None
    if desc['page'] == 'category':
        return 'query{game(name:%s){%s}}' % (lists.literal(desc['name']), lists.GAME), \
            lambda data: parser.category(data['game']) if data.get('game') else None
    return None


def title_of(desc):
    if desc['page'] in TITLES:
        return kodi.string(TITLES[desc['page']])
    return desc.get('title') or desc.get('q') or desc.get('login') or desc.get('name') or ''


def empty_message(desc):
    """What a page with nothing on it says: the personal page needs an account."""
    if desc['page'] == 'following' and not auth.signed_in():
        return kodi.string(30017)
    return kodi.string(30027)


def _cache_key(*parts):
    return (auth.active_account()[0] or 'guest') + ':' + json.dumps(parts, sort_keys=True)


def _fetch_batched(specs, header):
    """The first batches of the GraphQL shelves, and the page header, in one request:
    ({shelf index: (items, cursor)}, header item or None)."""
    indexes = [i for i, s in enumerate(specs) if lists.get(s['list']).batched]
    queries = [lists.get(specs[i]['list']).query(specs[i]['params']) for i in indexes]
    if header:
        queries.append(header[0])
    replies = gql.batch([(text, None) for text in queries])
    results = {i: lists.get(specs[i]['list']).read(data) for i, data in zip(indexes, replies)}
    return results, header[1](replies[-1]) if header else None


def _fetch(desc, specs):
    """Every shelf's first batch, and the page header."""
    results, header = _fetch_batched(specs, _header_query(desc))
    batches = [list(results[i]) if i in results else list(lists.get(s['list']).fetch(s['params']))
               for i, s in enumerate(specs)]
    return {'batches': batches, 'header': header}


def load(desc, use_cache=True):
    """{'title', 'shelves': [{'list', 'params', 'title', 'avatars', 'items', 'cursor'}], 'header', 'message'};
    shelves with nothing in them are left out. Only what Twitch said is cached: the titles are worded afresh."""
    specs = shelf_specs(desc)
    key = _cache_key('page', desc, [s['list'] for s in specs])
    page = kodi.Cache.get(key, PAGE_TTL) if use_cache else None
    if page is None:
        page = _fetch(desc, specs) if specs else {'batches': [], 'header': None}
        kodi.Cache.set(key, page)
    shelves = [dict(spec, items=items, cursor=cursor) for spec, (items, cursor) in zip(specs, page['batches'])]
    shelves = [s for s in shelves if s['items']]
    return {'title': title_of(desc), 'shelves': shelves, 'header': page['header'],
            'message': '' if shelves else empty_message(desc)}


def more(shelf, cursor):
    """The next batch of a shelf: (items, cursor of the batch after it or None)."""
    key = _cache_key('more', shelf['list'], shelf['params'], cursor)
    cached = kodi.Cache.get(key, PAGE_TTL)
    if cached is not None:
        return cached[0], cached[1]
    items, next_cursor = lists.get(shelf['list']).fetch(shelf['params'], after=cursor)
    kodi.Cache.set(key, [items, next_cursor])
    return items, next_cursor if next_cursor != cursor else None


# Search history, newest first.
def _state():
    return kodi.load_json('state.json', {})


def searches():
    return _state().get('search_history', [])


def remember_search(query):
    state = _state()
    history = [q for q in state.get('search_history', []) if q.lower() != query.lower()]
    state['search_history'] = [query] + history[:19]
    kodi.save_json('state.json', state)


def forget_search(query):
    state = _state()
    state['search_history'] = [q for q in state.get('search_history', []) if q != query]
    kodi.save_json('state.json', state)


def clear_searches():
    state = _state()
    state['search_history'] = []
    kodi.save_json('state.json', state)
