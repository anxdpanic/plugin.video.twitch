# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""The words shown with an item: the line under a tile (meta_line), the details text (plot), and the counts,
ages and times they are made of. Times from Twitch are UTC ('2026-11-24T19:18:20Z'); they are shown in
local time, in Kodi's region format."""
import calendar
import time

from . import kodi

TYPE_NAMES = {'ARCHIVE': 30045, 'HIGHLIGHT': 30046, 'UPLOAD': 30047}  # broadcastType -> its name
DAY = 86400


# Numbers
def short_count(value):
    """123456 -> '123K', 1234567 -> '1.2M', as Twitch writes viewer counts."""
    for limit, suffix in ((1e9, 'B'), (1e6, 'M'), (1e3, 'K')):
        if value >= limit:
            number = value / limit
            text = ('%.1f' % number).rstrip('0').rstrip('.') if number < 10 else '%d' % number
            return text + suffix
    return str(value)


def viewers(count):
    """'1.2K viewers'."""
    return kodi.formatted(30040, short_count(count))


def views(count):
    """'228K views'."""
    return kodi.formatted(30041, short_count(count))


def format_time(seconds):
    """3725 -> '1:02:05', 65 -> '1:05'."""
    seconds = max(int(seconds or 0), 0)
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return '%d:%02d:%02d' % (hours, minutes, secs) if hours else '%d:%02d' % (minutes, secs)


# Times
def timestamp(iso):
    """Seconds since the epoch of Twitch's '2026-11-24T19:18:20Z'; 0 when it can't be read."""
    try:
        return calendar.timegm(time.strptime((iso or '')[:19], '%Y-%m-%dT%H:%M:%S'))
    except ValueError:
        return 0


def _minutes_since(iso, now=None):
    """Whole minutes from a Twitch time until now (never negative)."""
    return max(int(((now or time.time()) - timestamp(iso)) // 60), 0)


def age(iso, now=None):
    """'3 hours ago', 'yesterday', '2 months ago'; '' when unknown."""
    if not timestamp(iso):
        return ''
    minutes = _minutes_since(iso, now)
    hours, days = minutes // 60, minutes // 1440
    if minutes < 2:
        return kodi.string(30049)
    if hours < 1:
        return kodi.formatted(30050, minutes)
    if hours < 24:
        return kodi.string(30051) if hours == 1 else kodi.formatted(30052, hours)
    if days < 2:
        return kodi.string(30053)
    if days < 30:
        return kodi.formatted(30054, days)
    if days < 365:
        months = days // 30
        return kodi.string(30055) if months == 1 else kodi.formatted(30056, months)
    years = days // 365
    return kodi.string(30057) if years == 1 else kodi.formatted(30058, years)


def uptime(iso, now=None):
    """How long a stream has been live: '2h 05m', or '' when unknown."""
    if not timestamp(iso):
        return ''
    minutes = _minutes_since(iso, now)
    return '%dh %02dm' % divmod(minutes, 60) if minutes >= 60 else '%dm' % minutes


def _local(iso):
    return time.localtime(timestamp(iso))


def day_name(iso, now=None):
    """'Today', 'Tomorrow', or the weekday and date ('Thu 27 Nov') of a time, in local time."""
    day = time.strftime('%Y-%m-%d', _local(iso))
    today = time.localtime(now or time.time())
    if day == time.strftime('%Y-%m-%d', today):
        return kodi.string(30106)
    if day == time.strftime('%Y-%m-%d', time.localtime(time.mktime(today) + DAY)):
        return kodi.string(30107)
    return time.strftime('%a %d %b', _local(iso))


def clock_time(iso):
    """A time of day in the region's format: '19:00', or '3:30 PM' (no leading zero on 12-hour clocks)."""
    clock = kodi.time_format()
    text = time.strftime(clock, _local(iso))
    return text[1:] if clock.startswith('%I') and text.startswith('0') else text


def span(start, end):
    """'19:00 - 03:00', or the start alone when there is no end."""
    return clock_time(start) + (' - ' + clock_time(end) if end else '')


def when(start, end, now=None):
    """'Tomorrow 19:00 - 03:00' for a scheduled stream."""
    return '%s %s' % (day_name(start, now), span(start, end))


# Parts of the lines
def _join(parts):
    """Parts that have something in them, joined with bullets."""
    return ' • '.join(p for p in parts if p)


def _lines(lines):
    """Lines that have something in them, one under another."""
    return '\n'.join(line for line in lines if line)


def stream_facts(item):
    """'18+ • English • Speedrun, Chill' for a live stream; '' when it has none of them."""
    return _join(['18+' if item.get('mature') else '',
                  kodi.language_name(item['language']) if item.get('language') else '',
                  ', '.join(item.get('tags') or [])])


def _playing(game_title):
    """'Playing Celeste', or '' when there is no category."""
    return kodi.formatted(30043, game_title) if game_title else ''


def _video_type(item):
    """'Clip', 'Past broadcast', 'Highlight' or 'Upload'."""
    if item['kind'] == 'clip':
        return kodi.string(30048)
    type_id = TYPE_NAMES.get(item.get('broadcast_type'))
    return kodi.string(type_id) if type_id else ''


# The line under a tile, by kind of item
def _channel_meta(item):
    """'LIVE • 1.2K viewers' for a live channel, '12K followers' otherwise."""
    if item['live']:
        return _join([kodi.string(30039), viewers(item['viewers'])])
    return kodi.formatted(30042, short_count(item['followers'])) if item['followers'] else ''


def _scheduled_meta(item):
    """The stream's day and times; only the times for an untitled one, which has its day as its title."""
    return span(item['start'], item['end']) if item['untitled'] else when(item['start'], item['end'])


META_LINES = {
    'live': lambda item: _join([item['channel'], viewers(item['viewers'])]),
    'video': lambda item: _join([item['channel'], views(item['views']), age(item['published'])]),
    'clip': lambda item: _join([item['channel'], views(item['views']), age(item['published'])]),
    'channel': _channel_meta,
    'category': lambda item: viewers(item['viewers']) if item['viewers'] else '',
    'scheduled': _scheduled_meta,
}


def meta_line(item):
    """The short line under a tile's title ('' for kinds that have none)."""
    line = META_LINES.get(item['kind'])
    return line(item) if line else ''


# The details text, by kind of item
def _live_plot(item):
    started = kodi.formatted(30044, uptime(item['started'])) if item['started'] else ''
    return [item['channel'], _playing(item['game_title']), _join([viewers(item['viewers']), started]),
            stream_facts(item)]


def _video_plot(item):
    return [item['channel'], item['game_title'],
            _join([_video_type(item), format_time(item['duration']), views(item['views']), age(item['published'])])]


def _channel_plot(item):
    return [item['description'], _join([_playing(item['game_title']) if item['live'] else '', meta_line(item)])]


PLOTS = {
    'live': _live_plot,
    'video': _video_plot,
    'clip': _video_plot,
    'channel': _channel_plot,
    'category': lambda item: [', '.join(item['tags']), meta_line(item)],
    'scheduled': lambda item: [item['channel'], item['game_title'], when(item['start'], item['end'])],
}


def plot(item):
    """The details text: what the focused tile shows under its title, and the plot of a listing's item.
    Items made by the window itself (search actions) carry their own text in 'plot'."""
    lines = PLOTS.get(item['kind'])
    return _lines(lines(item) if lines else [item.get('plot', '')])
