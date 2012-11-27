import sys
import urllib2
import urllib
import re
import xbmcaddon
import os
import socket
try:
    import json
except:
    import simplejson as json
from xbmcswift2 import Plugin

settings = xbmcaddon.Addon(id='plugin.video.twitch')
httpHeaderUserAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'
translation = settings.getLocalizedString
ITEMS_PER_SITE = 20
plugin = Plugin()


def downloadWebData(url):
    try:
        req = urllib2.Request(url)
        req.add_header('User-Agent', httpHeaderUserAgent)
        response = urllib2.urlopen(req)
        data = response.read()
        response.close()
        return data
    except urllib2.HTTPError, e:
        # HTTP errors usualy contain error information in JSON Format
        return e.fp.read()
    except urllib2.URLError, e:
        showNotification(translation(32001), translation(32010))

def showNotification(caption, text):
     xbmc.executebuiltin("XBMC.Notification(" + caption + "," + text + ")")


def getJsonFromTwitchApi(url):
    jsonString = downloadWebData(url)
    if jsonString is None:
        return None
    try:
        jsonData = json.loads(jsonString)
    except:
        showNotification(translation(32008), translation(32008))
        return None
    if type(jsonData) is dict and 'error' in jsonData.keys():
        showNotification(translation(32007),jsonData['error'])
        return None
    return jsonData


@plugin.route('/')
def createMainListing():
    items = [
        {'label': translation(30005), 'path': plugin.url_for(
            endpoint='createListOfFeaturedStreams'
        )},
        {'label': translation(30001), 'path': plugin.url_for(
            endpoint='createListOfGames', sindex='0'
        )},
        {'label': translation(30002), 'path': plugin.url_for(
            endpoint='createFollowingList'
        )},
        {'label': translation(30006), 'path': plugin.url_for(
            endpoint='createListOfTeams', sindex='0'
        )},
        {'label': translation(30003), 'path': plugin.url_for(
            endpoint='search'
        )},
        {'label': translation(30004), 'path': plugin.url_for(
            endpoint='showSettings'
        )}
    ]
    return items

@plugin.route('/createListOfFeaturedStreams/')
def createListOfFeaturedStreams():
    items = []
    jsonData = getJsonFromTwitchApi(
        url='https://api.twitch.tv/kraken/streams/featured')
    if jsonData is None:
        return
    for x in jsonData['featured']:
        name = x['stream']['channel']['status']
        if name == '':
            name = x['stream']['channel']['display_name']
        channelname = x['stream']['channel']['name']
        items.append({'label': name, 'path': plugin.url_for(endpoint='playLive', name=channelname),
         'is_playable': True, 'icon' : x['stream']['channel']['logo']})
    return items


@plugin.route('/createListOfGames/<sindex>/')
def createListOfGames(sindex):
    index = int(sindex)
    items = []
    jsonData = getJsonFromTwitchApi(url='https://api.twitch.tv/kraken/games/top?limit=' + str(ITEMS_PER_SITE) + '&offset=' + str(index * ITEMS_PER_SITE))
    if jsonData is None:
        return
    for x in jsonData['top']:
        try:
            name = str(x['game']['name'])
        except:
            continue
        try:
            image = x['game']['images']['super']
        except:
            image = ''
        items.append({'label': name, 'path': plugin.url_for(
            'createListForGame', gameName=name, sindex='0'), 'icon' : image})
    if len(jsonData['top']) >= ITEMS_PER_SITE:
        items.append({'label': translation(31001), 'path': plugin.url_for('createListOfGames', sindex=str(index + 1))})
    return items


@plugin.route('/createListForGame/<gameName>/<sindex>/')
def createListForGame(gameName, sindex):
    index = int(sindex)
    items = []
    jsonData = getJsonFromTwitchApi(url='https://api.twitch.tv/kraken/streams?game=' + urllib.quote_plus(gameName) + '&limit=' + str(ITEMS_PER_SITE) + '&offset=' + str(index * ITEMS_PER_SITE))
    if jsonData is None:
        return
    for x in jsonData['streams']:
        try:
            image = x['channel']['logo']
        except:
            image = ""
        name = x['channel']['status']
        if name == '':
            name = x['channel']['display_name']
        items.append({'label': name, 'path': plugin.url_for(endpoint='playLive', name=x['channel']['name']),
                    'is_playable' : True, 'icon' : image})
    if len(jsonData['streams']) >= ITEMS_PER_SITE:
        items.append({'label': translation(31001), 'path': plugin.url_for(
            'createListForGame', gameName=gameName, sindex=str(index + 1))})
    return items


@plugin.route('/createFollowingList/')
def createFollowingList():
    items = []
    username = settings.getSetting('username').lower()
    if not username:
        settings.openSettings()
        username = settings.getSetting('username').lower()
    #Using xml in this case, because it's alot faster than parsing throw the big json result
    xmlDataOnlineStreams = downloadWebData('http://api.justin.tv/api/stream/list.xml')
    jsonData = getJsonFromTwitchApi('http://api.justin.tv/api/user/favorites/' + username + '.json?limit=100')
    if jsonData is None:
        return
    for x in jsonData:
        loginname = x['login']
        if xmlDataOnlineStreams.count('<login>'+loginname+'</login>') > 0:
            name = loginname
            if type(x['status']) is unicode and len(x['status']) > 0:
                name = x['status']
            image = x['image_url_huge']
            items.append({'label': name.strip(), 'path': plugin.url_for(endpoint='playLive', name=loginname), 'icon' : image, 'is_playable' : True})
    return items    

