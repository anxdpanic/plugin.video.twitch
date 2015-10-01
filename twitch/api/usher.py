# -*- encoding: utf-8 -*-

from twitch.logging import log                                          # NOQA
log.warning('By using this module you are violating the Twitch TOS')    # NOQA

from twitch import keys
from twitch.api.parameters import Boolean
from twitch.parser import m3u8
from twitch.queries import HiddenApiQuery, UsherQuery
from twitch.queries import query


@query
def channel_token(channel):
    q = HiddenApiQuery('channels/{channel}/access_token')
    q.add_urlkw(keys.CHANNEL, channel)
    return q


@query
def vod_token(id):
    q = HiddenApiQuery('vods/{vod}/access_token')
    q.add_urlkw(keys.VOD, id)
    return q


@query
def _legacy_video(id):
    q = HiddenApiQuery('videos/{id}')
    q.add_urlkw(keys.ID, id)
    return q


@m3u8
@query
def live(channel):
    token = channel_token(channel)

    q = UsherQuery('api/channel/hls/{channel}.m3u8')
    q.add_urlkw(keys.CHANNEL, channel)
    q.add_param(keys.SIG, token[keys.SIG])
    q.add_param(keys.TOKEN, token[keys.TOKEN])
    q.add_param(keys.ALLOW_SOURCE, Boolean.FALSE)
    return q


@m3u8
@query
def _vod(id):
    id = id[1:]

    token = vod_token(id)

    q = UsherQuery('vod/{id}')
    q.add_urlkw(keys.ID, id)
    q.add_param(keys.NAUTHSIG, token[keys.SIG])
    q.add_param(keys.NAUTH, token[keys.TOKEN])
    return q


def video(id):
    if id.startswith('v'):
        return _vod(id)
    elif id.startswith(('a', 'c')):
        return _legacy_video(id)
    else:
        raise NotImplementedError('Unknown Video Type')
