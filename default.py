# -*- coding: utf-8 -*-
from converter import JsonListItemConverter
from functools import wraps
from twitch import TwitchTV, TwitchVideoResolver, Keys, TwitchException
from xbmcswift2 import Plugin  # @UnresolvedImport
import urllib2, json, sys

ITEMS_PER_PAGE = 20
LINE_LENGTH = 60

PLUGIN = Plugin()
CONVERTER = JsonListItemConverter(PLUGIN, LINE_LENGTH)
TWITCHTV = TwitchTV(PLUGIN.log)


def managedTwitchExceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TwitchException as error:
            handleTwitchException(error)
    return wrapper


def handleTwitchException(exception):
    codeTranslations = {TwitchException.NO_STREAM_URL   : 32004,
                        TwitchException.STREAM_OFFLINE  : 32002,
                        TwitchException.HTTP_ERROR      : 32001,
                        TwitchException.JSON_ERROR      : 32008}
    code = exception.code
    title = 31000
    msg = codeTranslations[code]
    PLUGIN.notify(PLUGIN.get_string(title), PLUGIN.get_string(msg))


@PLUGIN.route('/')
def createMainListing():
    items = [
        {'label': PLUGIN.get_string(30005),
         'path': PLUGIN.url_for(endpoint='createListOfFeaturedStreams')
         },
        {'label': PLUGIN.get_string(30001),
         'path': PLUGIN.url_for(endpoint='createListOfGames', index='0')
         },
        {'label': PLUGIN.get_string(30002),
         'path': PLUGIN.url_for(endpoint='createFollowingList')
         },
        {'label': PLUGIN.get_string(30006),
         'path': PLUGIN.url_for(endpoint='createListOfTeams')
         },
        {'label': PLUGIN.get_string(30003),
         'path': PLUGIN.url_for(endpoint='search')
         },
        {'label': PLUGIN.get_string(30004),
         'path': PLUGIN.url_for(endpoint='showSettings')
         }
    ]
    return items


@PLUGIN.route('/createListOfFeaturedStreams/')
@managedTwitchExceptions
def createListOfFeaturedStreams():
    streams = TWITCHTV.getFeaturedStream()
    return [CONVERTER.convertChannelToListItem(element[Keys.STREAM][Keys.CHANNEL])
            for element in streams]


@PLUGIN.route('/createListOfGames/<index>/')
@managedTwitchExceptions
def createListOfGames(index):
    index, offset, limit = calculatePaginationValues(index)

    games = TWITCHTV.getGames(offset, limit)
    items = [CONVERTER.convertGameToListItem(element[Keys.GAME]) for element in games]

    items.append(linkToNextPage('createListOfGames', index))
    return items


@PLUGIN.route('/createListForGame/<gameName>/<index>/')
@managedTwitchExceptions
def createListForGame(gameName, index):
    index, offset, limit = calculatePaginationValues(index)
    items = [CONVERTER.convertChannelToListItem(item[Keys.CHANNEL])for item
             in TWITCHTV.getGameStreams(gameName, offset, limit)]

    items.append(linkToNextPage('createListForGame', index, gameName=gameName))
    return items


@PLUGIN.route('/createFollowingList/')
@managedTwitchExceptions
def createFollowingList():
    username = getUserName()
    streams = TWITCHTV.getFollowingStreams(username)
    return [CONVERTER.convertChannelToListItem(stream[Keys.CHANNEL]) for stream in streams]


@PLUGIN.route('/search/')
@managedTwitchExceptions
def search():
    query = PLUGIN.keyboard('', PLUGIN.get_string(30101))
    if query:
        target = PLUGIN.url_for(endpoint='searchresults', query=query, index='0')
    else:
        target = PLUGIN.url_for(endpoint='createMainListing')
    PLUGIN.redirect(target)


