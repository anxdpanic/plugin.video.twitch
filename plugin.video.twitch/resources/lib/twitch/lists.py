# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""The lists the add-on shows (top streams, a category's clips, a channel's past broadcasts, ...): the query
for one batch of each, and how to read its items and the cursor for the next batch.

Arguments go into the query text as JSON literals rather than variables, so no query has to name Twitch's
argument types."""
import json

from . import gql, helix, parser

STREAM = ('id title viewersCount createdAt previewImageURL(width:1280,height:720) game{name displayName} '
          'broadcaster{login displayName profileImageURL(width:300)}')
USER_STREAM = 'id title viewersCount createdAt previewImageURL(width:1280,height:720) game{name displayName}'
VIDEO = ('id title lengthSeconds viewCount publishedAt broadcastType previewThumbnailURL(width:1280,height:720) '
         'game{name displayName} owner{login displayName profileImageURL(width:300)}')
CLIP = ('id slug title viewCount createdAt durationSeconds thumbnailURL(width:480,height:272) game{name displayName} '
        'broadcaster{login displayName profileImageURL(width:300)}')
USER = ('id login displayName description profileImageURL(width:300) offlineImageURL bannerImageURL '
        'followers{totalCount} stream{viewersCount game{displayName}}')
GAME = 'id name displayName viewersCount boxArtURL(width:285,height:380) tags(tagType:CONTENT){localizedName}'

PAGE_SIZE = 24
VIDEO_TYPES = ('ARCHIVE', 'HIGHLIGHT', 'UPLOAD')


def literal(value):
    """A value as a GraphQL literal: JSON's strings and numbers are valid GraphQL."""
    return json.dumps(value)


def _args(first, after, *extra):
    parts = ['first:%d' % first] + list(extra)
    if after:
        parts.append('after:%s' % literal(after))
    return ','.join(parts)


def _connection(fields):
    return '{edges{cursor node{%s}} pageInfo{hasNextPage}}' % fields


class List:
    """One kind of list, read with GraphQL. `build(params, args)` is the query text; `path` leads from the
    reply's data to the connection; `parse` turns a node into an item."""

    batched = True  # its first batch can share a request with other lists' (see pages)

    def __init__(self, build, path, parse, signed_in=False):
        self.build = build
        self.path = path
        self.parse = parse
        self.signed_in = signed_in

    def query(self, params, first=PAGE_SIZE, after=None):
        return self.build(params, _args(first, after))

    def fetch(self, params, after=None):
        return self.read(gql.query(self.query(params, after=after)))

    def read(self, data):
        """(items, cursor of the next batch or None) from the reply's data."""
        node = data
        for key in self.path:
            node = (node or {}).get(key)
        node = node or {}
        if 'edges' not in node:  # a plain list of nodes, without paging
            return [self.parse(n) for n in node.get('nodes') or [] if n], None
        edges = [e for e in node.get('edges') or [] if e and e.get('node')]
        items = [self.parse(e['node']) for e in edges]
        more = (node.get('pageInfo') or {}).get('hasNextPage') and edges and edges[-1].get('cursor')
        return items, more or None


class FollowedList:
    """A list of followed channels from Helix (logins), with their details from GraphQL, in Helix's order."""

    batched = False
    signed_in = True

    def __init__(self, path, fields, parse, live_only=False, first=PAGE_SIZE):
        self.path = path
        self.fields = fields
        self.parse = parse
        self.live_only = live_only
        self.first = first

    def _details(self, logins):
        if not logins:
            return []
        data = gql.query('query{users(logins:%s){%s}}' % (literal(logins), self.fields))
        users = {u['login']: u for u in data.get('users') or [] if u}
        found = [users[login] for login in logins if login in users]
        return [u for u in found if u.get('stream')] if self.live_only else found

    def fetch(self, params, after=None):
        logins, cursor = helix.page(self.path, 'user_login' if self.live_only else 'broadcaster_login',
                                    self.first, after)
        return [self.parse(u) for u in self._details(logins)], cursor


def _user(login, field):
    return 'query{user(login:%s){%s}}' % (literal(login), field)


def _game(name, field):
    return 'query{game(name:%s){%s}}' % (literal(name), field)


LISTS = {
    'top_streams': List(lambda p, a: 'query{streams(%s)%s}' % (a, _connection(STREAM)),
                        ('streams',), parser.live),
    'top_games': List(lambda p, a: 'query{games(%s)%s}' % (a, _connection(GAME)), ('games',), parser.category),
    'game_streams': List(lambda p, a: _game(p['name'], 'streams(%s,options:{sort:VIEWER_COUNT})%s'
                                         % (a, _connection(STREAM))), ('game', 'streams'), parser.live),
    'game_clips': List(lambda p, a: _game(p['name'], 'clips(%s,criteria:{period:LAST_WEEK})%s'
                                       % (a, _connection(CLIP))), ('game', 'clips'), parser.clip),
    'game_videos': List(lambda p, a: _game(p['name'], 'videos(%s,sort:VIEWS)%s' % (a, _connection(VIDEO))),
                        ('game', 'videos'), parser.video),
    'channel_live': List(lambda p, a: _user(p['login'], 'login displayName profileImageURL(width:300) stream{%s}'
                                         % USER_STREAM), ('user',), None),
    'channel_videos': List(lambda p, a: _user(p['login'], 'videos(%s,sort:TIME,type:%s)%s'
                                           % (a, p['type'], _connection(VIDEO))), ('user', 'videos'), parser.video),
    'channel_clips': List(lambda p, a: _user(p['login'], 'clips(%s,criteria:{period:ALL_TIME,sort:VIEWS_DESC})%s'
                                          % (a, _connection(CLIP))), ('user', 'clips'), parser.clip),
    'followed_live': FollowedList('streams/followed', 'login displayName profileImageURL(width:300) stream{%s}'
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


def _channel_live_read(data):
    """A channel's own stream, as a one-item list while it is live."""
    user = data.get('user') or {}
    return ([parser.live_user(user)] if user.get('stream') else []), None


LISTS['channel_live'].read = _channel_live_read


def get(key):
    return LISTS[key]
