import os

import pytest
import xbmcgui

from resources.lib.twitch import follows, gql, kodi


@pytest.fixture
def replies(monkeypatch):
    """Answer queries in order from the list the test fills, recording the queries."""
    answers, sent = [], []

    def query(text, variables=None, anonymous=False):
        sent.append(text)
        return answers.pop(0)
    monkeypatch.setattr(gql, 'query', query)
    return answers, sent


def test_status(replies):
    answers, sent = replies
    answers.append({'user': {'id': '7', 'self': {'follower': {'followedAt': '2026-11-25T00:00:00Z'}}}})
    assert follows.status('runner') == ('7', True)
    assert 'user(login:"runner")' in sent[0]
    answers.append({'user': {'id': '7', 'self': {'follower': None}}})
    assert follows.status('runner') == ('7', False)


def test_status_of_a_missing_channel(replies):
    replies[0].append({'user': None})
    with pytest.raises(gql.GQLError):
        follows.status('nobody')


def test_follow_forgets_saved_pages(replies):
    answers, sent = replies
    kodi.Cache.set('page', {'x': 1})
    answers.append({'followUser': {'follow': {'followedAt': 'now'}, 'error': None}})
    follows.follow('7')
    assert 'followUser(input:{targetID:"7"' in sent[0]
    assert not os.listdir(kodi.CACHE_DIR)


def test_refused_follow(replies):
    replies[0].append({'followUser': {'follow': None, 'error': {'code': 'TOO_MANY_FOLLOWS'}}})
    with pytest.raises(gql.GQLError, match='TOO_MANY_FOLLOWS'):
        follows.follow('7')


def test_change_unfollows_a_followed_channel(replies, english):
    english(30093)
    answers, sent = replies
    answers.append({'unfollowUser': {'follow': {'followedAt': 'then'}}})
    assert follows.change('7', True, 'Runner') is False
    assert 'unfollowUser' in sent[0]
    assert xbmcgui.NOTIFICATIONS[0][1] == 'Unfollowed Runner'


def test_ask_and_change_does_nothing_when_declined(replies, monkeypatch):
    answers, sent = replies
    answers.append({'user': {'id': '7', 'self': {'follower': None}}})
    monkeypatch.setattr(xbmcgui.Dialog, 'yesno', lambda self, heading, message, **kw: False)
    assert follows.ask_and_change('runner', 'Runner') is False
    assert len(sent) == 1
