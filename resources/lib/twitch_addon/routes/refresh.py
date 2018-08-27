# -*- coding: utf-8 -*-
from ..addon import cache
from ..addon.common import kodi


def route():
    do_cache_reset = kodi.get_setting('refresh_cache') == 'true'
    if do_cache_reset:
        result = cache.reset_cache()
    kodi.refresh_container()
