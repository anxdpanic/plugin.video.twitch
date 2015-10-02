# -*- encoding: utf-8 -*-
# https://github.com/justintv/Twitch-API/blob/master/v3_resources/chat.md

from twitch import keys
from twitch.queries import V3Query as Qry
from twitch.queries import query


@query
def by_channel(name):
    q = Qry('chat/{channel}')
    q.add_urlkw(keys.CHANNEL, name)
    return q


@query
def badges(name):
    q = Qry('chat/{channel}/badges')
    q.add_urlkw(keys.CHANNEL, name)
    return q


@query
def emoticons():
    q = Qry('chat/emoticons')
    return q
