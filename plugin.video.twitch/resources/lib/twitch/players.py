# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""Which inputstream add-on plays Twitch's HLS streams, and the list item each one is handed.

InputStream Adaptive (the default) picks a rendition by the connection's speed and switches as it goes, or asks
for one each time. InputStream FFmpeg Direct opens the playlist with FFmpeg's own demuxer and buffering, which
some devices handle better for live streams; it keeps to the best rendition and can pause and rewind (timeshift).

The player setting only applies to live streams. Everything else uses Adaptive:
- past broadcasts: FFmpeg Direct's seeking in them stalls (tested on the Vero: the first seek took 20 s, later
  ones stuck at 0:00);
- Play from beginning: FFmpeg opens a broadcast still being recorded as a live playlist and starts a few
  segments from its end, with no way to ask for the start."""
import json

import xbmc
import xbmcgui

from . import kodi

ADAPTIVE = 'inputstream.adaptive'
FFMPEG_DIRECT = 'inputstream.ffmpegdirect'
PLAYERS = {0: ADAPTIVE, 1: FFMPEG_DIRECT}  # the player setting -> add-on id
HLS_MIME = 'application/vnd.apple.mpegurl'
LIVE_DELAY = 8  # seconds Adaptive stays behind the live edge, so a live stream doesn't stall


def _enabled(addon_id):
    return xbmc.getCondVisibility('System.AddonIsEnabled(%s)' % addon_id)


def _installed(addon_id):
    return xbmc.getCondVisibility('System.HasAddon(%s)' % addon_id)


def _enable(addon_id):
    """Turn an installed add-on on (Kodi has no builtin for it, JSON-RPC does)."""
    xbmc.executeJSONRPC(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'Addons.SetAddonEnabled',
                                    'params': {'addonid': addon_id, 'enabled': True}}))


def _offer_ffmpeg_direct():
    """FFmpeg Direct is chosen but turned off: offer to turn it on. True when it is on now."""
    if not _installed(FFMPEG_DIRECT):
        return False
    if not xbmcgui.Dialog().yesno(kodi.string(30110), kodi.string(30114)):
        return False
    _enable(FFMPEG_DIRECT)
    return _enabled(FFMPEG_DIRECT)


def chosen(live):
    """The add-on to play with: for a live stream, the setting's, falling back to Adaptive when FFmpeg Direct
    isn't there or the viewer won't turn it on; Adaptive for everything else."""
    player = PLAYERS.get(kodi.setting_int('player'), ADAPTIVE) if live else ADAPTIVE
    if player == FFMPEG_DIRECT and not (_enabled(FFMPEG_DIRECT) or _offer_ffmpeg_direct()):
        kodi.log('%s is not enabled, playing with %s' % (FFMPEG_DIRECT, ADAPTIVE))
        return ADAPTIVE
    return player


def _adaptive(li, live, from_start):
    """Adaptive's properties. A broadcast still being recorded is a growing playlist, which Adaptive plays
    like a live stream from its end unless told to start at the beginning (from_start)."""
    if kodi.setting_bool('ask_quality'):
        li.setProperty('inputstream.adaptive.stream_selection_type', 'ask-quality')
    if live:
        li.setProperty('inputstream.adaptive.live_delay', str(LIVE_DELAY))
    if from_start:
        li.setProperty('inputstream.adaptive.play_timeshift_buffer', 'true')


def _ffmpeg_direct(li):
    """FFmpeg Direct's properties: a live HLS playlist opened by FFmpeg, as a real-time stream with timeshift,
    so it can be paused and rewound."""
    li.setProperty('inputstream.ffmpegdirect.manifest_type', 'hls')
    li.setProperty('inputstream.ffmpegdirect.open_mode', 'ffmpeg')
    li.setProperty('inputstream.ffmpegdirect.is_realtime_stream', 'true')
    li.setProperty('inputstream.ffmpegdirect.stream_mode', 'timeshift')


def stream_item(url, live, from_start=False):
    """The list item that plays an HLS stream with the chosen inputstream add-on."""
    li = xbmcgui.ListItem(path=url, offscreen=True)
    li.setMimeType(HLS_MIME)
    li.setContentLookup(False)
    player = chosen(live)
    li.setProperty('inputstream', player)
    if player == FFMPEG_DIRECT:
        _ffmpeg_direct(li)
    else:
        _adaptive(li, live, from_start)
    return li
