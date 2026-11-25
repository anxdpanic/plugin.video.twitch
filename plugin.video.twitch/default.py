# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
import sys

from resources.lib.twitch import router

if __name__ == '__main__':
    router.run(sys.argv)
