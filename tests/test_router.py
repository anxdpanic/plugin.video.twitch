import json

import xbmcaddon
import xbmcgui
import xbmcplugin
from samples import GAME, STREAM, VIDEO

from resources.lib.twitch import pages, parser, playback, router


def run(url):
    base, _, query = url.partition('?')
    router.run([base, '1', '?' + query if query else ''])


def test_url_for_carries_dicts_as_json():
    url = router.url_for('page', desc={'page': 'channel', 'login': 'x'})
    plugin = router.Plugin([url.split('?')[0], '1', '?' + url.split('?')[1]])
    assert plugin.route == 'page'
    assert plugin.param_json('desc') == {'page': 'channel', 'login': 'x'}


def test_item_urls():
    assert router.item_url(parser.live(STREAM)).endswith('/play/?live=runner')
    assert router.item_url(parser.video(VIDEO)).endswith('/play/?video=2939600059')
    assert '/page/?desc=' in router.item_url(parser.category(GAME))


def test_root_lists_the_menu():
    run(router.url_for(''))
    routes = [url.split('?')[0].replace(router.BASE, '') for url, _, _ in xbmcplugin.ITEMS]
    assert routes == ['tv/', 'search_list/', 'page/', 'page/', 'page/', 'accounts/', 'settings/']


def page_with(shelves):
    return {'title': 'T', 'shelves': shelves, 'header': None, 'message': ''}


def shelf(items, title='S', cursor=None):
    return {'list': 'top_streams', 'params': {}, 'title': title, 'avatars': False, 'items': items, 'cursor': cursor}


def test_single_shelf_page_lists_its_items_and_next_page(monkeypatch):
    monkeypatch.setattr(pages, 'load', lambda desc: page_with([shelf([parser.live(STREAM)], cursor='c1')]))
    run(router.url_for('page', desc={'page': 'categories'}))
    urls = [url for url, _, _ in xbmcplugin.ITEMS]
    assert urls[0].endswith('/play/?live=runner')
    assert 'cursor=c1' in urls[1]
    assert xbmcplugin.ITEMS[0][1].getProperty('IsPlayable') == 'true'


def test_shelves_become_folders_and_a_lone_item_stays_in_place(monkeypatch):
    live = parser.live(STREAM)
    videos = [parser.video(VIDEO), dict(parser.video(VIDEO), id='2')]
    monkeypatch.setattr(pages, 'load', lambda desc: page_with([shelf([live], 'Live now'), shelf(videos, 'Past')]))
    run(router.url_for('page', desc={'page': 'channel', 'login': 'runner'}))
    (live_url, _, live_folder), (shelf_url, shelf_li, shelf_folder) = xbmcplugin.ITEMS
    assert live_url.endswith('live=runner') and not live_folder
    assert '/shelf/' in shelf_url and shelf_folder and shelf_li.label == 'Past'


def test_play_live_resolves_through_inputstream(monkeypatch):
    monkeypatch.setattr(playback, 'live_url', lambda login: 'https://usher/%s.m3u8' % login)
    run(router.url_for('play', live='runner'))
    succeeded, li = xbmcplugin.RESOLVED[0]
    assert succeeded and li.path == 'https://usher/runner.m3u8'
    assert li.getProperty('inputstream') == 'inputstream.adaptive'
    assert li.mime == playback.HLS_MIME


def test_ask_quality_setting(monkeypatch):
    xbmcaddon.SETTINGS['ask_quality'] = True
    monkeypatch.setattr(playback, 'video_url', lambda video_id: 'https://usher/v.m3u8')
    run(router.url_for('play', video='1'))
    assert xbmcplugin.RESOLVED[0][1].getProperty('inputstream.adaptive.stream_selection_type') == 'ask-quality'


def test_failed_playback_tells_kodi_and_the_user(monkeypatch, english):
    english(30072)

    def offline(login):
        raise playback.PlaybackError('offline')
    monkeypatch.setattr(playback, 'live_url', offline)
    run(router.url_for('play', live='runner'))
    assert xbmcplugin.RESOLVED[0][0] is False
    assert "This can't be played: offline" in xbmcgui.NOTIFICATIONS[0][1]


def test_follow_entry_only_while_signed_in(english):
    english(30094)
    live = parser.live(STREAM)
    labels = [label for label, _ in router._context_menu(live)]
    assert 'Follow or unfollow' not in labels


def test_follow_entry_when_signed_in(english, signed_in):
    english(30094)
    menu = dict(router._context_menu(parser.live(STREAM)))
    assert 'follow/?login=runner&name=Runner' in menu['Follow or unfollow']


def test_search_remembers_the_query(monkeypatch):
    loaded = []
    monkeypatch.setattr(pages, 'load', lambda desc: loaded.append(desc) or page_with([]))
    run(router.url_for('search', q='chess'))
    assert loaded == [{'page': 'search', 'q': 'chess'}]
    assert pages.searches() == ['chess']
    assert json.loads(json.dumps(loaded[0]))['q'] == 'chess'
