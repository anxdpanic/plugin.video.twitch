import xbmcgui
from samples import CLIP, USER

from resources.lib.twitch import parser, qr, router, subscribe


def test_address_is_the_channels_subscribe_page():
    assert subscribe.address('Runner') == 'twitch.tv/subs/runner'


def test_without_a_qr_code_the_address_is_shown(monkeypatch, english):
    english(30098, 30099)
    del xbmcgui.OKS[:]
    monkeypatch.setattr(qr, 'image', lambda text: None)
    subscribe.show('runner', 'Runner')
    heading, message = xbmcgui.OKS[0]
    assert heading == 'Subscribe to Runner'
    assert 'twitch.tv/subs/runner' in message


def test_qr_code_is_of_the_full_address(monkeypatch):
    asked = []
    monkeypatch.setattr(qr, 'image', lambda text: asked.append(text))
    subscribe.show('runner', 'Runner')
    assert asked == ['https://www.twitch.tv/subs/runner']


def test_menu_entry_for_channels_and_clips_signed_out(english):
    english(30097)
    for item in (parser.channel(USER), parser.clip(CLIP)):
        menu = dict(router._context_menu(item))
        assert 'subscribe/?login=runner&name=Runner' in menu['Subscribe']
