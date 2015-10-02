# -*- encoding: utf-8 -*-
# https://github.com/justintv/Twitch-API/blob/master/v3_resources/streams.md

from twitch import keys
from twitch.queries import V3Query as Qry
from twitch.queries import query


@query
def by_channel(name):
    q = Qry('streams/{channel}')
    q.add_urlkw(keys.CHANNEL, name)
    return q


@query
def all(game=None, channel=None, limit=25, offset=0, client_id=None):
    q = Qry('streams')
    q.add_param(keys.GAME, game)
    q.add_param(keys.CHANNEL, channel)
    q.add_param(keys.LIMIT, limit, 25)
    q.add_param(keys.OFFSET, offset, 0)
    q.add_param(keys.CLIENT_ID, client_id)
    return q


@query
def featured(limit=25, offset=0):
    q = Qry('streams/featured')
    q.add_param(keys.LIMIT, limit, 25)
    q.add_param(keys.OFFSET, offset, 0)
    return q


@query
def summary(game=None):
    q = Qry('streams/summary')
    q.add_param(keys.GAME, game)
    return q


@query
def followed():
    raise NotImplementedError
