# -*- encoding: utf-8 -*-
# https://github.com/justintv/Twitch-API/blob/master/v3_resources/channels.md

from twitch import keys
from twitch.queries import V3Query as Qry
from twitch.queries import query

from .videos import by_channel


@query
def by_name(name):
    q = Qry('channels/{channel}')
    q.add_urlkw(keys.CHANNEL, name)
    return q


@query
def channel():
    raise NotImplementedError


def get_videos(name, **kwargs):
    return by_channel(name, **kwargs)


@query
def editors(name):
    raise NotImplementedError


# TODO needs authentification and put requests
@query
def update(name, status=None, game=None, delay=0):
    raise NotImplementedError


# TODO needs auth
@query
def delete(name):
    raise NotImplementedError


# TODO needs auth, needs POST request
@query
def commercial(name, length=30):
    raise NotImplementedError


@query
def teams(name):
    q = Qry('channels/{channel}/teams')
    q.add_urlkw('channel', name)
    return q
