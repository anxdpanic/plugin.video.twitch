"""Addresses of earlier versions (?mode=...), as other add-ons, favourites and .strm files use them."""
import json

import pytest
import xbmcplugin

from resources.lib.twitch import compat, gql, pages, playback, players, router


@pytest.fixture
def user_ids(monkeypatch):
    """Channel ids GraphQL knows: 123 is runner."""
    asked = []

    def query(text, variables=None, anonymous=False):
        asked.append(text)
        return {'user': {'login': 'runner'} if 'id:"123"' in text else None}
    monkeypatch.setattr(gql, 'query', query)
    return asked


def test_eventvods_video_at_a_time():
    assert compat.translate({'mode': 'play', 'video_id': '2939600059', 'seek_time': '754'}) == \
        ('play', {'video': '2939600059', 't': 754})


def test_old_style_video_id_and_no_seek():
    route, params = compat.translate({'mode': 'play', 'video_id': 'v42', 'seek_time': '0'})
    assert (route, params) == ('play', {'video': '42', 't': None})


def test_live_by_name_and_clip():
    assert compat.translate({'mode': 'play', 'channel_name': 'Runner'}) == ('play', {'live': 'runner'})
    assert compat.translate({'mode': 'play', 'slug': 'FunnyClip'}) == ('play', {'clip': 'FunnyClip'})


def test_rocketbeans_live_by_channel_id(user_ids):
    assert compat.translate({'mode': 'play', 'channel_id': '123'}) == ('play', {'live': 'runner'})
    assert 'user(id:"123")' in user_ids[0]


def test_unknown_channel_id_is_an_error(user_ids):
    with pytest.raises(gql.GQLError):
        compat.translate({'mode': 'play', 'channel_id': '999'})


def test_rocketbeans_uploads(user_ids):
    route, params = compat.translate({'mode': 'channel_video_list', 'broadcast_type': 'upload', 'channel_id': '123'})
    assert route == 'page'
    assert params['desc'] == {'page': 'list', 'list': 'channel_videos', 'title': 'runner',
                              'params': {'login': 'runner', 'type': 'UPLOAD'}}


def test_pages_and_unknown_modes():
    assert compat.translate({'mode': 'channel_videos', 'channel_name': 'runner'})[1]['desc']['page'] == 'channel'
    assert compat.translate({'mode': 'game_streams', 'game': 'Chess'})[1]['desc'] == \
        {'page': 'category', 'name': 'Chess', 'title': 'Chess'}
    assert compat.translate({'mode': 'following'}) == ('page', {'desc': {'page': 'following'}})
    assert compat.translate({'mode': 'reset_cache'}) == ('', {})


def test_router_plays_an_old_address_and_seeks(monkeypatch):
    monkeypatch.setattr(playback, 'video_url', lambda video_id: 'https://usher/vod/%s.m3u8' % video_id)
    seeks = []
    monkeypatch.setattr(players, 'start_at', lambda video_id, seconds: seeks.append((video_id, seconds)))
    router.run(['plugin://plugin.video.twitch/', '1', '?mode=play&video_id=42&seek_time=90'])
    assert xbmcplugin.RESOLVED[0][1].path == 'https://usher/vod/42.m3u8'
    assert seeks == [('42', 90.0)]


def test_router_lists_an_old_list_address(monkeypatch, user_ids):
    loaded = []
    monkeypatch.setattr(pages, 'load', lambda desc: loaded.append(desc) or
                        {'title': '', 'shelves': [], 'header': None, 'message': ''})
    router.run(['plugin://plugin.video.twitch/', '1',
                '?mode=channel_video_list&broadcast_type=upload&channel_id=123'])
    assert loaded == [json.loads(json.dumps({'page': 'list', 'list': 'channel_videos', 'title': 'runner',
                                             'params': {'login': 'runner', 'type': 'UPLOAD'}}))]


def test_router_without_mode_is_the_main_menu():
    router.run(['plugin://plugin.video.twitch/', '1', ''])
    assert xbmcplugin.ENDED == [True] and len(xbmcplugin.ITEMS) == 7
