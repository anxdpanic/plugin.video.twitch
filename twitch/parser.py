# -*- encoding: utf-8 -*-
import re

from twitch.logging import log

_m3u_pattern = re.compile(
        r'#EXT-X-MEDIA:.*'
        r'GROUP-ID="(?P<group_id>.\w*)",'
        r'NAME="(?P<group_name>\w*)"[,=\w]*\n'
        r'#EXT-X-STREAM-INF:.*\n('
        r'?P<url>http.*)')


def m3u8(f):
    def m3u8_wrapper(*args, **kwargs):
        return m3u8_to_dict(f(*args, **kwargs))
    return m3u8_wrapper


def m3u8_to_dict(string):
    log.debug('m3u8_to_dict called for:\n{}'.format(string))
    d = dict()
    matches = re.finditer(_m3u_pattern, string)
    for m in matches:
        d[m.group('group_name')] = m.group('url')
    log.debug('m3u8_to_dict result:\n{}'.format(d))
    return d
