#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import re
import os
import socket
import urllib
from xbmcswift2 import Plugin, ListItem
from twitch import TwitchTV, TwitchVideoResolver

ITEMS_PER_PAGE = 20
LINE_LENGTH = 60
ELLIPSIS = '...'
plugin = Plugin()
twitch = TwitchTV()

def showNotification(title, msg):
     plugin.notify(msg, title)


def getTitle(streamer, title, viewers):
    plugin.log.error('Debug message')
    stringSeparator = ' - '
    titleDisplaySetting = int(plugin.get_setting('titledisplay'))
    plugin.log.error('Value of titledisplay:' + str(titleDisplaySetting))
    
    streamer = streamer if streamer else '-'
    title = title if title else 'no title'
    viewers = viewers if viewers else '0'

    if titleDisplaySetting == 0:
        titleValues = [streamer, title]
    elif titleDisplaySetting == 1:
        titleValues = [str(viewers), streamer, title]
    elif titleDisplaySetting == 2:
        titleValues = [title]
    else:
        titleValues = [streamer]
    title = stringSeparator.join([cleanTitleValue(value) for value in titleValues])
    return truncateTitle(title)

def cleanTitleValue(value):
    return value.strip().replace('\r\n', ' ')

def truncateTitle(title):
    return title[:LINE_LENGTH] + (title[LINE_LENGTH:] and ELLIPSIS)

@plugin.route('/')
def createMainListing():
    items = [
        {'label': plugin.get_string(30005), 'path': plugin.url_for(
            endpoint = 'createListOfFeaturedStreams'
        )},
        {'label': plugin.get_string(30001), 'path': plugin.url_for(
            endpoint = 'createListOfGames', index = '0'
        )},
        {'label': plugin.get_string(30002), 'path': plugin.url_for(
            endpoint = 'createFollowingList'
        )},
        {'label': plugin.get_string(30006), 'path': plugin.url_for(
            endpoint = 'createListOfTeams', index = '0'
        )},
        {'label': plugin.get_string(30003), 'path': plugin.url_for(
            endpoint = 'search'
        )},
        {'label': plugin.get_string(30004), 'path': plugin.url_for(
            endpoint = 'showSettings'
        )}
    ]
    return items

@plugin.route('/createListOfFeaturedStreams/')
def createListOfFeaturedStreams():
    streams = twitch.getFeaturedStream()
    print "NUMBER OF STREAMS", len(streams)
    return [convertStreamToItem(stream) for stream in streams]

def convertStreamToItem(stream):
    streamData = stream['stream']
    channelData = stream['stream']['channel']
    loginname = channelData['name']
    title = getTitle(streamer = channelData.get('name'), title = channelData.get('status'), viewers = streamData.get('viewers'))
    items = []
    return {'label': title,
                  'path': plugin.url_for(endpoint = 'playLive', name = loginname),
                  'is_playable': True, 
                  'icon' : channelData['logo']}


@plugin.route('/createListOfGames/<index>/')
def createListOfGames(index):
    index = int(index)
    limit = ITEMS_PER_PAGE
    offset = str(index * ITEMS_PER_PAGE)
     
    games = twitch.getGames(offset,limit)
    items = [convertGameToItem(game) for game in games]
    items = [t for t in items if t] #Filter Possible Nonetype Items due to Unicode Errors
    if len(games) >= ITEMS_PER_PAGE: #TODO : pagination occurs even if noOfStreams % ITEMS_PER_PAGE == 0
        items.append({'label': plugin.get_string(31001), 'path': plugin.url_for('createListOfGames', index = str(index + 1))})
    return items

def convertGameToItem(game):
    name = game['game']['name']
    image = game['game']['logo']['large']
    image = ''
    return {'label': name,
           'path': plugin.url_for('createListForGame', gameName = name, index = '0'),
           'icon' : image}

@plugin.route('/createListForGame/<gameName>/<index>/')
def createListForGame(gameName, index):
    index = int(index)
    limit = ITEMS_PER_PAGE
    offset = index * ITEMS_PER_PAGE
    items = [convertGameStreamToItem(gameStream) for gameStream in twitch.getGameStreams(gameName, offset, limit)]
    if len(items) >= ITEMS_PER_PAGE: #TODO: won't always work as expected, no pagination only if <
        items.append({'label': plugin.get_string(31001), 'path': plugin.url_for(
            'createListForGame', gameName = gameName, index = str(index + 1))})
    return items

