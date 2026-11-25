from samples import CLIP, GAME, STREAM, USER, USER_STREAM, VIDEO

from resources.lib.twitch import parser


def test_live_stream_has_channel_game_and_previews():
    item = parser.live(STREAM)
    assert item['kind'] == 'live'
    assert item['id'] == item['login'] == 'runner'
    assert item['channel'] == 'Runner'
    assert item['viewers'] == 42066
    assert item['game'] == 'Celeste'
    assert '-640x360.jpg?t=' in item['thumb']
    assert '-1280x720.jpg?t=' in item['fanart']


def test_live_preview_address_changes_every_few_minutes():
    url = 'https://cdn/live_user_x-640x360.jpg'
    assert parser._live_preview(url, now=600) == parser._live_preview(url, now=899)
    assert parser._live_preview(url, now=600) != parser._live_preview(url, now=900)


def test_followed_channel_stream_takes_the_user_as_broadcaster():
    item = parser.live_user(dict(USER, stream=USER_STREAM))
    assert item['login'] == 'runner'
    assert item['title'] == 'Speedrun practice'


def test_emoji_are_taken_out_of_titles():
    assert parser.clean('RUSHEADA 🗣️ CUIDAO 🗣️ - GTA') == 'RUSHEADA CUIDAO - GTA'
    assert parser.clean('🔴[DROPS] GTA 6 🔴') == '[DROPS] GTA 6'
    assert parser.clean('Café ½ — ok') == 'Café ½ — ok'
    assert parser.live(dict(STREAM, title='🌴 Chill')).get('title') == 'Chill'


def test_untitled_stream_is_named_after_its_channel():
    assert parser.live(dict(STREAM, title=None))['title'] == 'Runner'


def test_video_and_clip():
    video = parser.video(VIDEO)
    assert (video['id'], video['duration'], video['broadcast_type']) == ('2939600059', 3725, 'ARCHIVE')
    assert video['thumb'].endswith('-640x360.jpg')
    clip = parser.clip(CLIP)
    assert (clip['id'], clip['duration'], clip['channel']) == ('FunnyClipSlug', 21, 'Runner')


def test_channel_offline_and_live():
    offline = parser.channel(USER)
    assert (offline['live'], offline['followers'], offline['fanart']) == (False, 12500, 'https://cdn/offline.jpg')
    live = parser.channel(dict(USER, stream={'viewersCount': 9, 'game': {'displayName': 'Celeste'}}))
    assert (live['live'], live['viewers'], live['game_title']) == (True, 9, 'Celeste')


def test_category():
    item = parser.category(GAME)
    assert (item['id'], item['title'], item['tags']) == ('Celeste', 'Celeste', ['Platformer'])
