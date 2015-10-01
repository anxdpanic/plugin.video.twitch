# -*- encoding: utf-8 -*-
# https://github.com/justintv/Twitch-API/blob/master/v3_resources/users.md

from twitch import keys
from twitch.queries import V3Query as Qry
from twitch.queries import query


@query
def by_name(name):
    q = Qry('users/{user}')
    q.add_urlkw(keys.USER, name)
    return q


# Needs Authentification
@query
def user():
    raise NotImplementedError


# Needs Authentification
@query
def streams():
    raise NotImplementedError


# Needs Authentification
@query
def videos():
    raise NotImplementedError
