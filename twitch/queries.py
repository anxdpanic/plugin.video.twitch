# -*- encoding: utf-8 -*-

from six.moves.urllib.parse import urljoin

from twitch.exceptions import ResourceUnavailableException
from twitch.logging import log
from twitch.scraper import download, get_json

_api_baseurl = 'https://api.twitch.tv/kraken/'
_hidden_api_baseurl = 'http://api.twitch.tv/api/'
_usher_baseurl = 'http://usher.twitch.tv/'

_v2_headers = {'ACCEPT': 'application/vnd.twitchtv.v2+json'}
_v3_headers = {'ACCEPT': 'application/vnd.twitchtv.v3+json'}


class _Query(object):
    def __init__(self, url, headers={}):
        self._headers = headers
        self._url = url

        self._params = dict()
        self._urlkws = dict()

    @property
    def url(self):
        formatted_url = self._url.format(**self._urlkws)  # throws KeyError
        return formatted_url

    @property
    def headers(self):
        return self._headers

    @property
    def params(self):
        return self._params

    @property
    def urlkws(self):
        return self._urlkws

    def add_path(self, path):
        self._url = urljoin(self._url, path)
        return self

    def add_param(self, key, value, default=None):
        assert_new(self._params, key)
        if value != default:
            self._params[key] = value
        return self

    def add_urlkw(self, kw, replacement):
        assert_new(self._urlkws, kw)
        self._urlkws[kw] = replacement
        return self

    def __str__(self):
        return 'Query to {url}, params {params}, headers {headers}'.format(
                url=self.url, params=self.params, headers=self.headers)

    def execute(self, f):
        try:
            return f(self.url, self.params, self.headers)
        except:
            raise ResourceUnavailableException(str(self))


class DownloadQuery(_Query):
    def execute(self):
        # TODO implement download completly here
        return super(DownloadQuery, self).execute(download)


class JsonQuery(_Query):
    def execute(self):
        # TODO implement get_json completly here
        return super(JsonQuery, self).execute(get_json)


class ApiQuery(JsonQuery):
    def __init__(self, path, headers={}):
        super(ApiQuery, self).__init__(_api_baseurl, headers)
        self.add_path(path)


class HiddenApiQuery(JsonQuery):
    def __init__(self, path, headers={}):
        super(HiddenApiQuery, self).__init__(_hidden_api_baseurl, headers)
        self.add_path(path)


class UsherQuery(DownloadQuery):
    def __init__(self, path, headers={}):
        super(UsherQuery, self).__init__(_usher_baseurl, headers)
        self.add_path(path)


class V3Query(ApiQuery):
    def __init__(self, path):
        super(V3Query, self).__init__(path, _v3_headers)


class V2Query(ApiQuery):
    def __init__(self, path):
        super(V2Query, self).__init__(path, _v2_headers)


def assert_new(d, k):
    if k in d:
        v = d.get(k)
        raise ValueError("Key '{}' already set to '{}'".format(
                         k, v))


# TODO maybe rename
def query(f):
    def wrapper(*args, **kwargs):
        qry = f(*args, **kwargs)
        if not isinstance(qry, _Query):
            raise ValueError('{} did not return a Query, was: {}'.format(
                             f.__name__, repr(qry)))
        log.debug('QUERY: url: %s, params: %s, '
                  'headers: %r, target_func: %r',
                  qry.url, qry.params, qry.headers, f.__name__)
        return qry.execute()
    return wrapper