@PLUGIN.route('/searchresults/<query>/<index>/')
@managedTwitchExceptions
def searchresults(query, index='0'):
    index, offset, limit = calculatePaginationValues(index)
    streams = TWITCHTV.searchStreams(query, offset, limit)

    items = [CONVERTER.convertChannelToListItem(stream[Keys.CHANNEL]) for stream in streams]
    items.append(linkToNextPage('searchresults', index, query=query))
    return items


@PLUGIN.route('/showSettings/')
def showSettings():
    #there is probably a better way to do this
    PLUGIN.open_settings()


@PLUGIN.route('/playLive/<name>/')
@managedTwitchExceptions
def playLive(name):
	
	#Get Required Quality From Settings
	videoQuality = getVideoQuality()
	
	#Get Access Token (not necessary at the moment but could come into effect at any time)
	tokenurl='http://api.twitch.tv/api/channels/' + name + '/access_token'
	readstream = json.loads(urllib2.urlopen(tokenurl).read())
	channeltoken= readstream['token']
	channelsig= readstream['sig']
	
	#Define Stream Playlist URL
	twitchurl = 'http://usher.twitch.tv/select/' + name + '.m3u8?nauthsig=' + channelsig + '&nauth=' + channeltoken + '&allow_source=true'
	
	#Download Multiple Quality Stream Playlist
	req = urllib2.Request(twitchurl)
	req.add_header('user-agent:', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0')
	response = urllib2.urlopen(req)
	data = response.read()
	response.close()
	
	#Split Into Multiple Lines
	streamurls = data.split('\n')
	#Initialize Custom Playlist Var
	playlist='#EXTM3U\n'
	
	#Define Qualities
	quality = 'Source,High,Medium,Low'
	quality = quality.split(',')

	#Loop Through Multiple Quality Stream Playlist Until We Find Our Preferred Quality
	for line in range(0, (len(streamurls)-1)):
		if quality[videoQuality] in streamurls[line]:
			#Add 3 Quality Specific Applicable Lines From Multiple Quality Stream Playlist To Our Custom Playlist Var
			playlist = playlist + streamurls[line] + '\n' + streamurls[(line + 1)] + '\n' + streamurls[(line + 2)]
	
	#Get Temporary Directory For The OS
	plpath = xbmc.translatePath('special://temp') + 'twitchfix.m3u8'
	
	#Write Custom Playlist
	text_file = open(plpath, "w")
	text_file.write(str(playlist))
	text_file.close()
	
	#Play Custom Playlist
	xbmc.Player().play(plpath)
	PLUGIN.set_resolved_url(plpath)


@PLUGIN.route('/createListOfTeams/')
@managedTwitchExceptions
def createListOfTeams():
    items = [CONVERTER.convertTeamToListItem(item)for item in TWITCHTV.getTeams()]
    return items


@PLUGIN.route('/createListOfTeamStreams/<team>/')
@managedTwitchExceptions
def createListOfTeamStreams(team):
    return [CONVERTER.convertTeamChannelToListItem(channel[Keys.CHANNEL])
            for channel in TWITCHTV.getTeamStreams(team)]


def calculatePaginationValues(index):
    index = int(index)
    limit = ITEMS_PER_PAGE
    offset = index * limit
    return  index, offset, limit


def getUserName():
    username = PLUGIN.get_setting('username', unicode).lower()
    if not username:
        PLUGIN.open_settings()
        username = PLUGIN.get_setting('username', unicode).lower()
    return username


def getVideoQuality():
    chosenQuality = PLUGIN.get_setting('video', unicode)
    qualities = {'0': 0, '1': 1, '2': 2, '3': 3}
    return qualities.get(chosenQuality, sys.maxint)


def linkToNextPage(target, currentIndex, **kwargs):
    return {'label': PLUGIN.get_string(31001),
            'path': PLUGIN.url_for(target, index=str(currentIndex + 1), **kwargs)
            }

if __name__ == '__main__':
    PLUGIN.run()
