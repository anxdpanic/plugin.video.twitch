# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""Twitch's Helix API, for the one thing GraphQL refuses the TV app's sign-in: the lists of followed
channels. It answers with logins; the details come from GraphQL."""
import urllib.parse

from . import auth, http

URL = 'https://api.twitch.tv/helix/'


def _headers(token):
    return {'Client-ID': auth.CLIENT_ID, 'Authorization': 'Bearer ' + token}


def get(path, **params):
    """GET a Helix endpoint as the active account; returns the reply."""
    token = auth.access_token()
    if not token:
        raise auth.AuthError('signed out')
    url = URL + path + '?' + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    try:
        return http.request_json(url, headers=_headers(token))
    except http.HTTPError as exc:
        if exc.status != 401:
            raise
        return http.request_json(url, headers=_headers(auth.recover_token()))


def page(path, field, first, after):
    """(values of `field` in the reply's rows, cursor of the next page or None)."""
    reply = get(path, user_id=auth.user_id(), first=first, after=after)
    rows = reply.get('data') or []
    return [row[field] for row in rows if row.get(field)], (reply.get('pagination') or {}).get('cursor') or None
