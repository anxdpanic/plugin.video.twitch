# -*- encoding: utf-8 -*-
# https://github.com/justintv/Twitch-API/blob/master/v3_resources/teams.md

from twitch import keys
from twitch.queries import V3Query as Qry
from twitch.queries import query


@query
def active(limit=25, offset=0):
    q = Qry('teams')
    q.add_param(keys.LIMIT, limit, 25)
    q.add_param(keys.OFFSET, offset, 0)
    return q


@query
def by_name(name):
    q = Qry('teams/{team}')
    q.add_urlkw(keys.TEAM, name)
    return q
