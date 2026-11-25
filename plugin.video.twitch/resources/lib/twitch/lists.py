# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""The lists the add-on shows (top streams, a category's clips, a channel's past broadcasts, ...): the query
for one batch of each, and how to read its items and the cursor for the next batch.

Every kind of list has fetch(params, after) -> (items, cursor or None). GraphQL lists (List) also give their
query text on its own, so a page can send the first batches of all its lists in one request.

Arguments go into the query text as JSON literals rather than variables, so no query has to name Twitch's
argument types."""
import json
import time

from . import describe, gql, helix, parser

# Fields asked for each kind of node. Pictures come at full HD for fanart; the tiles use a smaller copy of
# the same address (see parser).
USER_STREAM = ('id title viewersCount createdAt language isMature freeformTags{name} '
               'previewImageURL(width:1920,height:1080) game{name displayName}')
STREAM = USER_STREAM + ' broadcaster{login displayName profileImageURL(width:600)}'
VIDEO = ('id title lengthSeconds viewCount publishedAt broadcastType previewThumbnailURL(width:1920,height:1080) '
         'game{name displayName} owner{login displayName profileImageURL(width:600)}')
CLIP = ('id slug title viewCount createdAt durationSeconds thumbnailURL(width:1920,height:1080) '
        'game{name displayName} broadcaster{login displayName profileImageURL(width:600)}')
USER = ('id login displayName description profileImageURL(width:600) offlineImageURL bannerImageURL '
        'followers{totalCount} stream{viewersCount game{displayName}}')
GAME = 'id name displayName viewersCount boxArtURL(width:570,height:760) tags(tagType:CONTENT){localizedName}'
SCHEDULE = ('login displayName profileImageURL(width:600) offlineImageURL channel{schedule{segments{id title startAt '
            'endAt isCancelled categories{name displayName boxArtURL(width:570,height:760)}}}}')

PAGE_SIZE = 24
SCHEDULE_SIZE = 12  # coming streams shown on a channel's page


def literal(value):
    """A value as a GraphQL literal: JSON's strings, numbers and lists are valid GraphQL."""
    return json.dumps(value)


def _args(first, after):
    """'first:24,after:"cursor"': the paging arguments of a connection."""
    return 'first:%d' % first + (',after:%s' % literal(after) if after else '')


def _connection(fields):
    """The selection of a paged connection: its nodes' fields, cursors and whether there is more."""
    return '{edges{cursor node{%s}} pageInfo{hasNextPage}}' % fields


def _dig(data, path):
    """What `path` (a tuple of keys) leads to in the reply's data; {} where something on the way is null."""
    node = data
    for key in path:
        node = (node or {}).get(key)
    return node or {}


def _page_of(connection, parse):
    """(items, cursor of the next batch or None) of a paged connection."""
    edges = [e for e in connection.get('edges') or [] if e and e.get('node')]
    items = [parse(e['node']) for e in edges]
    more = (connection.get('pageInfo') or {}).get('hasNextPage') and edges and edges[-1].get('cursor')
    return items, more or None


class List:
    """One kind of list, read with GraphQL. `build(params, args)` is the query text; `path` leads from the
    reply's data to the connection; `parse` turns a node into an item. `read` can be given instead, for a
    reply that isn't a connection (a channel's own stream, its schedule)."""

    batched = True  # its first batch can share a request with other lists' (see pages)

    def __init__(self, build, path=(), parse=None, signed_in=False, read=None):
        self.build = build
        self.path = path
        self.parse = parse
        self.signed_in = signed_in  # only shown while signed in
        if read:
            self.read = read

    def query(self, params, first=PAGE_SIZE, after=None):
        return self.build(params, _args(first, after))

    def fetch(self, params, after=None):
        return self.read(gql.query(self.query(params, after=after)))

    def read(self, data):
        """(items, cursor of the next batch or None) from the reply's data."""
        node = _dig(data, self.path)
        if 'edges' not in node:  # a plain list of nodes, without paging
            return [self.parse(n) for n in node.get('nodes') or [] if n], None
        return _page_of(node, self.parse)


