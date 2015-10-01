# -*- encoding: utf-8 -*-
import six
from six.moves.urllib.error import URLError
from six.moves.urllib.parse import quote_plus  # NOQA
from six.moves.urllib.parse import urlencode
from six.moves.urllib.request import Request, urlopen

from twitch.keys import USER_AGENT, USER_AGENT_STRING
from twitch.logging import log

try:
    import json
except:
    import simplejson as json  # @UnresolvedImport

MAX_RETRIES = 5


def get_json(baseurl, parameters={}, headers={}):
    '''Download Data from an URL and returns it as JSON
    @param url Url to download from
    @param parameters Parameter dict to be encoded with url
    @param headers Headers dict to pass with Request
    @returns JSON Object with data from URL
    '''
    jsonString = download(baseurl, parameters, headers)
    jsonDict = json.loads(jsonString)
    log.debug(json.dumps(jsonDict, indent=4, sort_keys=True))
    return jsonDict


def download(baseurl, parameters={}, headers={}):
    '''Download Data from an url and returns it as a String
    @param baseurl Url to download from (e.g. http://www.google.com)
    @param parameters Parameter dict to be encoded with url
    @param headers Headers dict to pass with Request
    @returns String of data from URL
    '''
    url = '?'.join([baseurl, urlencode(parameters)])
    log.debug('Downloading: ' + url)
    data = ""
    for _ in range(MAX_RETRIES):
        try:
            req = Request(url, headers=headers)
            req.add_header(USER_AGENT, USER_AGENT_STRING)
            response = urlopen(req)
            if six.PY2:
                data = response.read()
            else:
                data = response.readall().decode('utf-8')
            response.close()
            break
        except Exception as err:
            if not isinstance(err, URLError):
                log.debug("Error %s during HTTP Request, abort", repr(err))
                raise  # propagate non-URLError
            log.debug("Error %s during HTTP Request, retrying", repr(err))
    else:
        raise
    return data
