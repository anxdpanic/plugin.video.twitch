# -*- coding: utf-8 -*-
"""

    Copyright (C) 2016 Twitch-on-Kodi

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
import sys
import routes
from addon.common import kodi
from addon.common import log_utils
from addon.constants import DISPATCHER


def main(argv=None):
    if sys.argv:
        argv = sys.argv
    queries = kodi.parse_query(sys.argv[2])
    log_utils.log('Version: |%s| Kodi Version: %s' % (kodi.get_version(), kodi.get_kodi_version()), log_utils.LOGDEBUG)
    log_utils.log('Queries: |%s| Args: |%s|' % (queries, argv), log_utils.LOGDEBUG)

    # don't process params that don't match our url exactly
    plugin_url = 'plugin://%s/' % kodi.get_id()
    if argv[0] != plugin_url:
        return

    mode = queries.get('mode', None)
    DISPATCHER.dispatch(mode, queries)


if __name__ == '__main__':
    sys.exit(main())
