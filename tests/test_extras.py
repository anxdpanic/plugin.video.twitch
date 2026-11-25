"""Watch from the start, channel schedules, and the tags, language and mature flag of live streams."""
import pytest
import xbmcplugin
from samples import STREAM, USER

from resources.lib.twitch import describe, gql, lists, parser, playback, router

SEGMENT = {'id': 's1', 'title': 'Any% attempts', 'startAt': '2026-11-27T19:00:00Z', 'endAt': '2026-11-27T23:00:00Z',
           'isCancelled': False, 'categories': [{'name': 'Celeste', 'displayName': 'Celeste',
                                                 'boxArtURL': 'https://cdn/celeste.jpg'}]}
NOW = describe.timestamp('2026-11-26T12:00:00Z')


def schedule_reply(segments):
    return {'user': dict(USER, channel={'schedule': {'segments': segments}})}


def test_schedule_keeps_coming_streams_soonest_first():
    past = dict(SEGMENT, id='old', startAt='2026-11-20T19:00:00Z', endAt='2026-11-20T23:00:00Z')
    later = dict(SEGMENT, id='later', startAt='2026-11-29T19:00:00Z', endAt='2026-11-29T23:00:00Z')
    cancelled = dict(SEGMENT, id='off', isCancelled=True)
    items, cursor = lists._schedule_read(schedule_reply([later, past, cancelled, SEGMENT]), now=NOW)
    assert [i['id'] for i in items] == ['s1', 'later'] and cursor is None


def test_scheduled_item(monkeypatch):
    monkeypatch.setattr(describe, 'day_name', lambda iso, now=None: 'Tomorrow')
    item = parser.scheduled(dict(SEGMENT, title='', categories=[]), USER)
    assert (item['title'], item['untitled'], item['thumb'], item['poster'], item['game']) == (
        'Tomorrow', True, 'https://cdn/runner.png', False, '')
    item = parser.scheduled(SEGMENT, USER)
    assert (item['title'], item['untitled'], item['poster'], item['game_title']) == (
        'Any% attempts', False, True, 'Celeste')


def test_untitled_schedule_line_is_only_the_times(monkeypatch):
    monkeypatch.setattr(describe, 'day_name', lambda iso, now=None: 'Tomorrow')
    untitled = parser.scheduled(dict(SEGMENT, title=''), USER)
    assert not describe.meta_line(untitled).startswith('Tomorrow')
    assert describe.meta_line(parser.scheduled(SEGMENT, USER)).startswith('Tomorrow ')


def test_scheduled_item_leads_to_its_category():
    with_game = parser.scheduled(SEGMENT, USER)
    assert '/page/?desc=' in router.item_url(with_game) and router.is_folder(with_game)
    without = parser.scheduled(dict(SEGMENT, categories=[]), USER)
    assert router.item_url(without).endswith('/noop/') and not router.is_folder(without)


def test_when_names_today_and_tomorrow(english):
    english(30106, 30107)
    assert describe.day_name('2026-11-26T12:00:00Z', now=NOW) == 'Today'
    assert describe.day_name('2026-11-27T12:00:00Z', now=NOW) == 'Tomorrow'
    assert describe.when('2026-11-27T12:00:00Z', '', now=NOW).startswith('Tomorrow ')


def test_stream_facts():
    item = parser.live(dict(STREAM, language='EN', isMature=True, freeformTags=[{'name': 'Speedrun'},
                                                                                 {'name': 'Chill'}]))
    assert (item['language'], item['mature'], item['tags']) == ('en', True, ['Speedrun', 'Chill'])
    assert describe.stream_facts(item) == '18+ • EN • Speedrun, Chill'  # the stub has no language names
    assert describe.stream_facts(parser.live(STREAM)) == ''


def test_play_from_start_plays_the_recording(monkeypatch):
    monkeypatch.setattr(gql, 'query', lambda text, variables=None, anonymous=False: {'user': {
        'stream': {'id': '1'}, 'videos': {'edges': [{'node': {'id': '99', 'status': 'RECORDING'}}]}}})
    monkeypatch.setattr(playback, 'video_url', lambda video_id: 'https://usher/vod/%s.m3u8' % video_id)
    router.run([router.url_for('play').split('?')[0], '1', '?from_start=runner'])
    assert xbmcplugin.RESOLVED[0][1].path == 'https://usher/vod/99.m3u8'


@pytest.mark.parametrize('user', [
    {'stream': None, 'videos': {'edges': [{'node': {'id': '99', 'status': 'RECORDING'}}]}},
    {'stream': {'id': '1'}, 'videos': {'edges': [{'node': {'id': '98', 'status': 'RECORDED'}}]}},
    {'stream': {'id': '1'}, 'videos': {'edges': []}},
])
def test_no_recording_to_start_from(monkeypatch, user):
    monkeypatch.setattr(gql, 'query', lambda text, variables=None, anonymous=False: {'user': user})
    with pytest.raises(playback.PlaybackError):
        playback.recording_id('runner')


def test_live_menu_starts_with_play_from_beginning(english):
    english(30100)
    assert router._context_menu(parser.live(STREAM))[0][0] == 'Play from beginning'


def test_play_from_start_starts_at_the_beginning_of_the_recording(monkeypatch):
    monkeypatch.setattr(playback, 'recording_id', lambda login: '99')
    monkeypatch.setattr(playback, 'video_url', lambda video_id: 'https://usher/vod/99.m3u8')
    router.run([router.url_for('play').split('?')[0], '1', '?from_start=runner'])
    assert xbmcplugin.RESOLVED[0][1].getProperty('inputstream.adaptive.play_timeshift_buffer') == 'true'


def test_twelve_hour_clock_has_no_leading_zero(monkeypatch):
    from resources.lib.twitch import kodi
    monkeypatch.setattr(kodi, 'time_format', lambda: '%I:%M %p')
    monkeypatch.setattr(describe, '_local', lambda iso: (2026, 11, 27, 15, 30, 0, 4, 331, 0))
    assert describe.clock_time('x') == '3:30 PM'
