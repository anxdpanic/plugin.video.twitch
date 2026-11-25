# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""Twitch's GraphQL nodes as the add-on's items: plain dicts shared by the plugin listings and the TV window.

Every item has 'kind' (live, video, clip, channel, category), 'id', 'title', 'thumb' and 'fanart'; the
rest depends on the kind."""
import re
import time

from . import describe, fonts

PREVIEW_REFRESH = 300  # seconds: a live preview's address changes this often, so Kodi fetches a new frame
BIG, SMALL = '1920x1080', '640x360'  # fanart, and the tile picture made from it
# Emoji and pictographs: skin fonts don't have them, so Kodi draws boxes. Joiners and variation selectors go too.
EMOJI = re.compile('[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002B00-\U00002BFF\U0000FE0E\U0000FE0F'
                   '\U0000200D\U000020E3\U000E0020-\U000E007F]+')
SPACES = re.compile(r'\s{2,}')


def clean(text):
    """Text without what the skin's font can't draw (it would show as boxes), and without the runs of spaces
    left behind."""
    drawable = fonts.current()
    text = ''.join(c if c in drawable else ' ' for c in EMOJI.sub(' ', text or ''))
    return SPACES.sub(' ', text).strip()


def _smaller(url):
    """The same image at tile size (Twitch puts the size in the address)."""
    return (url or '').replace(BIG, SMALL)


def _live_preview(url, now=None):
    """A live preview's address with a part that changes every few minutes: Kodi caches images by address,
    and the image at this one keeps changing."""
    if not url:
        return ''
    stamp = int((now or time.time()) // PREVIEW_REFRESH)
    return '%s%st=%d' % (url, '&' if '?' in url else '?', stamp)


def _game(node):
    game = node.get('game') or {}
    return game.get('name') or '', clean(game.get('displayName') or game.get('name'))


def _person(user):
    user = user or {}
    return {'login': user.get('login') or '', 'channel': clean(user.get('displayName')) or user.get('login') or '',
            'avatar': user.get('profileImageURL') or ''}


def live(stream, user=None):
    """A live stream; `user` is its broadcaster when the stream node doesn't carry one (followed channels)."""
    person = _person(user or stream.get('broadcaster'))
    game, game_title = _game(stream)
    preview = stream.get('previewImageURL') or ''
    item = {'kind': 'live', 'id': person['login'], 'title': clean(stream.get('title')) or person['channel'],
            'thumb': _live_preview(_smaller(preview)), 'fanart': _live_preview(preview),
            'viewers': int(stream.get('viewersCount') or 0), 'started': stream.get('createdAt') or '',
            'game': game, 'game_title': game_title, 'language': (stream.get('language') or '').lower(),
            'mature': bool(stream.get('isMature')),
            'tags': [t for t in (clean(tag.get('name')) for tag in stream.get('freeformTags') or []) if t]}
    item.update(person)
    return item


def live_user(user):
    """A followed channel that is live: the user node with its stream inside."""
    return live(user.get('stream') or {}, user)


def video(node):
    """A past broadcast, highlight or upload."""
    person = _person(node.get('owner'))
    game, game_title = _game(node)
    preview = node.get('previewThumbnailURL') or ''
    item = {'kind': 'video', 'id': node.get('id') or '', 'title': clean(node.get('title')) or person['channel'],
            'thumb': _smaller(preview), 'fanart': preview, 'duration': int(node.get('lengthSeconds') or 0),
            'views': int(node.get('viewCount') or 0), 'published': node.get('publishedAt') or '',
            'broadcast_type': node.get('broadcastType') or '', 'game': game, 'game_title': game_title}
    item.update(person)
    return item


def clip(node):
    person = _person(node.get('broadcaster'))
    game, game_title = _game(node)
    item = {'kind': 'clip', 'id': node.get('slug') or node.get('id') or '',
            'title': clean(node.get('title')) or person['channel'],
            'thumb': _smaller(node.get('thumbnailURL')), 'fanart': node.get('thumbnailURL') or '',
            'duration': int(node.get('durationSeconds') or 0), 'views': int(node.get('viewCount') or 0),
            'published': node.get('createdAt') or '', 'game': game, 'game_title': game_title}
    item.update(person)
    return item


def scheduled(segment, user):
    """A stream on a channel's schedule. Its picture is its category's box art, or the channel's picture."""
    person = _person(user)
    categories = segment.get('categories') or [{}]
    game = categories[0] if categories else {}
    title = clean(segment.get('title'))
    start = segment.get('startAt') or ''
    item = {'kind': 'scheduled', 'id': segment.get('id') or '',
            'title': title or describe.day_name(start),  # untitled: named by its day, not the channel again
            'untitled': not title, 'thumb': game.get('boxArtURL') or person['avatar'],
            'poster': bool(game.get('boxArtURL')), 'fanart': user.get('offlineImageURL') or '',
            'start': start, 'end': segment.get('endAt') or '',
            'game': game.get('name') or '', 'game_title': clean(game.get('displayName') or game.get('name'))}
    item.update(person)
    return item


def channel(node):
    person = _person(node)
    stream = node.get('stream') or {}
    item = {'kind': 'channel', 'id': person['login'], 'title': person['channel'], 'thumb': person['avatar'],
            'fanart': node.get('offlineImageURL') or node.get('bannerImageURL') or '',
            'description': clean(node.get('description')),
            'followers': int(((node.get('followers') or {}).get('totalCount')) or 0),
            'live': bool(stream), 'viewers': int(stream.get('viewersCount') or 0),
            'game_title': clean((stream.get('game') or {}).get('displayName'))}
    item.update(person)
    return item


def category(node):
    name = node.get('name') or ''
    return {'kind': 'category', 'id': name, 'title': clean(node.get('displayName')) or name,
            'thumb': node.get('boxArtURL') or '', 'fanart': '', 'viewers': int(node.get('viewersCount') or 0),
            'tags': [t.get('localizedName') for t in node.get('tags') or [] if t.get('localizedName')]}
