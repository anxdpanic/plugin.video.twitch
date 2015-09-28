# -*- encoding: utf-8 -*-

from twitch import keys as Keys  # TODO improve
from twitch import urls as Urls  # TODO improve
from twitch.exceptions import HttpException, StreamOfflineException
from twitch.logging import log as default_logger
from twitch.parser import M3UPlaylist
from twitch.scraper import download, get_json, quote_plus


# TODO move settings into Twitch class so they can be modified
# TODO on an instance basis

class Twitch(object):
    def __init__(self, logger=default_logger):
        self.log = logger

    def getFeaturedStream(self):
        url = ''.join([Urls.STREAMS, Keys.FEATURED])
        return self._fetchItems(url, Keys.FEATURED)

    def getGames(self, offset=0, limit=10):
        options = Urls.OPTIONS_OFFSET_LIMIT.format(offset, limit)
        url = ''.join([Urls.GAMES, Keys.TOP, options])
        return self._fetchItems(url, Keys.TOP)

    def searchGames(self, query, type='suggest', live=True):
        quotedQuery = quote_plus(query)
        options = Urls.OPTIONS_SEARCH_GAMES.format(quotedQuery, type, live)
        url = ''.join([Urls.SEARCH, Keys.GAMES, options])
        return self._fetchItems(url, Keys.GAMES)

    def getChannels(self, offset=0, limit=10):
        options = Urls.OPTIONS_OFFSET_LIMIT.format(offset, limit)
        url = ''.join([Urls.STREAMS, options])
        return self._fetchItems(url, Keys.STREAMS)

    def getGameStreams(self, gameName, offset=0, limit=10):
        quotedName = quote_plus(gameName)
        options = Urls.OPTIONS_OFFSET_LIMIT_GAME.format(
                offset, limit, quotedName)
        url = ''.join([Urls.BASE, Keys.STREAMS, options])
        return self._fetchItems(url, Keys.STREAMS)

    def searchStreams(self, query, offset=0, limit=10):
        quotedQuery = quote_plus(query)
        options = Urls.OPTIONS_OFFSET_LIMIT_QUERY.format(
                offset, limit, quotedQuery)
        url = ''.join([Urls.SEARCH, Keys.STREAMS, options])
        return self._fetchItems(url, Keys.STREAMS)

    def getFollowingStreams(self, username):
        # Get ChannelNames
        followingChannels = self.getFollowingChannelNames(username)
        channelNames = self._filterChannelNames(followingChannels)

        # get Streams of that Channels
        options = '?channel=' + ','.join(
                [channels[Keys.NAME] for channels in channelNames])
        url = ''.join([Urls.BASE, Keys.STREAMS, options])
        channels = {'live': self._fetchItems(url, Keys.STREAMS)}
        channels['others'] = channelNames
        return channels

    def getFollowingGames(self, username):
        acc = []
        limit = 100
        offset = 0
        quotedUsername = quote_plus(username)
        baseurl = Urls.FOLLOWED_GAMES.format(quotedUsername)
        while True:
            url = baseurl + Urls.OPTIONS_OFFSET_LIMIT.format(offset, limit)
            temp = self._fetchItems(url, Keys.FOLLOWS)
            if (len(temp) == 0):
                break
            acc = acc + temp
            offset = offset + limit
        return acc

    def getFollowerVideos(self, username, offset, past):
        url = Urls.CHANNEL_VIDEOS.format(username, offset, past)
        items = get_json(url)
        return {Keys.TOTAL: items[Keys.TOTAL],
                Keys.VIDEOS: items[Keys.VIDEOS]}

    def getVideoTitle(self, id):
        url = Urls.VIDEO_INFO.format(id)
        return self._fetchItems(url, 'title')

    def __getChunkedVideo(self, id):
        # twitch site queries chunked playlists also with token
        # not necessary yet but might change (similar to vod playlists)
        url = Urls.VIDEO_PLAYLIST.format(id)
        return get_json(url)

    def __getVideoPlaylistChunkedArchived(self, id, maxQuality):
        vidChunks = self.__getChunkedVideo(id)
        chunks = []
        if vidChunks['chunks'].get(Keys.QUALITY_LIST_VIDEO[maxQuality]):
            # prefered quality is not None -> available
            chunks = vidChunks['chunks'][Keys.QUALITY_LIST_VIDEO[maxQuality]]
        else:
            # prefered quality is not available TODO best match
            chunks = vidChunks['chunks'][Keys.QUALITY_LIST_VIDEO[0]]

        title = self.getVideoTitle(id)
        itemTitle = '%s - Part {0} of %s' % (title, len(chunks))

        playlist = [('', ('', vidChunks['preview']))]
        curN = 0
        for chunk in chunks:
            curN += 1
            playlist += [(
                chunk['url'], (
                    itemTitle.format(curN),
                    vidChunks['preview']
                )
            )]

        return playlist

    def __getVideoPlaylistVod(self, id, maxQuality):
        playlist = [('', ())]
        vodid = id[1:]
        url = Urls.VOD_TOKEN.format(vodid)
        access_token = get_json(url)

        playlistQualitiesUrl = Urls.VOD_PLAYLIST.format(
            vodid,
            access_token['token'],
            access_token['sig'])
        playlistQualitiesData = download(playlistQualitiesUrl)
        playlistQualities = M3UPlaylist(playlistQualitiesData)

        vodUrl = playlistQualities.get_quality(maxQuality)
        playlist += [(vodUrl, ())]

        return playlist

    def getVideoPlaylist(self, id, maxQuality):
        playlist = [(), ()]
        if(id.startswith(('a', 'c'))):
            playlist = self.__getVideoPlaylistChunkedArchived(id, maxQuality)
        elif(id.startswith('v')):
            playlist = self.__getVideoPlaylistVod(id, maxQuality)
        return playlist

    def getFollowingChannelNames(self, username):
        acc = []
        limit = 100
        offset = 0
        quotedUsername = quote_plus(username)
        baseurl = Urls.FOLLOWED_CHANNELS.format(quotedUsername)
        while True:
            url = baseurl + Urls.OPTIONS_OFFSET_LIMIT.format(offset, limit)
            temp = self._fetchItems(url, Keys.FOLLOWS)
            if (len(temp) == 0):
                break
            acc = acc + temp
            offset = offset + limit
        return acc

    def getTeams(self, index):
        return self._fetchItems(Urls.TEAMS.format(str(index * 25)), Keys.TEAMS)

    def getTeamStreams(self, teamName):
        '''
        Consider this method to be unstable, because the
        requested resource is not part of the official Twitch API
        '''
        quotedTeamName = quote_plus(teamName)
        url = Urls.TEAMSTREAM.format(quotedTeamName)
        return self._fetchItems(url, Keys.CHANNELS)

    def getLiveStream(self, channelName, maxQuality):
        '''gets playable livestream url'''
        # Get Access Token (not necessary at the moment but could
        # come into effect at any time)
        tokenurl = Urls.CHANNEL_TOKEN.format(channelName)
        channeldata = get_json(tokenurl)
        channeltoken = channeldata['token']
        channelsig = channeldata['sig']

        # Download and Parse Multiple Quality Stream Playlist
        try:
            hls_url = Urls.HLS_PLAYLIST.format(
                    channelName, channelsig, channeltoken)
            data = download(hls_url)
            playlist = M3UPlaylist(data)
            return playlist.get_quality(maxQuality)
        except HttpException:
            # HTTP Error in download web data -> stream is offline
            raise StreamOfflineException()

    def _filterChannelNames(self, channels):
        tmp = [{
            Keys.DISPLAY_NAME: item[Keys.CHANNEL][Keys.DISPLAY_NAME],
            Keys.NAME: item[Keys.CHANNEL][Keys.NAME],
            Keys.LOGO: item[Keys.CHANNEL][Keys.LOGO]
        } for item in channels]
        return sorted(tmp, key=lambda k: k[Keys.DISPLAY_NAME])

    def _fetchItems(self, url, key):
        items = get_json(url)
        return items[key] if items else []
