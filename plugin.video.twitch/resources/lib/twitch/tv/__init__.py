# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""The TV interface: Twitch in a full-screen window of its own, built on the plugin's pages and playback."""


def open_window():
    """Write the window's layout for the current skin, then show the window until it is closed."""
    from . import skin
    from .window import TVWindow

    window = TVWindow(skin.XML_NAME, skin.prepare(), 'Default', '1080i')
    window.doModal()
    del window
