# -*- encoding: utf-8 -*-
# https://github.com/justintv/Twitch-API/blob/master/v3_resources/ingests.md

from twitch.queries import V3Query as Qry
from twitch.queries import query


@query
def get():
    q = Qry('ingests')
    return q
