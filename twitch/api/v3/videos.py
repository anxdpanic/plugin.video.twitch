# -*- encoding: utf-8 -*-
# https://github.com/justintv/Twitch-API/blob/master/v3_resources/videos.md

from twitch import keys
from twitch.api.parameters import Boolean, Period
from twitch.queries import V3Query as Qry
from twitch.queries import query

from .users import videos


@query
def by_id(identification):
    q = Qry('videos/{id}')
    q.add_urlkw(keys.ID, identification)
    return q


@query
def top(limit=10, offset=0, game=None, period=Period.WEEK):
    q = Qry('videos/top')
    q.add_param(keys.LIMIT, limit, 10)
    q.add_param(keys.OFFSET, offset, 0)
    q.add_param(keys.GAME, game)
    q.add_param(keys.PERIOD, Period.validate(period), Period.WEEK)
    return q


@query
def by_channel(name, limit=10, offset=0,
               broadcasts=Boolean.FALSE, hls=Boolean.FALSE):
    q = Qry('channels/{channel}/videos')
    q.add_urlkw(keys.CHANNEL, name)
    q.add_param(keys.LIMIT, limit, 10)
    q.add_param(keys.OFFSET, offset, 0)
    q.add_param(keys.BROADCASTS, Boolean.validate(broadcasts), Boolean.FALSE)
    q.add_param(keys.HLS, Boolean.validate(hls), Boolean.FALSE)
    return q


# Needs Auth
def followed(*args, **kwargs):
    videos(*args, **kwargs)
