#-*- encoding: utf-8 -*-
import urllib2
import urllib
import re
from string import Template
try:
    import json
except:
    import simplejson as json

httpHeaderUserAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'
BASE_URL = 'https://api.twitch.tv/kraken/'
STREAMS_URL = BASE_URL + 'streams/'  
GAMES_URL = BASE_URL + 'games/'
STREAMS = 'streams'
FEATURED = 'featured'
TOP = 'top'
OPTS_LIMIT_OFFSET = '?limit={}&offset={}'
OPTS_LIMIT_OFFSET_GAME = OPTS_LIMIT_OFFSET + '&game={}'

PATTERN_VALID_FEED = "^https?:\/\/(?:[^\.]*.)?(?:twitch|justin)\.tv\/([a-zA-Z0-9_]+).*$"
PATTERN_IP = '.*\d+\.\d+\.\d+\.\d+.*'
PATTERN_EXPIRATION = '.*"expiration": (\d+)[^\d].*'

TWITCH_API_URL = "http://usher.justin.tv/find/{channel}.json?type=any&group=&channel_subscription="
TWITCH_SWF_URL = "http://www.justin.tv/widgets/live_embed_player.swf?channel="

FORMAT_RTMP_URL = "${rtmp} playpath=${playpath} swfUrl=${swfUrl} swfVfy=1 ${jtvMatch} live=1"


class JSONScraper(object):
    
    def _downloadWebData(self, url,headers = None):
        req = urllib2.Request(url)
        req.add_header('User-Agent', httpHeaderUserAgent)
        response = urllib2.urlopen(req)
        data = response.read()
        response.close()
        return data
    
    def getJson(self, url, headers = None):
        jsonString = self._downloadWebData(url, headers)
        return json.loads(jsonString)
    

class TwitchTV(object):
    
    def __init__(self):
        self.scraper = JSONScraper()

    def getFeaturedStream(self):
        url = ''.join([STREAMS_URL,FEATURED])
        items = self.scraper.getJson(url)
        return items[FEATURED] if items else []
    
    def getGames(self, offset=10, limit=10):
        url = ''.join([GAMES_URL,TOP,OPTS_LIMIT_OFFSET.format(limit,offset)])
        items = self.scraper.getJson(url)
        return items[TOP] if items[TOP] else []
    
    def getGameStreams(self, gameName, offset = 10, limit = 10):
        opts = OPTS_LIMIT_OFFSET_GAME.format(limit, offset, urllib.quote_plus(gameName))
        url = BASE_URL+ STREAMS + opts
        items = self.scraper.getJson(url)
        return items[STREAMS] if items else []
    
class TwitchVideoResolver(object):

    def getSwfUrl(self, channelName):
        url = TWITCH_SWF_URL + channelName
        headers = {'User-agent': httpHeaderUserAgent,
               'Referer': 'http://www.twitch.tv/' + channelName}
        req = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(req)
        return response.geturl()
    
    def getRTMPUrl(self, channelName, maxQuality):
        swfUrl = self.getSwfUrl(channelName)
        streamQualities = self.getStreamsForChannel(channelName)
        if streamQualities: # check that api response isn't empty (i.e. stream is offline)
            items = [self.parseStreamValues(stream, swfUrl) for stream in
                      streamQualities if self.streamIsAccessible(stream)]
            if items:
                return self.bestMatchForChosenQuality(items, maxQuality)['rtmpUrl']
        return None
    
    def streamIsAccessible(self, stream):
        if not stream.get('token') and re.match(PATTERN_IP,stream.get('connect')):
            #log "skipping quality ${stream.type} because stream has no token and requires one" 
            return False # skip qualities where we get no token (subscription) and stream's a non-cdn server
        return True
    
    
    def getStreamsForChannel(self, channelName):
        scraper = JSONScraper()
        url = TWITCH_API_URL.format(channel = channelName)
        return scraper.getJson(url)
    
    def parseStreamValues(self, stream, swfUrl):#
        streamVars = {'swfUrl':swfUrl}
        # stream.connect is "rtmp://someip/app", so stream already includes the "app" parameter
        streamVars['rtmp'] = stream['connect']
        streamVars['playpath'] = stream.get('play')
        
        if stream['token']:
            jtv = stream['token'].replace("\"", "\\\"")
            jtv = jtv.replace(" ", "\\\\20")
            expiration = int(re.match(PATTERN_EXPIRATION, stream['token']).group(1))
        else:
            jtv = expiration = ""
        streamVars['jtvMatch'] = (" jtv=" +jtv) if re.match(PATTERN_IP, streamVars['rtmp']) else ""
        quality = int(stream.get('video_height',0))
        return {'quality': quality,  'rtmpUrl': Template(FORMAT_RTMP_URL).substitute(streamVars)}
    
    def bestMatchForChosenQuality(self, streams, maxQuality):
        bestStream = streams[0]
        for stream in streams[1:]:
            if bestStream['quality'] < stream['quality'] <= maxQuality:
                bestStream = stream
        return bestStream
                