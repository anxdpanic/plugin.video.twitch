# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 plugin.video.twitch
"""Minimal HTTP client on urllib (no third-party modules on stock Kodi)."""
import gzip
import json
import socket
import urllib.error
import urllib.parse
import urllib.request

from . import kodi


class HTTPError(Exception):
    """A request that didn't succeed: `status` is the HTTP status, or 0 when there was no answer at all."""

    def __init__(self, status, body=b'', url=''):
        Exception.__init__(self, 'HTTP %s' % status)
        self.status = status
        self.body = body
        self.url = url

    def json(self):
        """The error's body as JSON (Twitch explains most refusals there); {} when it isn't JSON."""
        try:
            return json.loads(self.body.decode('utf-8'))
        except ValueError:
            return {}


def _encode(data, headers):
    """A dict body goes as a form, a dict with a 'json' key as that JSON; bytes go as they are."""
    if isinstance(data, dict) and 'json' not in data:
        headers.setdefault('Content-Type', 'application/x-www-form-urlencoded')
        return urllib.parse.urlencode(data).encode('utf-8')
    if isinstance(data, dict):
        headers.setdefault('Content-Type', 'application/json')
        return json.dumps(data['json']).encode('utf-8')
    return data


def _read(resp_or_error):
    """The body of a response (or of an HTTP error), unzipped when the server gzipped it."""
    body = resp_or_error.read() or b''
    if resp_or_error.headers and resp_or_error.headers.get('Content-Encoding') == 'gzip':
        try:
            body = gzip.decompress(body)
        except OSError:
            pass
    return body


def _where(url):
    """The address without its query, for the log (queries hold tokens)."""
    return url.split('?')[0]


def request(url, data=None, headers=None, method=None, timeout=20):
    """Returns (status, body); raises HTTPError (status 0 when there was no response at all)."""
    headers = dict(headers or {})
    headers.setdefault('Accept-Encoding', 'gzip')
    req = urllib.request.Request(url, data=_encode(data, headers), headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, _read(resp)
    except urllib.error.HTTPError as exc:
        kodi.log('HTTP %s for %s' % (exc.code, _where(url)))
        raise HTTPError(exc.code, _read(exc), url) from exc
    except (urllib.error.URLError, socket.timeout, ConnectionError) as exc:
        kodi.log('network error for %s: %s' % (_where(url), exc))
        raise HTTPError(0, b'', url) from exc


def request_json(url, data=None, headers=None, method=None, timeout=20):
    """request(), with the body read as JSON ({} for an empty one)."""
    _, body = request(url, data=data, headers=headers, method=method, timeout=timeout)
    return json.loads(body.decode('utf-8')) if body else {}
