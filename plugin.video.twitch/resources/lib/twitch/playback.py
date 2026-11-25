# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""Stream addresses: a playback token from the GraphQL API, then Twitch's HLS playlist (usher) for live
streams and past broadcasts, or a clip's own MP4 file."""
import random
import urllib.parse

from . import gql, http, kodi, lists

USHER_LIVE = 'https://usher.ttvnw.net/api/channel/hls/%s.m3u8'
USHER_VIDEO = 'https://usher.ttvnw.net/vod/%s.m3u8'
TOKEN_PARAMS = '{platform:"android",playerBackend:"mediaplayer",playerType:"site"}'
HLS_MIME = 'application/vnd.apple.mpegurl'
# codecs setting -> what the playlist may offer, best first
CODECS = {0: 'h264', 1: 'h265,h264', 2: 'av1,h265,h264'}


class PlaybackError(Exception):
    """Twitch won't play this: offline, deleted, sub-only or blocked in the region."""


def _token(field, argument, value):
    data = gql.query('query{%s(%s:%s,params:%s){value signature}}'
                     % (field, argument, lists.literal(value), TOKEN_PARAMS))
    token = data.get(field)
    if not token or not token.get('value'):
        raise PlaybackError(field)
    return token


def _usher_query(token):
    return urllib.parse.urlencode({
        # No audio-only rendition: InputStream Adaptive could drop to it on a slow link and show no picture.
        'sig': token['signature'], 'token': token['value'], 'allow_source': 'true', 'allow_audio_only': 'false',
        'fast_bread': 'true', 'p': random.randint(0, 9999999), 'player_backend': 'mediaplayer',
        'playlist_include_framerate': 'true', 'supported_codecs': CODECS.get(kodi.setting_int('codecs'), 'h264'),
    })


def _checked(url, not_found=None):
    """The playlist address, once Twitch has answered it: an offline channel, a sub-only broadcast or a
    region block shows up here as an error rather than as a player that never starts. `not_found` is what to
    say for a 404 instead of Twitch's own words."""
    try:
        http.request(url, timeout=15)
    except http.HTTPError as exc:
        if exc.status == 404 and not_found:
            raise PlaybackError(not_found) from exc
        reply = exc.json()
        message = reply[0].get('error') if isinstance(reply, list) and reply and isinstance(reply[0], dict) else ''
        raise PlaybackError(message or 'HTTP %s' % exc.status) from exc
    return url


def live_url(login):
    token = _token('streamPlaybackAccessToken', 'channelName', login)
    # Twitch answers an offline channel with 404 and "Can not find channel".
    return _checked(USHER_LIVE % urllib.parse.quote(login.lower()) + '?' + _usher_query(token),
                    not_found=kodi.string(30071))


def video_url(video_id):
    token = _token('videoPlaybackAccessToken', 'id', video_id)
    return _checked(USHER_VIDEO % urllib.parse.quote(video_id) + '?' + _usher_query(token))


def recording_id(login):
    """The past broadcast a live stream is being recorded into, to play it from the start."""
    data = gql.query('query{user(login:%s){stream{id} videos(first:1,type:ARCHIVE,sort:TIME){edges{node{id status}}}}}'
                     % lists.literal(login))
    user = data.get('user') or {}
    edges = ((user.get('videos') or {}).get('edges')) or []
    video = edges[0]['node'] if edges else {}
    if not user.get('stream') or video.get('status') != 'RECORDING':
        raise PlaybackError(kodi.string(30102))
    return video['id']


def _best_quality(qualities):
    """The clip file to play: the highest resolution, the higher frame rate at the same resolution."""
    def rank(q):
        try:
            return int(q.get('quality') or 0), float(q.get('frameRate') or 0)
        except ValueError:
            return 0, 0
    return max(qualities, key=rank)


def clip_url(slug):
    data = gql.query('query{clip(slug:%s){videoQualities{quality frameRate sourceURL} '
                     'playbackAccessToken(params:%s){value signature}}}' % (lists.literal(slug), TOKEN_PARAMS))
    clip = data.get('clip') or {}
    qualities = [q for q in clip.get('videoQualities') or [] if q.get('sourceURL')]
    token = clip.get('playbackAccessToken') or {}
    if not qualities or not token.get('value'):
        raise PlaybackError('clip')
    source = _best_quality(qualities)['sourceURL']
    return source + ('&' if '?' in source else '?') + urllib.parse.urlencode(
        {'sig': token['signature'], 'token': token['value']})
