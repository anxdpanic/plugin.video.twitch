# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""Thin helpers around the Kodi API: settings, strings, paths, logging, JSON storage and a small cache."""
import hashlib
import json
import os
import time

import xbmc
import xbmcaddon
import xbmcvfs

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
PROFILE = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
CACHE_DIR = os.path.join(PROFILE, 'cache')
# Generated files (the TV window's layout, QR codes) live in Kodi's temp folder.
TEMP_DIR = os.path.join(xbmcvfs.translatePath('special://temp/'), ADDON_ID)


def refresh():
    """Read settings and strings afresh from here on. With reuselanguageinvoker on, Kodi keeps this module
    loaded between plugin runs, and an Addon object can go on answering with the settings it read when it
    was made; the TV window calls this after the settings dialog closes."""
    global ADDON
    ADDON = xbmcaddon.Addon(ADDON_ID)


# Logging
def log(msg):
    """Log at debug level, so nothing appears unless Kodi debug logging is on."""
    xbmc.log('[%s] %s' % (ADDON_ID, msg), xbmc.LOGDEBUG)


def log_error(msg):
    """Log a real failure; the only messages written outside debug logging."""
    xbmc.log('[%s] %s' % (ADDON_ID, msg), xbmc.LOGERROR)


# Strings and settings
def string(string_id):
    """The add-on's string in Kodi's language (strings.po)."""
    return ADDON.getLocalizedString(string_id)


def formatted(string_id, *args):
    """A localised string with %-placeholders filled in. A translation whose placeholders don't match the
    arguments is shown as it is, rather than raising inside a dialog or listing."""
    label = string(string_id)
    try:
        return label % args
    except (TypeError, ValueError):
        log('string %d does not fit its arguments: %r' % (string_id, label))
        return label


def setting_bool(key):
    return ADDON.getSettingBool(key)


def setting_int(key):
    """An integer setting; 0 when it isn't set or isn't a number."""
    try:
        return ADDON.getSettingInt(key)
    except (RuntimeError, TypeError):
        return 0


def language_name(code):
    """'en' -> 'English', in English as Kodi names it; the code itself when Kodi doesn't know it."""
    try:
        return xbmc.convertLanguage(code, xbmc.ENGLISH_NAME) or code.upper()
    except (AttributeError, RuntimeError, TypeError):
        return code.upper()


def time_format():
    """Kodi's time format for the region, without seconds: '%H:%M' or '%I:%M %p'."""
    try:
        return xbmc.getRegion('time').replace(':%S', '') or '%H:%M'
    except (AttributeError, RuntimeError):
        return '%H:%M'


# Files in the add-on's profile
def _ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)


def load_json(name, default=None):
    """A JSON file of the add-on's profile; `default` (or {}) when it is missing or broken."""
    path = os.path.join(PROFILE, name)
    try:
        with open(path, encoding='utf-8') as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {} if default is None else default


def save_json(name, data):
    """Write a JSON file of the add-on's profile, through a temporary file so a reader never sees half of it."""
    _ensure_dir(PROFILE)
    path = os.path.join(PROFILE, name)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as handle:
        json.dump(data, handle)
    os.replace(tmp, path)


def prune_dir(path, max_age):
    """Delete the files in a folder older than `max_age` seconds (all of them for a negative age)."""
    if not os.path.isdir(path):
        return
    now = time.time()
    for name in os.listdir(path):
        try:
            if now - os.path.getmtime(os.path.join(path, name)) > max_age:
                os.remove(os.path.join(path, name))
        except OSError:
            pass


class Cache:
    """A small file cache of JSON values by key, each good for the time-to-live the reader asks for (pages
    keep what Twitch answered for a couple of minutes)."""

    @staticmethod
    def _path(key):
        return os.path.join(CACHE_DIR, hashlib.sha1(key.encode('utf-8')).hexdigest() + '.json')

    @classmethod
    def get(cls, key, ttl):
        """The value stored under `key` less than `ttl` seconds ago, or None."""
        path = cls._path(key)
        try:
            if time.time() - os.path.getmtime(path) > ttl:
                return None
            with open(path, encoding='utf-8') as handle:
                return json.load(handle)
        except (OSError, ValueError):
            return None

    @classmethod
    def set(cls, key, value):
        _ensure_dir(CACHE_DIR)
        with open(cls._path(key), 'w', encoding='utf-8') as handle:
            json.dump(value, handle)