@plugin.route('/createListOfTeams/')
def createListOfTeams():
    #Temporary solution until twitch api method is available
    items = []
    jsonString = downloadWebData(url='https://spreadsheets.google.com/feeds/list/0ArmMFLQnLIp8dFJ5bW9aOW03VHY5aUhsUFNXSUl1SXc/od6/public/basic?alt=json')
    if jsonString is None:
        return
    try:
        jsonData = json.loads(jsonString)
    except:
        showNotification(translation(32008),translation(32008))
        return
    for x in jsonData['feed']['entry']:
        teamData = x['content']['$t'].split(',')
        try:
            image = teamData[1][7:]
        except:
            image = ""
        name = x['title']['$t']
        channelname = teamData[0][7:]
        items.append({'label': name, 'path': plugin.url_for(endpoint='createListOfTeamStreams', team=channelname), 'icon' : image})
    return items


@plugin.route('/createListOfTeamStreams/<team>/')
def createListOfTeamStreams(team):
    items = []
    jsonData = getJsonFromTwitchApi(url='http://api.twitch.tv/api/team/' + urllib.quote_plus(team) + '/live_channels.json')
    if jsonData is None:
        return
    for x in jsonData['channels']:
        try:
            image = x['channel']['image']['size600']
        except:
            image = ""
        if x['channel']['title'] is None:
            name = x['channel']['display_name']
        else:
            name = x['channel']['display_name'] + ' - ' + x['channel']['title']
        channelname = x['channel']['name']
        items.append({'label': name, 'path': plugin.url_for(endpoint='playLive', name=channelname), 'is_playable' : True, 'icon' : image})
    return items


@plugin.route('/search/')
def search():
    items = []
    keyboard = xbmc.Keyboard('', translation(30101))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = urllib.quote_plus(keyboard.getText())
        sdata = downloadWebData('http://api.swiftype.com/api/v1/public/engines/search.json?callback=jQuery1337&q=' + search_string + '&engine_key=9NXQEpmQPwBEz43TM592&page=1&per_page=' + str(ITEMS_PER_SITE))
        sdata = sdata.replace('jQuery1337', '')
        sdata = sdata[1:len(sdata) - 1]
        jdata = json.loads(sdata)
        records = jdata['records']['broadcasts']
        for x in records:
            items.append({'label': x['title'], 'path': plugin.url_for(
                endpoint='playLive', name=x['user']
            ), 'is_playable' : True})
        return items

@plugin.route('/showSettings/')
def showSettings():
    #there is probably a better way to do this
    settings.openSettings()


def getSwfUrl(channel_name):
    # Helper method to grab the swf url
    base_url = 'http://www.justin.tv/widgets/live_embed_player.swf?channel=%s' % channel_name
    headers = {'User-agent': httpHeaderUserAgent,
               'Referer': 'http://www.justin.tv/' + channel_name}
    req = urllib2.Request(base_url, None, headers)
    response = urllib2.urlopen(req)
    return response.geturl()


def getBestJtvTokenPossible(name):
    # Helper method to find another jtv token
    swf_url = getSwfUrl(name)
    headers = {'User-agent': httpHeaderUserAgent,
               'Referer': swf_url}
    url = 'http://usher.justin.tv/find/' + name + '.json?type=any&group='
    data = json.loads(downloadWebData(url))
    bestVideoHeight = -1
    bestIndex = -1
    index = 0
    for x in data:
        value = x.get('token', '')
        videoHeight = int(x['video_height'])
        if (value != '') and (videoHeight > bestVideoHeight):
            bestVideoHeight = x['video_height']
            bestIndex = index
        index = index + 1
    if bestIndex == -1:
        return None
    return data[bestIndex]


@plugin.route('/playLive/<name>/')
def playLive(name):
    swf_url = getSwfUrl(name)
    headers = {'User-agent': httpHeaderUserAgent,
               'Referer': swf_url}
    chosenQuality = settings.getSetting('video')
    videoTypeName = 'any'
    if chosenQuality == '0':
        videoTypeName = 'any'
    elif chosenQuality == '1':
        videoTypeName = '720p'
    elif chosenQuality == '2':
        videoTypeName = '480p'
    elif chosenQuality == '3':
        videoTypeName = '360p'
    url = 'http://usher.justin.tv/find/' + name + '.json?type=' + \
        videoTypeName + '&private_code=null&group='
    data = json.loads(downloadWebData(url))
    tokenIndex = 0

    try:
        # trying to get a token in desired quality
        token = ' jtv=' + data[tokenIndex]['token'].replace(
            '\\', '\\5c').replace(' ', '\\20').replace('"', '\\22')
        rtmp = data[tokenIndex]['connect'] + '/' + data[tokenIndex]['play']
    except:
        showNotification(translation(32005),translation(32006))
        jtvtoken = getBestJtvTokenPossible(name)
        if jtvtoken is None:
            showNotification(translation(31000),translation(32004))
            return
        token = ' jtv=' + jtvtoken['token'].replace('\\', '\\5c').replace(' ', '\\20').replace('"', '\\22')
        rtmp = jtvtoken['connect'] + '/' + jtvtoken['play']

    swf = ' swfUrl=%s swfVfy=1 live=1' % swf_url
    Pageurl = ' Pageurl=http://www.justin.tv/' + name
    url = rtmp + token + swf + Pageurl
    item = {
        'label': name,
        'path': url,
    }
    return plugin.play_video(item)


if __name__ == '__main__':
    plugin.run()