def convertGameStreamToItem(gameStream):
    channelData = gameStream['channel']
    try:
        image = channelData['logo']
    except:
        image = ""
    title = getTitle(streamer = channelData.get('name'), title = channelData.get('status'), viewers = gameStream.get('viewers'))
    return {'label': title,
            'path': plugin.url_for(endpoint = 'playLive', name = channelData['name']),
            'is_playable' : True,
            'icon' : image}

@plugin.route('/createFollowingList/')
def createFollowingList():
    items = []
    username = plugin.get_setting('username').lower()
    if not username:
        plugin.open_settings()
        username = plugin.get_setting('username').lower()
    jsonData = getJsonFromTwitchApi('http://api.justin.tv/api/user/favorites/' + username + '.json?limit=100&offset=0&live=true')
    if jsonData is None:
        return
    for x in jsonData:
        loginname = x['login']
        image = x['image_url_huge']
        title = getTitle(streamer = x.get('login'), title = x.get('status'), viewers = x.get('views_count'))
        items.append({'label': title , 'path': plugin.url_for(endpoint = 'playLive', name = loginname), 'icon' : image, 'is_playable' : True})
    return items

@plugin.route('/createListOfTeams/')
def createListOfTeams():
    items = []
    jsonData = getJsonFromTwitchApi('https://api.twitch.tv/kraken/teams/')
    if jsonData is None:
        return
    for x in jsonData['teams']:
        try:
            image = x['logo']
        except:
            image = ""
        name = x['name']
        items.append({'label': name, 'path': plugin.url_for(endpoint = 'createListOfTeamStreams', team = name), 'icon' : image})
    return items


@plugin.route('/createListOfTeamStreams/<team>/')
def createListOfTeamStreams(team):
    items = []
    jsonData = getJsonFromTwitchApi(url = 'http://api.twitch.tv/api/team/' + urllib.quote_plus(team) + '/live_channels.json')
    if jsonData is None:
        return
    for x in jsonData['channels']:
        try:
            image = x['channel']['image']['size600']
        except:
            image = ""
        try:
            channelData = x['channel']
            title = getTitle(streamer = channelData.get('display_name'), title = channelData.get('title'), viewers = channelData.get('current_viewers'))
            channelname = x['channel']['name']
            items.append({'label': title, 'path': plugin.url_for(endpoint = 'playLive', name = channelname), 'is_playable' : True, 'icon' : image})
        except:
            # malformed data element
            pass
    return items


@plugin.route('/search/')
def search():
    items = []
    keyboard = xbmc.Keyboard('', plugin.get_string(30101))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = urllib.quote_plus(keyboard.getText())
        sdata = downloadWebData('http://api.swiftype.com/api/v1/public/engines/search.json?callback=jQuery1337&q=' + search_string + '&engine_key=9NXQEpmQPwBEz43TM592&page=1&per_page=' + str(ITEMS_PER_PAGE))
        sdata = sdata.replace('jQuery1337', '')
        sdata = sdata[1:len(sdata) - 1]
        jdata = json.loads(sdata)
        records = jdata['records']['broadcasts']
        for x in records:
            items.append({'label': x['title'], 'path': plugin.url_for(
                endpoint = 'playLive', name = x['user']
            ), 'is_playable' : True})
        return items

@plugin.route('/showSettings/')
def showSettings():
    #there is probably a better way to do this
    plugin.open_settings()


@plugin.route('/playLive/<name>/')
def playLive(name):
    videoQuality = getVideoQuality()
    resolver = TwitchVideoResolver()
    rtmpUrl = resolver.getRTMPUrl(name, videoQuality)
    plugin.set_resolved_url(rtmpUrl)
    
def getVideoQuality():
    chosenQuality = plugin.get_setting('video')
    qualities = {'0':sys.maxint, '1':720, '2':480, '3':360}
    return qualities.get(chosenQuality, 0)

if __name__ == '__main__':
    plugin.run()
