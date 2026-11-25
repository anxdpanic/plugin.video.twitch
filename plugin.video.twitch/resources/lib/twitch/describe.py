# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""The words shown with an item: the line under a tile, the details text, counts and ages."""
import calendar
import time

from . import kodi

TYPE_NAMES = {'ARCHIVE': 30045, 'HIGHLIGHT': 30046, 'UPLOAD': 30047}


def short_count(value):
    """123456 -> '123K', 1234567 -> '1.2M', as Twitch writes viewer counts."""
    for limit, suffix in ((1e9, 'B'), (1e6, 'M'), (1e3, 'K')):
        if value >= limit:
            number = value / limit
            text = ('%.1f' % number).rstrip('0').rstrip('.') if number < 10 else '%d' % number
            return text + suffix
    return str(value)


def format_time(seconds):
    """3725 -> '1:02:05', 65 -> '1:05'."""
    seconds = max(int(seconds or 0), 0)
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return '%d:%02d:%02d' % (hours, minutes, secs) if hours else '%d:%02d' % (minutes, secs)


def timestamp(iso):
    """Seconds since the epoch of Twitch's '2026-11-24T19:18:20Z'; 0 when it can't be read."""
    try:
        return calendar.timegm(time.strptime((iso or '')[:19], '%Y-%m-%dT%H:%M:%S'))
    except ValueError:
        return 0


def age(iso, now=None):
    """'3 hours ago', 'yesterday', '2 months ago'; '' when unknown."""
    then = timestamp(iso)
    if not then:
        return ''
    minutes = max(int(((now or time.time()) - then) // 60), 0)
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
    then = timestamp(iso)
    if not then:
        return ''
    minutes = max(int(((now or time.time()) - then) // 60), 0)
    return '%dh %02dm' % divmod(minutes, 60) if minutes >= 60 else '%dm' % minutes


def _join(parts):
    return ' • '.join(p for p in parts if p)


def viewers(count):
    return kodi.formatted(30040, short_count(count))


def views(count):
    return kodi.formatted(30041, short_count(count))


def meta_line(item):
    """The short line under a tile's title."""
    kind = item['kind']
    if kind == 'live':
        return _join([item['channel'], viewers(item['viewers'])])
    if kind in ('video', 'clip'):
        return _join([item['channel'], views(item['views']), age(item['published'])])
    if kind == 'channel':
        if item['live']:
            return _join([kodi.string(30039), viewers(item['viewers'])])
        return kodi.formatted(30042, short_count(item['followers'])) if item['followers'] else ''
    if kind == 'category':
        return viewers(item['viewers']) if item['viewers'] else ''
    if kind == 'scheduled':  # an untitled one already has its day as its title
        return span(item['start'], item['end']) if item['untitled'] else when(item['start'], item['end'])
    return ''


def stream_facts(item):
    """'18+ • English • Speedrun, Chill' for a live stream; '' when it has none of them."""
    return _join(['18+' if item.get('mature') else '',
                  kodi.language_name(item['language']) if item.get('language') else '',
                  ', '.join(item.get('tags') or [])])


def _local(iso):
    return time.localtime(timestamp(iso))


def day_name(iso, now=None):
    """'Today', 'Tomorrow', or the weekday and date ('Thu 27 Nov') of a time, in local time."""
    day = time.strftime('%Y-%m-%d', _local(iso))
    today = time.localtime(now or time.time())
    if day == time.strftime('%Y-%m-%d', today):
        return kodi.string(30106)
    if day == time.strftime('%Y-%m-%d', time.localtime(time.mktime(today) + 86400)):
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


def _video_type(item):
    if item['kind'] == 'clip':
        return kodi.string(30048)
    type_id = TYPE_NAMES.get(item.get('broadcast_type'))
    return kodi.string(type_id) if type_id else ''


def plot(item):
    """The details text: what the focused tile shows under its title, and the plot of a listing's item."""
    kind = item['kind']
    if kind == 'live':
        lines = [item['channel'],
                 kodi.formatted(30043, item['game_title']) if item['game_title'] else '',
                 _join([viewers(item['viewers']),
                        kodi.formatted(30044, uptime(item['started'])) if item['started'] else '']),
                 stream_facts(item)]
    elif kind == 'scheduled':
        lines = [item['channel'], item['game_title'], when(item['start'], item['end'])]
    elif kind in ('video', 'clip'):
        lines = [item['channel'], item['game_title'],
                 _join([_video_type(item), format_time(item['duration']), views(item['views']),
                        age(item['published'])])]
    elif kind == 'channel':
        lines = [item['description'],
                 _join([kodi.formatted(30043, item['game_title']) if item['live'] and item['game_title'] else '',
                        meta_line(item)])]
    elif kind == 'category':
        lines = [', '.join(item['tags']), meta_line(item)]
    else:
        lines = [item.get('plot', '')]
    return '\n'.join(line for line in lines if line)
