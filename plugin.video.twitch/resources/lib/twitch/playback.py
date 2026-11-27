# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""Stream addresses: a playback token from the GraphQL API, then Twitch's HLS playlist (usher) for live
streams and past broadcasts, or a clip's own MP4 file.

The token is asked for as the Android player, and signed in when there is an account, so the account's
Turbo or subscriber benefits (no ads, sub-only broadcasts) come with it."""
import random
import urllib.parse

from . import gql, http, kodi, lists

USHER_LIVE = 'https://usher.ttvnw.net/api/channel/hls/%s.m3u8'
USHER_VIDEO = 'https://usher.ttvnw.net/vod/%s.m3u8'
TOKEN_PARAMS = '{platform:"android",playerBackend:"mediaplayer",playerType:"site"}'
CODECS = {0: 'h264', 1: 'h265,h264', 2: 'av1,h265,h264'}  # codecs setting -> what the playlist may offer
CHECK_TIMEOUT = 15  # seconds to wait for the playlist when checking it


class PlaybackError(Exception):
    """Twitch won't play this: offline, deleted, sub-only or blocked in the region."""


# Live streams and past broadcasts
def _token(field, argument, value):
    """A playback token ({'value', 'signature'}) from GraphQL's `field`; PlaybackError when Twitch gives none."""
    data = gql.query('query{%s(%s:%s,params:%s){value signature}}'
                     % (field, argument, lists.literal(value), TOKEN_PARAMS))
    token = data.get(field)
    if not token or not token.get('value'):
        raise PlaybackError(field)
    return token


def _usher_query(token):
    """The playlist's query: the signed token, every rendition up to the source, and the codecs allowed."""
    return urllib.parse.urlencode({
        'sig': token['signature'], 'token': token['value'], 'allow_source': 'true',
        # No audio-only rendition: InputStream Adaptive could drop to it on a slow link and show no picture.
        'allow_audio_only': 'false',
        'fast_bread': 'true',  # low-latency segments
        'p': random.randint(0, 9999999),  # a different address each time, as Twitch's players send
        'player_backend': 'mediaplayer', 'playlist_include_framerate': 'true',
        'supported_codecs': CODECS.get(kodi.setting_int('codecs'), 'h264'),
    })


def _refusal(exc):
    """Twitch's reason for refusing a playlist ('Content is restricted to subscribers'), or the status."""
    reply = exc.json()
    first = reply[0] if isinstance(reply, list) and reply and isinstance(reply[0], dict) else {}
    return first.get('error') or 'HTTP %s' % exc.status


def _checked(url, not_found=None):
    """The playlist address, once Twitch has answered it: an offline channel, a sub-only broadcast or a
    region block shows up here as an error rather than as a player that never starts. `not_found` is what to
    say for a 404 instead of Twitch's own words."""
    try:
        http.request(url, timeout=CHECK_TIMEOUT)
    except http.HTTPError as exc:
        if exc.status == 404 and not_found:
            raise PlaybackError(not_found) from exc
        raise PlaybackError(_refusal(exc)) from exc
    return url


def live_url(login):
    """The HLS playlist of a channel's live stream."""
    token = _token('streamPlaybackAccessToken', 'channelName', login)
    # Twitch answers an offline channel with 404 and "Can not find channel".
    return _checked(USHER_LIVE % urllib.parse.quote(login.lower()) + '?' + _usher_query(token),
                    not_found=kodi.string(30071))


def video_url(video_id):
    """The HLS playlist of a past broadcast, highlight or upload (or of a broadcast still being recorded)."""
    token = _token('videoPlaybackAccessToken', 'id', video_id)
    return _checked(USHER_VIDEO % urllib.parse.quote(video_id) + '?' + _usher_query(token))


def _latest_archive(login):
    """(whether the channel is live, its newest past broadcast {'id', 'status'} or {})."""
    data = gql.query('query{user(login:%s){stream{id} videos(first:1,type:ARCHIVE,sort:TIME){edges{node{id status}}}}}'
                     % lists.literal(login))
    user = data.get('user') or {}
    edges = (user.get('videos') or {}).get('edges') or []
    return bool(user.get('stream')), edges[0]['node'] if edges else {}


def recording_id(login):
    """The past broadcast a live stream is being recorded into, to play it from the start."""
    live, video = _latest_archive(login)
    if not live or video.get('status') != 'RECORDING':
        raise PlaybackError(kodi.string(30102))
    return video['id']


# Clips
def _rank(quality):
    """How good a clip file is: (height, frame rate); (0, 0) for one that doesn't say."""
    try:
        return int(quality.get('quality') or 0), float(quality.get('frameRate') or 0)
    except ValueError:
        return 0, 0


def _best_quality(qualities):
    """The clip file to play: the highest resolution, the higher frame rate at the same resolution."""
    return max(qualities, key=_rank)


def _clip(slug):
    """(the clip's files that have an address, its playback token); PlaybackError when either is missing."""
    data = gql.query('query{clip(slug:%s){videoQualities{quality frameRate sourceURL} '
                     'playbackAccessToken(params:%s){value signature}}}' % (lists.literal(slug), TOKEN_PARAMS))
    clip = data.get('clip') or {}
    qualities = [q for q in clip.get('videoQualities') or [] if q.get('sourceURL')]
    token = clip.get('playbackAccessToken') or {}
    if not qualities or not token.get('value'):
        raise PlaybackError('clip')
    return qualities, token


def _signed(url, token):
    """A clip file's address with the token Twitch's CDN asks for."""
    return url + ('&' if '?' in url else '?') + urllib.parse.urlencode(
        {'sig': token['signature'], 'token': token['value']})


def clip_url(slug):
    """The MP4 file of a clip, at its best quality."""
    qualities, token = _clip(slug)
    return _signed(_best_quality(qualities)['sourceURL'], token)


def clip_files(slug):
    """Every file of a clip, best first: [(its videoQualities entry, signed address)]."""
    qualities, token = _clip(slug)
    return [(q, _signed(q['sourceURL'], token)) for q in sorted(qualities, key=_rank, reverse=True)]
