#-*- encoding: utf-8 -*-
import urllib2
from urllib import quote_plus
import re
from string import Template
try:
    import json
except:
    import simplejson as json

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'

class JSONScraper(object):

    def _downloadWebData(self, url, headers = None):
        print url
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
        url = ''.join([Urls.STREAMS, Keys.FEATURED])
        return self._fetchItems(url, Keys.FEATURED)

    def getGames(self, offset = 10, limit = 10):
        options = Urls.OPTIONS_LIMIT_OFFSET.format(limit, offset)
        url = ''.join([Urls.GAMES, Keys.TOP, options])
        has
        return self._fetchItems(url, Keys.TOP)

    def getGameStreams(self, gameName, offset = 10, limit = 10):
        quotedName = quote_plus(gameName)
        options = Urls.OPTIONS_LIMIT_OFFSET_GAME.format(limit, offset, quotedName)
        url = ''.join([Urls.BASE, Keys.STREAMS, options])
        return self._fetchItems(url, Keys.STREAMS)

    def searchStreams(self, query, offset = 10, limit = 10):
        quotedQuery = quote_plus(query)
        options = Urls.OPTIONS_LIMIT_OFFSET_QUERY.format(limit, offset, quotedQuery)
        url = ''.join([Urls.SEARCH, Keys.STREAMS, options])
        return self._fetchItems(url, Keys.STREAMS)
    
    def getFollowingStreams(self, username):
        #Get Channels
        followingChannels = self.getFollowingChannels(username)
        channelNames = self._filterChannelNames(followingChannels)
        #get Streams
        options = '?channel=' + ','.join(channelNames)
        url = ''.join([Urls.BASE, Keys.STREAMS, options])
        return self._fetchItems(url, Keys.STREAMS)
        
    def getFollowingChannels(self, username):
        quotedUsername = quote_plus(username)
        url = Urls.FOLLOWED_CHANNELS.format(quotedUsername)
        return self._fetchItems(url, Keys.FOLLOWS)
    
    def _filterChannelNames(self, channels):
        return [item[Keys.CHANNEL][Keys.NAME] for item in channels]
    
    def _fetchItems(self, url, key):
        items = self.scraper.getJson(url)
        return items[key] if items else []
    
    def getTeams(self):
        return self._fetchItems(Urls.TEAMS, Keys.TEAMS)

class TwitchVideoResolver(object):

    def getSwfUrl(self, channelName):
        url = Urls.TWITCH_SWF + channelName
        headers = {Keys.USER_AGENT: USER_AGENT,
                   Keys.REFERER: Urls.TWITCH_TV + channelName}
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
        if not stream[Keys.TOKEN] and re.match(Patterns.IP, stream.get(Keys.CONNECT)):
            #log "skipping quality ${stream.type} because stream has no token and requires one" 
            return False # skip qualities where we get no token (subscription) and stream's a non-cdn server
        return True


    def getStreamsForChannel(self, channelName):
        scraper = JSONScraper()
        url = Urls.TWITCH_API.format(channel = channelName)
        return scraper.getJson(url)

    def parseStreamValues(self, stream, swfUrl):
        streamVars = {Keys.SWF_URL : swfUrl}
        streamVars[Keys.RTMP] = stream[Keys.CONNECT]
        streamVars[Keys.PLAYPATH] = stream.get(Keys.PLAY)

        if stream[Keys.TOKEN]:
            jtv = stream[Keys.TOKEN].replace('\"', '\\\"')
            jtv = jtv.replace(' ', '\\\\20')
            expiration = int(re.match(Patterns.EXPIRATION, stream[Keys.TOKEN]).group(1))
        else:
            jtv = expiration = ''

        streamVars[Keys.JTV_MATCH] = (' jtv=' + jtv) if re.match(Patterns.IP, streamVars[Keys.RTMP]) else ''
        quality = int(stream.get(Keys.VIDEO_HEIGHT, 0))
        return {Keys.QUALITY: quality,
                Keys.RTMP_URL: Urls.FORMAT_FOR_RTMP.format(**streamVars)}

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
    CHANNEL = 'channel'
    CONNECT = 'connect'
    DISPLAY_NAME = 'display_name'
    FEATURED = 'featured'
    FOLLOWS = 'follows'
    GAME = 'game'
    JTV_MATCH = 'jtvMatch'
    LOGO = 'logo'
    LARGE = 'large'
    NAME = 'name'
    PLAY = 'play'
    PLAYPATH = 'playpath'
    QUALITY = 'quality'
    RTMP = 'rtmp'
    STREAMS = 'streams'
    REFERER = 'Referer'
    RTMP_URL = 'rtmpUrl'
    STATUS = 'status'
    STREAM = 'stream'
    SWF_URL = 'swfUrl'
    TEAMS = 'teams'
    TOKEN = 'token'
    TOP = 'top'
    USER_AGENT = 'User-Agent'
    VIDEO_BANNER  = 'video_banner'
    VIDEO_HEIGHT = 'video_height'
    VIEWERS = 'viewers'

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
    FOLLOWED_CHANNELS =  BASE + 'users/{}/follows/channels'
    GAMES = BASE + 'games/'
    STREAMS = BASE + 'streams/'
    SEARCH = BASE + 'search/'
    TEAMS = BASE + 'teams'
    
    OPTIONS_LIMIT_OFFSET = '?limit={}&offset={}'
    OPTIONS_LIMIT_OFFSET_GAME = OPTIONS_LIMIT_OFFSET + '&game={}'
    OPTIONS_LIMIT_OFFSET_QUERY = OPTIONS_LIMIT_OFFSET + '&q={}'

    TWITCH_API = "http://usher.justin.tv/find/{channel}.json?type=any&group=&channel_subscription="
    TWITCH_SWF = "http://www.justin.tv/widgets/live_embed_player.swf?channel="
    FORMAT_FOR_RTMP = "{rtmp} playpath={playpath} swfUrl={swfUrl} swfVfy=1 {jtvMatch} live=1"