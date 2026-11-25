# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""Following and unfollowing channels as the active account."""
import xbmcgui

from . import gql, kodi, lists


def status(login):
    """(channel's user id, whether the account follows it); raises GQLError when there is no such channel."""
    data = gql.query('query{user(login:%s){id self{follower{followedAt}}}}' % lists.literal(login))
    user = data.get('user')
    if not user:
        raise gql.GQLError('no channel %s' % login)
    return user['id'], bool((user.get('self') or {}).get('follower'))


def _forget_pages():
    """The saved pages show the old follows; the next ones are loaded afresh."""
    kodi.prune_dir(kodi.CACHE_DIR, -1)


def follow(user_id):
    data = gql.query('mutation{followUser(input:{targetID:%s,disableNotifications:false})'
                     '{follow{followedAt} error{code}}}' % lists.literal(user_id))
    reply = data.get('followUser') or {}
    if reply.get('error') or not reply.get('follow'):
        raise gql.GQLError('follow refused: %s' % ((reply.get('error') or {}).get('code') or 'no follow'))
    _forget_pages()


def unfollow(user_id):
    data = gql.query('mutation{unfollowUser(input:{targetID:%s}){follow{followedAt}}}' % lists.literal(user_id))
    if data.get('unfollowUser') is None:
        raise gql.GQLError('unfollow refused')
    _forget_pages()


def _notify(message):
    xbmcgui.Dialog().notification(kodi.ADDON.getAddonInfo('name'), message, xbmcgui.NOTIFICATION_INFO, 3000)


def change(user_id, following, name):
    """Unfollow a followed channel, follow another; tells the user. Returns whether it is followed now."""
    if following:
        unfollow(user_id)
        _notify(kodi.formatted(30093, name))
        return False
    follow(user_id)
    _notify(kodi.formatted(30092, name))
    return True


def ask_and_change(login, name):
    """For a menu entry that can't know beforehand: look up the follow, ask, then change it.
    True when it changed."""
    user_id, following = status(login)
    if not xbmcgui.Dialog().yesno(kodi.string(30094), kodi.formatted(30096 if following else 30095, name)):
        return False
    change(user_id, following, name)
    return True
