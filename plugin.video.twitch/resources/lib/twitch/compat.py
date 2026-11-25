# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""The plugin addresses of earlier versions (plugin://plugin.video.twitch/?mode=...), translated to this one's.

Other add-ons play and list Twitch through them (Eventvods plays past broadcasts at a time with
?mode=play&video_id=...&seek_time=..., Rocket Beans plays and lists its channel by id), as do favourites,
.strm files and keymaps made with earlier versions. Channels named by id are looked up to their login."""
from . import gql, lists

BROADCAST_TYPES = {'archive': 'ARCHIVE', 'highlight': 'HIGHLIGHT', 'upload': 'UPLOAD'}
LIST_PAGES = {'following': 'following', 'followed': 'following', 'featured_streams': 'home', 'stream_list': 'home',
              'browse': 'home', 'games': 'categories'}  # old list modes -> this version's page


def login_of(params):
    """The channel's login from channel_name, else looked up from channel_id; '' when neither is given."""
    if params.get('channel_name'):
        return params['channel_name'].lower()
    if not params.get('channel_id'):
        return ''
    data = gql.query('query{user(id:%s){login}}' % lists.literal(params['channel_id']))
    user = data.get('user')
    if not user:
        raise gql.GQLError('no channel with id %s' % params['channel_id'])
    return user['login']


def _seconds(value):
    """seek_time as whole seconds; None for none, zero or a value that isn't a number."""
    try:
        seconds = int(float(value or 0))
    except ValueError:
        return None
    return seconds if seconds > 0 else None


def _play(params):
    """?mode=play: a past broadcast (video_id, at seek_time), a clip (slug) or a channel's live stream."""
    if params.get('video_id'):
        video_id = params['video_id'].lstrip('v')  # very old versions wrote 'v123'
        return 'play', {'video': video_id, 't': _seconds(params.get('seek_time'))}
    if params.get('slug'):
        return 'play', {'clip': params['slug']}
    return 'play', {'live': login_of(params)}


def _channel_page(params):
    """?mode=channel_videos: the channel's page."""
    login = login_of(params)
    return 'page', {'desc': {'page': 'channel', 'login': login, 'title': params.get('display_name') or login}}


def _channel_video_list(params):
    """?mode=channel_video_list: one kind of the channel's videos (the first, when several are named)."""
    login = login_of(params)
    first = (params.get('broadcast_type') or 'archive').split(',')[0].strip().lower()
    video_type = BROADCAST_TYPES.get(first, 'ARCHIVE')
    return 'page', {'desc': {'page': 'list', 'list': 'channel_videos', 'title': login,
                             'params': {'login': login, 'type': video_type}}}


def _clips_list(params):
    """?mode=clips_list: a channel's clips; the main menu when it named only a category by id."""
    if not (params.get('channel_id') or params.get('channel_name')):
        return '', {}
    login = login_of(params)
    return 'page', {'desc': {'page': 'list', 'list': 'channel_clips', 'title': login, 'params': {'login': login}}}


def _category_page(params):
    """?mode=game_streams (game) or ?mode=game_lists (game_name): the category's page."""
    name = params.get('game') or params.get('game_name') or ''
    if not name:
        return '', {}
    return 'page', {'desc': {'page': 'category', 'name': name, 'title': name}}


MODES = {
    'play': _play,
    'channel_videos': _channel_page,
    'channel_video_list': _channel_video_list,
    'clips_list': _clips_list,
    'game_streams': _category_page,
    'game_lists': _category_page,
    'search': lambda params: ('search_list', {}),
    'settings': lambda params: ('settings', {}),
}


def translate(params):
    """(route, params) of this version for an earlier version's ?mode=... parameters. Modes with no
    counterpart (cache, token and quality maintenance) open the main menu."""
    mode = params.get('mode') or ''
    if mode in LIST_PAGES:
        return 'page', {'desc': {'page': LIST_PAGES[mode]}}
    handler = MODES.get(mode)
    return handler(params) if handler else ('', {})
