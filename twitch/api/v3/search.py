# -*- encoding: utf-8 -*-
# https://github.com/justintv/Twitch-API/blob/master/v3_resources/search.md

from twitch import keys
from twitch.api.parameters import Boolean
from twitch.queries import V3Query as Qry
from twitch.queries import query


@query
def channels(query, limit=25, offset=0):
    q = Qry('search/channels')
    q.add_param(keys.QUERY, query)
    q.add_param(keys.LIMIT, limit, 25)
    q.add_param(keys.OFFSET, offset, 0)
    return q


@query
def streams(query, limit=25, offset=0, hls=Boolean.FALSE):
    q = Qry('search/streams')
    q.add_param(keys.QUERY, query)
    q.add_param(keys.LIMIT, limit, 25)
    q.add_param(keys.OFFSET, offset, 0)
    q.add_param(keys.HLS, hls, Boolean.FALSE)
    return q


# 'type' can currently only be suggest, so it is hardcoded
@query
def games(query, live=Boolean.FALSE):
    q = Qry('search/games')
    q.add_param(keys.QUERY, query)
    q.add_param(keys.TYPE, 'suggest')
    q.add_param(keys.LIVE, live, Boolean.FALSE)
    return q
