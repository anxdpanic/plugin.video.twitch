# -*- encoding: utf-8 -*-
# https://github.com/justintv/Twitch-API/blob/master/v3_resources/subscriptions.md

from twitch.api.parameters import Direction
from twitch.queries import query


# Needs Authentification
@query
def by_channel(channel, limit=25, offset=0, direction=Direction.ASC):
    raise NotImplementedError


# Needs Authentification
@query
def channel_to_user(channel, user):
    raise NotImplementedError


# Needs Authentification
@query
def user_to_channel(user, channel):
    raise NotImplementedError
