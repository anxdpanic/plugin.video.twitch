#-*- encoding: utf-8 -*-
import urllib2
import urllib
import re
from string import Template
try:
    import json
except:
    import simplejson as json

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'

class JSONScraper(object):
    
    def _downloadWebData(self, url,headers = None):
        req = urllib2.Request(url)
        req.add_header(Keys.USER_AGENT, USER_AGENT)
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
        url = ''.join([Urls.STREAMS,Keys.FEATURED])
        items = self.scraper.getJson(url)
        return items[Keys.FEATURED] if items else []
    
    def getGames(self, offset=10, limit=10):
        url = ''.join([Urls.GAMES,Keys.TOP,Urls.OPTIONS_LIMIT_OFFSET.format(limit,offset)])
        items = self.scraper.getJson(url)
        return items[Keys.TOP] if items[Keys.TOP] else []
    
    def getGameStreams(self, gameName, offset = 10, limit = 10):
        options = Urls.OPTIONS_LIMIT_OFFSET_GAME.format(limit, offset, urllib.quote_plus(gameName))
        url = ''.join([Urls.BASE, Keys.STREAMS, options])
        items = self.scraper.getJson(url)
        return items[Keys.STREAMS] if items else []
    
class TwitchVideoResolver(object):

    def getSwfUrl(self, channelName):
        url = TWITCH_SWF_URL + channelName
        headers = {Keys.USER_AGENT: USER_AGENT,
                   Keys.REFERER: Urls.TWITCH.TV + channelName}
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
                return self.bestMatchForChosenQuality(items, maxQuality)[Keys.RTMP_URL]
        return None
    
    def streamIsAccessible(self, stream):
        if not stream.get(Keys.TOKEN) and re.match(PATTERN_IP,stream.get(Keys.CONNECT)):
            #log "skipping quality ${stream.type} because stream has no token and requires one" 
            return False # skip qualities where we get no token (subscription) and stream's a non-cdn server
        return True
    
    
    def getStreamsForChannel(self, channelName):
        scraper = JSONScraper()
        url = TWITCH_API_URL.format(channel = channelName)
        return scraper.getJson(url)
    
    def parseStreamValues(self, stream, swfUrl):#
        streamVars = {Keys.SWF_URL : swfUrl}
        # stream.connect is "rtmp://someip/app", so stream already includes the "app" parameter
        streamVars[Keys.RTMP] = stream[Keys.CONNECT]
        streamVars[Keys.PLAYPATH] = stream.get(Keys.PLAY)
        
        if stream[Keys.TOKEN]:
            jtv = stream[Keys.TOKEN].replace("\"", "\\\"")
            jtv = jtv.replace(" ", "\\\\20")
            expiration = int(re.match(PATTERN_EXPIRATION, stream[Keys.TOKEN]).group(1))
        else:
            jtv = expiration = ""
        streamVars[Keys.JTV_MATCH] = (" jtv=" +jtv) if re.match(PATTERN_IP, streamVars[Keys.RTMP]) else ""
        quality = int(stream.get(Key.VIDEO_HEIGHT,0))
        return {Keys.QUALITY: quality,  Keys.RTMP_URL: Template(FORMAT_RTMP_URL).substitute(streamVars)}
    
    def bestMatchForChosenQuality(self, streams, maxQuality):
        bestStream = streams[0]
        for stream in streams[1:]:
            if bestStream[Keys.QUALITY] < stream[Keys.QUALITY] <= maxQuality:
                bestStream = stream
        return bestStream


class Keys(object):
    '''
    Should not be instantiated, just used to categorize 
    string-constants
    '''
    CONNECT = 'connect'
    FEATURED = 'featured'
    JTV_MATCH = 'jtvMatch'
    PLAY = 'play'
    PLAYPATH = 'playpath'
    QUALITY = 'quality'
    RTMP = 'rtmp'
    STREAMS = 'streams'
    REFERER = 'Referer'
    RTMP_URL = 'rtmpUrl'
    SWF_URL = 'swfUrl'
    TOKEN = 'token'
    TOP = 'top'
    USER_AGENT = 'User-Agent'
    VIDEO_HEIGHT = 'video_height'
                
class Patterns(object):
    '''
    Should not be instantiated, just used to categorize 
    string-constants
    '''
    VALID_FEED = "^https?:\/\/(?:[^\.]*.)?(?:twitch|justin)\.tv\/([a-zA-Z0-9_]+).*$"
    IP = '.*\d+\.\d+\.\d+\.\d+.*'
    EXPIRATION = '.*"expiration": (\d+)[^\d].*'
    
class Urls(object):
    '''
    Should not be instantiated, just used to categorize 
    string-constants
    '''
    TWITCH_TV = 'http://www.twitch.tv/'
    
    BASE = 'https://api.twitch.tv/kraken/'
    GAMES = BASE + 'games/'
    STREAMS = BASE + 'streams/'  
    OPTIONS_LIMIT_OFFSET = '?limit={}&offset={}'
    OPTIONS_LIMIT_OFFSET_GAME = OPTIONS_LIMIT_OFFSET + '&game={}'
    
    TWITCH_API = "http://usher.justin.tv/find/{channel}.json?type=any&group=&channel_subscription="
    TWITCH_SWF = "http://www.justin.tv/widgets/live_embed_player.swf?channel="
    FORMAT_FOR_RTMP = "${rtmp} playpath=${playpath} swfUrl=${swfUrl} swfVfy=1 ${jtvMatch} live=1"