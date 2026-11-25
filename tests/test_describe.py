from samples import GAME, STREAM, USER, VIDEO

from resources.lib.twitch import describe, parser

NOW = describe.timestamp('2026-11-25T12:00:00Z')


def test_short_count():
    assert describe.short_count(999) == '999'
    assert describe.short_count(42066) == '42K'
    assert describe.short_count(1234567) == '1.2M'
    assert describe.short_count(1000000) == '1M'


def test_format_time():
    assert describe.format_time(65) == '1:05'
    assert describe.format_time(3725) == '1:02:05'


def test_age(english):
    english(30049, 30050, 30051, 30052, 30053, 30054, 30056, 30058)
    assert describe.age('2026-11-25T11:59:30Z', NOW) == 'just now'
    assert describe.age('2026-11-25T11:30:00Z', NOW) == '30 minutes ago'
    assert describe.age('2026-11-25T11:00:00Z', NOW) == '1 hour ago'
    assert describe.age('2026-11-24T12:00:00Z', NOW) == 'yesterday'
    assert describe.age('2026-11-20T12:00:00Z', NOW) == '5 days ago'
    assert describe.age('2026-08-25T12:00:00Z', NOW) == '3 months ago'
    assert describe.age('2023-11-25T12:00:00Z', NOW) == '3 years ago'
    assert describe.age('', NOW) == ''


def test_uptime():
    assert describe.uptime('2026-11-25T11:15:00Z', NOW) == '45m'
    assert describe.uptime('2026-11-25T09:55:00Z', NOW) == '2h 05m'


def test_meta_lines(english):
    english(30039, 30040, 30041, 30042)
    assert describe.meta_line(parser.live(STREAM)) == 'Runner • 42K viewers'
    assert describe.meta_line(parser.channel(USER)) == '12K followers'
    assert describe.meta_line(parser.category(GAME)) == '3.2K viewers'
    assert describe.meta_line(parser.video(VIDEO)).startswith('Runner • 228K views • ')


def test_plots(english):
    english(30040, 30041, 30043, 30044, 30045)
    live = describe.plot(parser.live(STREAM)).split('\n')
    assert live[:2] == ['Runner', 'Playing Celeste']
    assert live[2].startswith('42K viewers • Live for ')
    video = describe.plot(parser.video(VIDEO)).split('\n')
    assert video[2].startswith('Past broadcast • 1:02:05 • 228K views')
