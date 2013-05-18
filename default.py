#!/usr/bin/python
# -*- coding: utf-8 -*-
from twitch import TwitchTV, TwitchVideoResolver, Keys, TwitchException
from xbmcswift2 import Plugin #@UnresolvedImport
import sys
from functools import wraps
from converter import JsonListItemConverter 

ITEMS_PER_PAGE = 20
LINE_LENGTH = 60

plugin = Plugin()
converter = JsonListItemConverter(plugin, LINE_LENGTH)
twitchtv = TwitchTV()


def managedTwitchExceptions(func):
    @wraps(func)
    def wrapper(*args,**kwargs):
        try:
            return func(*args, **kwargs)
        except TwitchException as e:
            handleTwitchException(e)
    return wrapper


def handleTwitchException(exception):
    codeTranslations = {TwitchException.NO_STREAM_URL   : 32004,
                        TwitchException.STREAM_OFFLINE  : 32002,
                        TwitchException.HTTP_ERROR      : 32001,
                        TwitchException.JSON_ERROR      : 32008 }
    code = exception.code
    title = 31000
    msg = codeTranslations[code]
    plugin.notify(plugin.get_string(title), plugin.get_string(msg))


@plugin.route('/')
def createMainListing():
    items = [
        {
         'label': plugin.get_string(30005),
         'path': plugin.url_for(endpoint = 'createListOfFeaturedStreams')
         },
        {
         'label': plugin.get_string(30001),
         'path': plugin.url_for(endpoint = 'createListOfGames', index = '0')
         },
        {
         'label': plugin.get_string(30002),
         'path': plugin.url_for(endpoint = 'createFollowingList')
         },
        {
         'label': plugin.get_string(30006),
         'path': plugin.url_for(endpoint = 'createListOfTeams')
         },
        {
         'label': plugin.get_string(30003),
         'path': plugin.url_for(endpoint = 'search')
         },
        {
         'label': plugin.get_string(30004),
         'path': plugin.url_for(endpoint = 'showSettings')
         }
    ]
    return items


@plugin.route('/createListOfFeaturedStreams/')
@managedTwitchExceptions
def createListOfFeaturedStreams():
    streams = twitchtv.getFeaturedStream()
    return [converter.convertChannelToListItem(element[Keys.STREAM][Keys.CHANNEL])
            for element in streams]


@plugin.route('/createListOfGames/<index>/')
@managedTwitchExceptions
def createListOfGames(index):
    index, offset, limit = calculatePaginationValues(index)

    games = twitchtv.getGames(offset, limit)
    items = [converter.convertGameToListItem(element[Keys.GAME]) for element in games]

    items.append(linkToNextPage('createListOfGames', index))
    return items


@plugin.route('/createListForGame/<gameName>/<index>/')
@managedTwitchExceptions
def createListForGame(gameName, index):
    index, offset, limit = calculatePaginationValues(index)
    items = [converter.convertChannelToListItem(item[Keys.CHANNEL])for item
             in twitchtv.getGameStreams(gameName, offset, limit)]

    items.append(linkToNextPage('createListForGame', index, gameName = gameName))
    return items


@plugin.route('/createFollowingList/')
@managedTwitchExceptions
def createFollowingList():
    username = getUserName()
    streams = twitchtv.getFollowingStreams(username)
    return [converter.convertChannelToListItem(stream[Keys.CHANNEL]) for stream in streams]


@plugin.route('/search/')
@managedTwitchExceptions
def search():
    query = plugin.keyboard('', plugin.get_string(30101))
    if query:
        target = plugin.url_for(endpoint = 'searchresults', query = query, index = '0')
    else:
        target = plugin.url_for(endpoint = 'createMainListing')
    plugin.redirect(target)


@plugin.route('/searchresults/<query>/<index>/')
@managedTwitchExceptions
def searchresults(query, index = '0'):
    index, offset, limit = calculatePaginationValues(index)
    streams = twitchtv.searchStreams(query, offset, limit)
    
    items = [converter.convertChannelToListItem(stream[Keys.CHANNEL]) for stream in streams]
    items.append(linkToNextPage('searchresults', index, query = query))
    return items


@plugin.route('/showSettings/')
def showSettings():
    #there is probably a better way to do this
    plugin.open_settings()


@plugin.route('/playLive/<name>/')
@managedTwitchExceptions
def playLive(name):
    videoQuality = getVideoQuality()
    resolver = TwitchVideoResolver()
    rtmpUrl = resolver.getRTMPUrl(name, videoQuality)
    plugin.set_resolved_url(rtmpUrl)


@plugin.route('/createListOfTeams/')
@managedTwitchExceptions
def createListOfTeams():
    items = [converter.convertTeamToListItem(item)for item in twitchtv.getTeams()]
    return items


@plugin.route('/createListOfTeamStreams/<team>/')
@managedTwitchExceptions
def createListOfTeamStreams(team):
    return [converter.convertTeamChannelToListItem(channel[Keys.CHANNEL]) 
            for channel in twitchtv.getTeamStreams(team)]


def calculatePaginationValues(index):
    index = int(index)
    limit = ITEMS_PER_PAGE
    offset = index * limit
    return  index, offset, limit


def getUserName():
    username = plugin.get_setting('username').lower()
    if not username:
        plugin.open_settings()
        username = plugin.get_setting('username').lower()
    return username


def getVideoQuality():
    chosenQuality = plugin.get_setting('video')
    qualities = {'0':sys.maxint, '1':720, '2':480, '3':360}
    return qualities.get(chosenQuality, sys.maxint)


def linkToNextPage(target, currentIndex, **kwargs):
    return {
            'label': plugin.get_string(31001),
            'path': plugin.url_for(target, index = str(currentIndex+1), **kwargs)
            }

if __name__ == '__main__':
    plugin.run()
