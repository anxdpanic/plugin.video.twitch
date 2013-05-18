#!/usr/bin/python
# -*- coding: utf-8 -*-
from twitch import TwitchTV, TwitchVideoResolver, Keys
from xbmcswift2 import Plugin #@UnresolvedImport
import sys

class Templates(object):
    TITLE = "{title}"
    STREAMER = "{streamer}"
    STREAMER_TITLE = "{streamer} - {title}"
    VIEWERS_STREAMER_TITLE = "{viewers} - {streamer} - {title}"
    ELLIPSIS = '...'

ITEMS_PER_PAGE = 20
LINE_LENGTH = 60

plugin = Plugin()
twitchtv = TwitchTV()
translation = plugin.get_string

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
    streams = twitchtv.getFeaturedStream()
    return [convertChannelToListItem(element[Keys.STREAM][Keys.CHANNEL])
            for element in streams]


@plugin.route('/createListOfGames/<index>/')
def createListOfGames(index):
    index, offset, limit = calculatePaginationValues(index)

    games = twitchtv.getGames(offset, limit)
    items = [convertGameToListItem(element[Keys.GAME]) for element in games]

    items.append(linkToNextPage('createListOfGames', index))
    return items


@plugin.route('/createListForGame/<gameName>/<index>/')
def createListForGame(gameName, index):
    index, offset, limit = calculatePaginationValues(index)
    items = [convertChannelToListItem(item[Keys.CHANNEL])for item
             in twitchtv.getGameStreams(gameName, offset, limit)]

    items.append(linkToNextPage('createListForGame', index, gameName = gameName))
    return items


@plugin.route('/createFollowingList/')
def createFollowingList():
    username = getUserName()
    streams = twitchtv.getFollowingStreams(username)
    return [convertChannelToListItem(stream[Keys.CHANNEL]) for stream in streams]


@plugin.route('/search/')
def search():
    query = plugin.keyboard('', plugin.get_string(30101))
    if query:
        target = plugin.url_for(endpoint = 'searchresults', query = query, index = '0')
    else:
        target = plugin.url_for(endpoint = 'createMainListing')
    plugin.redirect(target)


@plugin.route('/searchresults/<query>/<index>/')
def searchresults(query, index = '0'):
    index, offset, limit = calculatePaginationValues(index)
    streams = twitchtv.searchStreams(query, offset, limit)
    
    items = [convertChannelToListItem(stream[Keys.CHANNEL]) for stream in streams]
    items.append(linkToNextPage('searchresults', index, query = query))
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
    
@plugin.route('/createListOfTeams/<index>/')
def createListOfTeams():
    items = [convertTeamToListItem(item)for item in twitchtv.getTeams()]
    return items

@plugin.route('/createListOfTeamStreams/<team>/')
def createListOfTeamStreams(team):
    return [convertTeamChannelToListItem(channel[Keys.CHANNEL]) 
            for channel in twitchtv.getTeamStreams(team)]

def convertTeamChannelToListItem(teamChannel):
    images = teamChannel.get('image','')
    image = '' if not images else images.get('size600','')

    channelname = teamChannel['name']
    title = formatTitle({'streamer':teamChannel.get('display_name'), 
                        'title':teamChannel.get('title'), 
                        'viewers':teamChannel.get('current_viewers')})
    
    return {'label': title,
            'path': plugin.url_for(endpoint='playLive', name=channelname),
            'is_playable' : True,
            'icon' : image}

def calculatePaginationValues(index):
    index = int(index)
    limit = ITEMS_PER_PAGE
    offset = index * limit
    return  index, offset, limit

def formatTitle(titleValues):
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
    return qualities.get(chosenQuality, sys.maxint)


def showNotification(title, msg):
    plugin.notify(msg, title)


def getTitleTemplate(titleSetting):
    options = {0:Templates.STREAMER_TITLE,
               1:Templates.VIEWERS_STREAMER_TITLE,
               2:Templates.TITLE,
               3:Templates.STREAMER}
    return options.get(titleSetting, Templates.STREAMER)

def extractTitleValues(channel):
    return {
            'streamer':channel.get(Keys.DISPLAY_NAME, 'Unnamed Streamer'),
            'title': channel.get(Keys.STATUS, 'Untitled Stream'),
            'viewers':channel.get(Keys.VIEWERS, 'Unknown Number of Viewers')
            }

def cleanTitleValue(value):
    if isinstance(value, basestring):
        return unicode(value).replace('\r\n', ' ').strip().encode('utf-8')
    else:
        return value


def truncateTitle(title):
    return title[:LINE_LENGTH] + (title[LINE_LENGTH:] and Templates.ELLIPSIS)


def convertChannelToListItem(channel):
    videobanner = channel.get(Keys.VIDEO_BANNER, '')
    logo = channel.get(Keys.LOGO, '')
    return {
            'label': getTitleForChannel(channel),
            'path': plugin.url_for(endpoint = 'playLive', name = channel[Keys.NAME]),
            'is_playable': True,
            'icon' : videobanner if videobanner else logo
            }

def getTitleForChannel(channel):
    titleValues = extractTitleValues(channel)
    return formatTitle(titleValues)
    
def convertGameToListItem(game):
    name = game[Keys.NAME].encode('utf-8')
    image = game[Keys.LOGO].get(Keys.LARGE, '')
    return {
            'label': name,
            'path': plugin.url_for('createListForGame', gameName = name, index = '0'),
            'icon' : image
            }

def convertTeamToListItem(team):
    name = team['name']
    return {
            'label': name,
            'path': plugin.url_for(endpoint='createListOfTeamStreams', team=name),
            'icon' : team.get(Keys.LOGO,'')
            }
    
    
def linkToNextPage(target, currentIndex, **kwargs):
    return {
            'label': plugin.get_string(31001),
            'path': plugin.url_for(target, index = str(currentIndex+1), **kwargs)
            }


if __name__ == '__main__':
    plugin.run()
