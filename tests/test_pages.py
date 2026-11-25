from samples import GAME, STREAM, USER, connection

from resources.lib.twitch import gql, lists, pages


def fake_batch(monkeypatch, replies):
    """Answer the page's batch with `replies` (one per query) and record the queries."""
    sent = []

    def batch(queries, anonymous=False):
        sent.extend(text for text, _ in queries)
        return replies[:len(queries)]
    monkeypatch.setattr(gql, 'batch', batch)
    return sent


def test_signed_out_home_leaves_out_followed_channels(monkeypatch, english):
    english(30001, 30011, 30012)
    sent = fake_batch(monkeypatch, [{'streams': connection([STREAM], more=True)}, {'games': connection([GAME])}])
    page = pages.load({'page': 'home'})
    assert page['title'] == 'Home'
    assert [s['title'] for s in page['shelves']] == ['Top live channels', 'Top categories']
    assert page['shelves'][0]['cursor'] == 'c0'
    assert len(sent) == 2


def test_signed_in_home_starts_with_followed_live(monkeypatch, signed_in):
    fake_batch(monkeypatch, [{'streams': connection([STREAM])}, {'games': connection([GAME])}])
    monkeypatch.setattr(lists.FollowedList, 'fetch', lambda self, params, after=None: ([{'id': 'x'}], None))
    shelves = pages.load({'page': 'home'})['shelves']
    assert [s['list'] for s in shelves] == ['followed_live', 'top_streams', 'top_games']


def test_following_signed_out_says_to_sign_in(monkeypatch, english, no_network):
    english(30017)
    page = pages.load({'page': 'following'})
    assert page['shelves'] == []
    assert page['message'] == 'Sign in to see the channels you follow.'


def test_channel_page_has_header_and_drops_empty_shelves(monkeypatch):
    empty = {'user': {'videos': connection([])}}
    replies = [{'user': dict(USER, stream=None)}, empty, empty, empty, {'user': {'clips': connection([])}},
               {'user': USER}]
    sent = fake_batch(monkeypatch, replies)
    page = pages.load({'page': 'channel', 'login': 'runner', 'title': 'Runner'})
    assert page['header']['title'] == 'Runner'
    assert page['title'] == 'Runner'
    assert page['shelves'] == []
    assert 'type:ARCHIVE' in sent[1] and 'type:UPLOAD' in sent[3]


def test_pages_are_cached_briefly(monkeypatch):
    calls = []
    monkeypatch.setattr(gql, 'batch', lambda queries, anonymous=False: calls.append(1) or
                        [{'games': connection([GAME])}])
    pages.load({'page': 'categories'})
    pages.load({'page': 'categories'})
    assert len(calls) == 1


def test_more_stops_when_the_cursor_repeats(monkeypatch):
    monkeypatch.setattr(lists.List, 'fetch', lambda self, params, after=None: ([{'id': 'a'}], after))
    items, cursor = pages.more({'list': 'top_streams', 'params': {}}, 'same')
    assert items == [{'id': 'a'}] and cursor is None


def test_search_history():
    pages.remember_search('chess')
    pages.remember_search('speedrun')
    pages.remember_search('Chess')
    assert pages.searches() == ['Chess', 'speedrun']
    pages.forget_search('speedrun')
    assert pages.searches() == ['Chess']
    pages.clear_searches()
    assert pages.searches() == []
