# -*- encoding: utf-8 -*-
# https://github.com/justintv/Twitch-API/blob/master/v3_resources/root.md

from twitch.queries import V3Query as Qry
from twitch.queries import query


# TODO token as parameter
@query
def root():
    return Qry('')
