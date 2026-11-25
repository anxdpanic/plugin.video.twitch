from samples import STREAM, USER, USER_STREAM, connection

from resources.lib.twitch import helix, lists


def test_arguments_are_literals():
    query = lists.get('game_streams').query({'name': 'Say "Hi"'}, first=5, after='abc==')
    assert 'game(name:"Say \\"Hi\\"")' in query
    assert 'streams(first:5,after:"abc==",options:{sort:VIEWER_COUNT})' in query


def test_channel_video_type_is_used():
    assert 'type:HIGHLIGHT' in lists.get('channel_videos').query({'login': 'x', 'type': 'HIGHLIGHT'})


def test_read_gives_items_and_next_cursor():
    items, cursor = lists.get('top_streams').read({'streams': connection([STREAM, STREAM], more=True)})
    assert [i['login'] for i in items] == ['runner', 'runner']
    assert cursor == 'c1'
    _, cursor = lists.get('top_streams').read({'streams': connection([STREAM])})
    assert cursor is None


def test_read_of_a_missing_list_is_empty():
    assert lists.get('game_streams').read({'game': None}) == ([], None)


def test_plain_node_lists_have_no_cursor():
    items, cursor = lists.get('followed_games').read(
        {'currentUser': {'followedGames': {'nodes': [{'name': 'Chess', 'displayName': 'Chess'}]}}})
    assert [i['id'] for i in items] == ['Chess'] and cursor is None


def test_channel_live_is_one_item_while_live():
    assert lists.get('channel_live').read({'user': dict(USER, stream=None)}) == ([], None)
    items, _ = lists.get('channel_live').read({'user': dict(USER, stream=USER_STREAM)})
    assert [i['kind'] for i in items] == ['live']


def test_followed_live_keeps_helix_order_and_drops_offline(monkeypatch):
    monkeypatch.setattr(helix, 'page', lambda path, field, first, after: (['b', 'a', 'gone'], 'next'))
    users = [dict(USER, login='a', stream=USER_STREAM), dict(USER, login='b', stream=USER_STREAM),
             dict(USER, login='gone', stream=None)]
    monkeypatch.setattr(lists.gql, 'query', lambda text, variables=None, anonymous=False: {'users': users + [None]})
    items, cursor = lists.get('followed_live').fetch({})
    assert [i['login'] for i in items] == ['b', 'a']
    assert cursor == 'next'


def test_follows_asks_helix_for_broadcasters(monkeypatch):
    asked = []
    monkeypatch.setattr(helix, 'page', lambda path, field, first, after: asked.append((path, field, after)) or
                        ([], None))
    assert lists.get('follows').fetch({}, after='x') == ([], None)
    assert asked == [('channels/followed', 'broadcaster_login', 'x')]
