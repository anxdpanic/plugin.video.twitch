import shutil

import pytest
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs


@pytest.fixture
def english(monkeypatch):
    """Give the named string ids their en_GB text from strings.po, as Kodi would."""
    def load(*string_ids):
        for string_id in string_ids:
            monkeypatch.setitem(xbmcaddon.STRINGS, string_id, xbmcaddon.english(string_id))
    return load


@pytest.fixture
def no_network(monkeypatch):
    """Fail any request a test didn't stand in for."""
    from resources.lib.twitch import http

    def refuse(url, *args, **kwargs):
        raise AssertionError('unexpected request to %s' % url)
    monkeypatch.setattr(http, 'request', refuse)
    monkeypatch.setattr(http, 'request_json', refuse)


@pytest.fixture
def signed_in():
    """An active account, as a finished sign-in leaves it."""
    from resources.lib.twitch import auth
    auth.add_account({'access_token': 'tok', 'refresh_token': 'ref'}, 'Tester', '42', 'avatar.png')


@pytest.fixture(autouse=True)
def no_skin_font(monkeypatch):
    """No skin to read a font from: nothing is dropped from text (test_fonts sets its own coverage)."""
    from resources.lib.twitch import fonts
    monkeypatch.setattr(fonts, '_current', fonts.Coverage([]))


@pytest.fixture(autouse=True)
def clean_state():
    """Fresh profile, settings and recorded plugin output for every test."""
    shutil.rmtree(xbmcvfs.ROOT, ignore_errors=True)
    xbmcaddon.SETTINGS.clear()
    xbmcplugin.reset()
    del xbmcgui.NOTIFICATIONS[:]
    del xbmc.BUILTINS[:]
    yield
    shutil.rmtree(xbmcvfs.ROOT, ignore_errors=True)
