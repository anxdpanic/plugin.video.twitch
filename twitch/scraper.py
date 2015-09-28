# -*- encoding: utf-8 -*-

import sys

from twitch.exceptions import HttpException, JsonException
from twitch.keys import USER_AGENT, USER_AGENT_STRING
from twitch.logging import log

json = False
try:
    import json
except:
    import simplejson as json  # @UnresolvedImport

if not json:
    raise JsonException()

if sys.version_info < (3, 0):
    PY2 = True
    PY3 = False
else:
    PY2 = False
    PY3 = True

if PY2:
    from urllib import quote_plus  # NOQA
    from urllib2 import Request, urlopen, URLError
elif PY3:
    from urllib.request import urlopen, Request
    from urllib.parse import quote_plus  # NOQA
    from urllib.error import URLError

MAX_RETRIES = 5


def get_json(url):
    '''Download Data from an URL and returns it as JSON
    @param url Url to download from
    @returns JSON Object with data from URL
    '''

    jsonString = download(url)
    try:
        jsonDict = json.loads(jsonString)
        log.debug(json.dumps(jsonDict, indent=4, sort_keys=True))
        return jsonDict
    except:
        raise JsonException()


def download(url):
    '''Download Data from an url and returns it as a String
    @param url Url to download from (e.g. http://www.google.com)
    @returns String of data from URL
    '''
    data = ""
    for _ in range(MAX_RETRIES):
        try:
            req = Request(url)
            req.add_header(USER_AGENT, USER_AGENT_STRING)
            response = urlopen(req)
            if PY2:
                data = response.read()
            elif PY3:
                data = response.readall().decode('utf-8')
            response.close()
            break
        except Exception as err:
            if not isinstance(err, URLError):
                log.debug("Error %s during HTTP Request, abort", repr(err))
                raise  # propagate non-URLError
            log.debug("Error %s during HTTP Request, retrying", repr(err))
    else:
        raise HttpException()
    return data
