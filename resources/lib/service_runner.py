# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'twitch_addon'))

from twitch_addon.addon import utils
from twitch_addon import service

# Set proxy environment variables as early as possible
try:
    proxy_config = utils.get_proxy_dict()
    if proxy_config:
        os.environ['HTTP_PROXY'] = proxy_config['http']
        os.environ['HTTPS_PROXY'] = proxy_config['https']
        os.environ['http_proxy'] = proxy_config['http']  # lowercase versions
        os.environ['https_proxy'] = proxy_config['https']
except:
    pass

service.run()
