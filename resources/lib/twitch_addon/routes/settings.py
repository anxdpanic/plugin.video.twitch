# -*- coding: utf-8 -*-
from ..addon.common import kodi


def route(refresh=True):
    kodi.show_settings()
    if refresh:
        kodi.refresh_container()
