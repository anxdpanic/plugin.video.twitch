# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""Play (choose quality): the renditions Twitch offers for a stream, video or clip, listed for the viewer to pick
one, whatever the player setting. A live stream or past broadcast is then played from that rendition's own
playlist (which either inputstream add-on plays as it is), a clip from that rendition's file."""
import re

import xbmcgui

from . import http, kodi, playback

ATTRIBUTE = re.compile(r'([A-Z0-9-]+)=("[^"]*"|[^,]*)')
CODEC_NAMES = (('av01', 'AV1'), ('hvc1', 'HEVC'), ('hev1', 'HEVC'), ('avc1', 'H.264'))
SOURCE_GROUP = 'chunked'  # Twitch's name for the rendition that is the broadcaster's own


class Cancelled(Exception):
    """The viewer closed the quality list without picking one."""


def _attributes(line):
    """The attributes of an #EXT-X-... line, quotes taken off."""
    return {key: value.strip('"') for key, value in ATTRIBUTE.findall(line.split(':', 1)[1])}


def _codec(codecs):
    """'H.264', 'HEVC' or 'AV1', from a rendition's CODECS."""
    return next((name for prefix, name in CODEC_NAMES if prefix in codecs), '')


def _rendition(info, names, url):
    """A rendition from its #EXT-X-STREAM-INF attributes, the names of the video groups, and its address."""
    group = info.get('VIDEO', '')
    height = int((info.get('RESOLUTION') or 'x0').split('x')[-1] or 0)
    return {'name': names.get(group) or group, 'height': height, 'fps': float(info.get('FRAME-RATE') or 0),
            'bandwidth': int(info.get('BANDWIDTH') or 0), 'codec': _codec(info.get('CODECS', '')),
            'source': group == SOURCE_GROUP, 'url': url}


def renditions(master):
    """The video renditions of a master playlist, best first: [{'name', 'height', 'fps', 'bandwidth', 'codec',
    'source', 'url'}]. Audio-only ones (no resolution) are left out."""
    names, found, info = {}, [], None
    for line in master.splitlines():
        if line.startswith('#EXT-X-MEDIA:'):
            media = _attributes(line)
            names[media.get('GROUP-ID', '')] = media.get('NAME', '')
        elif line.startswith('#EXT-X-STREAM-INF:'):
            info = _attributes(line)
        elif info is not None and line and not line.startswith('#'):
            if info.get('RESOLUTION'):
                found.append(_rendition(info, names, line.strip()))
            info = None
    return sorted(found, key=lambda r: (r['height'], r['fps'], r['bandwidth']), reverse=True)


def _megabits(bandwidth):
    return '%.1f Mbps' % (bandwidth / 1e6)


def label(rendition):
    """'1080p60 (source) • HEVC • 8.0 Mbps' for the quality list. Twitch names live sources '1440p60 (source)'
    itself, but not every source."""
    source = rendition['source'] and 'source' not in rendition['name'].lower()
    name = rendition['name'] + (' (%s)' % kodi.string(30122) if source else '')
    parts = [name, rendition.get('codec'), _megabits(rendition['bandwidth']) if rendition.get('bandwidth') else '']
    return ' • '.join(p for p in parts if p)


def _pick(options):
    """The option the viewer picks from the list; raises Cancelled when they close it."""
    picked = xbmcgui.Dialog().select(kodi.string(30121), [label(o) for o in options])
    if picked < 0:
        raise Cancelled()
    return options[picked]


def choose_rendition(master_url):
    """The playlist address of the rendition the viewer picks from a master playlist."""
    _, body = http.request(master_url)
    options = renditions(body.decode('utf-8', 'replace'))
    if not options:
        return master_url  # nothing to choose from: play it as it is
    return _pick(options)['url']


def _clip_option(quality, url):
    """A clip file as a rendition: '1080p60' and its signed address."""
    height = int(quality.get('quality') or 0)
    fps = int(float(quality.get('frameRate') or 0))
    return {'name': '%dp%s' % (height, fps if fps > 30 else ''), 'height': height, 'fps': fps, 'bandwidth': 0,
            'codec': '', 'source': False, 'url': url}


def choose_clip(slug):
    """The file address of the clip quality the viewer picks."""
    options = [_clip_option(q, url) for q, url in playback.clip_files(slug)]
    return _pick(options)['url']