class FollowedList:
    """A list of followed channels: logins from Helix, details from GraphQL, in Helix's order. `live_only`
    keeps the channels that are live (Helix's live list can name a stream that has just ended)."""

    batched = False  # Helix can't share a GraphQL request
    signed_in = True

    def __init__(self, path, fields, parse, live_only=False, first=PAGE_SIZE):
        self.path = path
        self.fields = fields
        self.parse = parse
        self.live_only = live_only
        self.first = first

    def _users(self, logins):
        """The GraphQL user nodes of these logins, in the same order; logins Twitch doesn't know are skipped."""
        if not logins:
            return []
        data = gql.query('query{users(logins:%s){%s}}' % (literal(logins), self.fields))
        users = {u['login']: u for u in data.get('users') or [] if u}
        return [users[login] for login in logins if login in users]

    def fetch(self, params, after=None):
        field = 'user_login' if self.live_only else 'broadcaster_login'
        logins, cursor = helix.page(self.path, field, self.first, after)
        users = self._users(logins)
        if self.live_only:
            users = [u for u in users if u.get('stream')]
        return [self.parse(u) for u in users], cursor


# Query builders
def _user(login, fields):
    return 'query{user(login:%s){%s}}' % (literal(login), fields)


def _game(name, fields):
    return 'query{game(name:%s){%s}}' % (literal(name), fields)


# Readers for replies that aren't a connection
def _read_channel_live(data):
    """A channel's own stream, as a one-item list while it is live."""
    user = data.get('user') or {}
    return ([parser.live_user(user)] if user.get('stream') else []), None


def _segments(data):
    return (((data.get('user') or {}).get('channel') or {}).get('schedule') or {}).get('segments') or []


def _coming(segments, now):
    """The segments not cancelled and not over yet (Twitch's schedule also holds the past week's), soonest
    first."""
    coming = [s for s in segments if not s.get('isCancelled')
              and describe.timestamp(s.get('endAt') or s.get('startAt')) > now]
    return sorted(coming, key=lambda s: s.get('startAt') or '')


def _read_schedule(data, now=None):
    """A channel's coming streams, up to SCHEDULE_SIZE of them."""
    user = data.get('user') or {}
    coming = _coming(_segments(data), now or time.time())
    return [parser.scheduled(s, user) for s in coming[:SCHEDULE_SIZE]], None


LISTS = {
    'top_streams': List(lambda p, a: 'query{streams(%s)%s}' % (a, _connection(STREAM)), ('streams',), parser.live),
    'top_games': List(lambda p, a: 'query{games(%s)%s}' % (a, _connection(GAME)), ('games',), parser.category),
    'game_streams': List(lambda p, a: _game(p['name'], 'streams(%s,options:{sort:VIEWER_COUNT})%s'
                                         % (a, _connection(STREAM))), ('game', 'streams'), parser.live),
    'game_clips': List(lambda p, a: _game(p['name'], 'clips(%s,criteria:{period:LAST_WEEK})%s'
                                       % (a, _connection(CLIP))), ('game', 'clips'), parser.clip),
    'game_videos': List(lambda p, a: _game(p['name'], 'videos(%s,sort:VIEWS)%s' % (a, _connection(VIDEO))),
                        ('game', 'videos'), parser.video),
    'channel_live': List(lambda p, a: _user(p['login'], 'login displayName profileImageURL(width:600) stream{%s}'
                                         % USER_STREAM), read=_read_channel_live),
    'channel_schedule': List(lambda p, a: _user(p['login'], SCHEDULE), read=_read_schedule),
    'channel_videos': List(lambda p, a: _user(p['login'], 'videos(%s,sort:TIME,type:%s)%s'
                                           % (a, p['type'], _connection(VIDEO))), ('user', 'videos'), parser.video),
    'channel_clips': List(lambda p, a: _user(p['login'], 'clips(%s,criteria:{period:ALL_TIME,sort:VIEWS_DESC})%s'
                                          % (a, _connection(CLIP))), ('user', 'clips'), parser.clip),
    'followed_live': FollowedList('streams/followed', 'login displayName profileImageURL(width:600) stream{%s}'
                                  % USER_STREAM, parser.live_user, live_only=True, first=100),
    'follows': FollowedList('channels/followed', USER, parser.channel),
    'followed_games': List(lambda p, a: 'query{currentUser{followedGames(first:100,type:ALL){nodes{%s}}}}' % GAME,
                           ('currentUser', 'followedGames'), parser.category, signed_in=True),
    'search_streams': List(lambda p, a: 'query{searchStreams(userQuery:%s,%s)%s}'
                           % (literal(p['q']), a, _connection(STREAM)), ('searchStreams',), parser.live),
    'search_channels': List(lambda p, a: 'query{searchUsers(userQuery:%s,%s)%s}'
                            % (literal(p['q']), a, _connection(USER)), ('searchUsers',), parser.channel),
    'search_games': List(lambda p, a: 'query{searchCategories(query:%s,%s)%s}'
                         % (literal(p['q']), a, _connection(GAME)), ('searchCategories',), parser.category),
}


def get(key):
    return LISTS[key]
