# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""Twitch's GraphQL API (gql.twitch.tv), signed in as the active account when there is one."""
from . import auth, http

URL = 'https://gql.twitch.tv/gql'


class GQLError(Exception):
    pass


def _headers(token):
    headers = {'Client-ID': auth.CLIENT_ID}
    if token:
        headers['Authorization'] = 'OAuth ' + token
    return headers


def _payload(query, variables):
    return {'query': query, 'variables': variables or {}}


def _data(reply):
    """The data of one reply; raises GQLError when it has none (the query itself was refused)."""
    if not isinstance(reply, dict):
        raise GQLError('unexpected reply')
    errors = reply.get('errors') or []
    if reply.get('data') is None:
        raise GQLError('; '.join(e.get('message', '') for e in errors) or 'no data')
    return reply['data']


def _post(body, anonymous=False):
    token = None if anonymous else auth.access_token()
    try:
        return http.request_json(URL, data={'json': body}, headers=_headers(token))
    except http.HTTPError as exc:
        if exc.status == 401 and token:  # see auth.recover_token: kept, refreshed, or signed out
            return http.request_json(URL, data={'json': body}, headers=_headers(auth.recover_token()))
        raise


def query(text, variables=None, anonymous=False):
    """Run one query; returns its data."""
    return _data(_post(_payload(text, variables), anonymous))


def batch(queries, anonymous=False):
    """Run several (text, variables) queries in one request; returns their data in order."""
    if not queries:
        return []
    replies = _post([_payload(text, variables) for text, variables in queries], anonymous)
    if not isinstance(replies, list) or len(replies) != len(queries):
        raise GQLError('unexpected batch reply')
    return [_data(reply) for reply in replies]
