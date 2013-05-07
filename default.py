#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import re
import os
import socket
import urllib
from xbmcswift2 import Plugin, ListItem
from twitch import TwitchTV, TwitchVideoResolver, Keys

class Templates(object):
    TITLE = "{title}"
    STREAMER = "{streamer}"
    STREAMER_TITLE = "{streamer} - {title}"
    VIEWERS_STREAMER_TITLE = "{viewers} - {streamer} - {title}"
    ELLIPSIS = '...'

ITEMS_PER_PAGE = 20
LINE_LENGTH = 60

plugin = Plugin()
twitch = TwitchTV()

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
         'path': plugin.url_for(endpoint = 'createListOfTeams', index = '0')
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
def createListOfFeaturedStreams():
    streams = twitch.getFeaturedStream()
    return [convertChannelToListItem(element[Keys.STREAM][Keys.CHANNEL])
            for element in streams]


@plugin.route('/createListOfGames/<index>/')
def createListOfGames(index):
    index = int(index)
    limit = ITEMS_PER_PAGE
    offset = str(index * ITEMS_PER_PAGE)

    games = twitch.getGames(offset, limit)
    items = [convertGameToListItem(element[Keys.GAME]) for element in games]
    #TODO : pagination occurs even if noOfStreams % ITEMS_PER_PAGE == 0
    if len(games) >= ITEMS_PER_PAGE:
        items.append(linkt_to_next_page('createListOfGames',index))
    return items


@plugin.route('/createListForGame/<gameName>/<index>/')
def createListForGame(gameName, index):
    index = int(index)
    limit = ITEMS_PER_PAGE
    offset = index * ITEMS_PER_PAGE
    items = [convertChannelToListItem(item[Keys.CHANNEL])for item
             in twitch.getGameStreams(gameName, offset, limit)]
    #TODO: won't always work as expected, no pagination only if <
    if len(items) >= ITEMS_PER_PAGE: 
        items.append(link_to_next_page('createListForGame',index))
    return items


@plugin.route('/createFollowingList/')
def createFollowingList():
    items = []
    username = getUserName()
    streams = twitch.getFollowingStreams(username)
    return [convertChannelToListItem(stream[Keys.CHANNEL]) for stream in streams]


@plugin.route('/createListOfTeams/')
def createListOfTeams():
    teams = twitch.getTeams()
    return [convertTeamToItem(team) for team in teams]


@plugin.route('/search/')
def search():
    querystr = plugin.keyboard('', plugin.get_string(30101))
    results = plugin.url_for(endpoint = 'searchresults', query = querystr, index = '0')
    plugin.redirect(results)


@plugin.route('/searchresults/<query>/<index>/')
def searchresults(query, index = '0'):
    index = int(index)
    limit = ITEMS_PER_PAGE
    offset = str(index * ITEMS_PER_PAGE)
    items = [convertGameStreamToItem(gameStream) for gameStream
             in twitch.searchStreams(query, offset, limit)]
    #TODO: won't always work as expected, no pagination only if <
    if len(items) >= ITEMS_PER_PAGE:
        items.append(link_to_next_page('searchresults', index))
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


def getTitle(titleValues):
    titleSetting = int(plugin.get_setting('titledisplay'))
    template = getTitleTemplate(titleSetting)

    for key, value in titleValues.iteritems():
        titleValues[key] = cleanTitleValue(value)
    title = template.format(**titleValues)

    return truncateTitle(title)

def getUserName():
    username = plugin.get_setting('username').lower()
    if not username:
        plugin.open_settings()
        username = plugin.get_setting('username').lower()
    return username


def getVideoQuality():
    chosenQuality = plugin.get_setting('video')
    qualities = {'0':sys.maxint, '1':720, '2':480, '3':360}
    return qualities.get(chosenQuality, 0)


def showNotification(title, msg):
     plugin.notify(msg, title)


def getTitleTemplate(titleSetting):
    options = {0:Templates.STREAMER_TITLE,
               1:Templates.VIEWERS_STREAMER_TITLE,
               2:Templates.TITLE,
               3:Templates.STREAMER}
    return options.get(titleSetting, Templates.STREAMER)


def cleanTitleValue(value):
    if isinstance(value, basestring):
        return unicode(value).replace('\r\n', ' ').strip().encode('utf-8')
    else:
        return value


def truncateTitle(title):
    return title[:LINE_LENGTH] + (title[LINE_LENGTH:] and Template.ELLIPSIS)


def convertChannelToListItem(channel):
    titleValues = extractTitleValues(channel)
    title = getTitle(titleValues)
    channelName = channel[Keys.NAME]
    videobanner = channel.get(Keys.VIDEO_BANNER, '')
    logo = channel.get(Keys.LOGO, '')

    return {
            'label': title,
            'path': plugin.url_for(endpoint = 'playLive', name = channelName),
            'is_playable': True,
            'icon' : videobanner if videobanner else logo
            }


def convertGameToListItem(game):
    name = game[Keys.NAME].encode('utf-8')
    image = game[Keys.LOGO].get(Keys.LARGE, '')
    return {
            'label': name,
            'path': plugin.url_for('createListForGame', gameName = name, index = '0'),
            'icon' : image
            }


def extractTitleValues(channel):
    return {
            'streamer':channel.get(Keys.DISPLAY_NAME, 'Unnamed Streamer'),
            'title': channel.get(Keys.STATUS, 'Untitled Stream'),
            'viewers':channel.get(Keys.VIEWERS, 'Unknown Number of Viewers')
            }
    
def link_to_next_page(target, currentIndex):
    return {
            'label': plugin.get_string(31001),
            'path': plugin.url_for(target, index = currentIndex+1)
            }


if __name__ == '__main__':
    plugin.run()
