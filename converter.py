# -*- coding: utf-8 -*-
from twitch import Keys
import xbmcgui, xbmc, uuid

class PlaylistConverter(object):
    def convertToXBMCPlaylist(self, InputPlaylist):
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        for (url, details) in InputPlaylist:
            if(details == ()):
                playlist.add(url)
            else:
                (name, preview) = details
                playlist.add(url, xbmcgui.ListItem(name, thumbnailImage=preview))

        return playlist

class JsonListItemConverter(object):

    def __init__(self, PLUGIN, title_length):
        self.plugin = PLUGIN
        self.titleBuilder = TitleBuilder(PLUGIN, title_length)

    def convertGameToListItem(self, game):
        name = game[Keys.NAME].encode('utf-8')
        if not name:
            name = self.plugin.get_string(30064)
        try:
            image = game[Keys.BOX].get(Keys.LARGE, '')
        except:
            image = 'http://static-cdn.jtvnw.net/ttv-static/404_boxart.jpg'
        return {'label': name,
                'path': self.plugin.url_for('createListForGame',
                                            gameName=name, index='0'),
                'icon': image,
                'thumbnail': image
                }

    def convertTeamToListItem(self, team):
        name = team['name']
        return {'label': name,
                'path': self.plugin.url_for(endpoint='createListOfTeamStreams',
                                            team=name),
                'icon': team.get(Keys.LOGO, ''),
                'thumbnail': team.get(Keys.LOGO, '')
                }

    def convertTeamChannelToListItem(self, teamChannel):
        images = teamChannel.get('image', '')
        image = '' if not images else images.get('size600', '')

        channelname = teamChannel['name']
        titleValues = {'streamer': teamChannel.get('display_name'),
                       'title': teamChannel.get('title'),
                       'viewers': teamChannel.get('current_viewers')}

        title = self.titleBuilder.formatTitle(titleValues)
        return {'label': title,
                'path': self.plugin.url_for(endpoint='playLive', name=channelname),
                'is_playable': True,
                'icon': image,
                'thumbnail': image
                }

    def convertFollowersToListItem(self, follower):
        videobanner = follower.get(Keys.LOGO, '')
        return {'label': follower[Keys.DISPLAY_NAME],
                'path': self.plugin.url_for(endpoint='channelVideos',
                                            name=follower[Keys.NAME]),
                'icon': videobanner,
                'thumbnail': videobanner 
                }

    def convertVideoListToListItem(self,video):
        duration = str(video.get(Keys.LENGTH, ''))
        return {'label': video['title'],
                'path': self.plugin.url_for(endpoint='playVideo',
                                            id=video['_id']),
                'is_playable': True,
                'icon': video.get(Keys.PREVIEW, ''),
                'thumbnail': video.get(Keys.PREVIEW, ''),
                'info': {'duration': duration}
                }

    def convertStreamToListItem(self, stream):
        channel = stream[Keys.CHANNEL]
        videobanner = channel.get(Keys.VIDEO_BANNER, '')
        preview = stream.get(Keys.PREVIEW, '')
        if preview:
            preview = preview.get(Keys.MEDIUM, '') + "?uuid=" + str(uuid.uuid4());
        logo = channel.get(Keys.LOGO, '')
        return {'label': self.getTitleForStream(stream),
                'path': self.plugin.url_for(endpoint='playLive',
                                            name=channel[Keys.NAME]),
                'is_playable': True,
                'icon': preview if preview else logo,
                'thumbnail': preview if preview else logo,
                'properties': {'fanart_image': videobanner}
                }

    def getTitleForStream(self, stream):
        titleValues = self.extractStreamTitleValues(stream)
        return self.titleBuilder.formatTitle(titleValues)

    def extractStreamTitleValues(self, stream):
        channel = stream[Keys.CHANNEL]

        if Keys.VIEWERS in channel:
            viewers = channel.get(Keys.VIEWERS)
        else:
            viewers = stream.get(Keys.VIEWERS, self.plugin.get_string(30062))

        return {'streamer': channel.get(Keys.DISPLAY_NAME,
                                        self.plugin.get_string(30060)),
                'title': channel.get(Keys.STATUS,
                                     self.plugin.get_string(30061)),
                'game': channel.get(Keys.GAME,
                                     self.plugin.get_string(30064)),
                'viewers': viewers}

class TitleBuilder(object):

    class Templates(object):
        TITLE = u"{title}"
        STREAMER = u"{streamer}"
        STREAMER_TITLE = u"{streamer} - {title}"
        VIEWERS_STREAMER_TITLE = u"{viewers} - {streamer} - {title}"
        STREAMER_GAME_TITLE = u"{streamer} - {game} - {title}"
        GAME_VIEWERS_STREAMER_TITLE = u"[{game}] {viewers} | {streamer} - {title}"
        ELLIPSIS = u'...'

    def __init__(self, PLUGIN, line_length):
        self.plugin = PLUGIN
        self.line_length = line_length

    def formatTitle(self, titleValues):
        titleSetting = int(self.plugin.get_setting('titledisplay', unicode))
        template = self.getTitleTemplate(titleSetting)

        for key, value in titleValues.iteritems():
            titleValues[key] = self.cleanTitleValue(value)
        title = template.format(**titleValues)

        return self.truncateTitle(title)

    def getTitleTemplate(self, titleSetting):
        options = {0: TitleBuilder.Templates.STREAMER_TITLE,
                   1: TitleBuilder.Templates.VIEWERS_STREAMER_TITLE,
                   2: TitleBuilder.Templates.TITLE,
                   3: TitleBuilder.Templates.STREAMER,
                   4: TitleBuilder.Templates.STREAMER_GAME_TITLE,
                   5: TitleBuilder.Templates.GAME_VIEWERS_STREAMER_TITLE}
        return options.get(titleSetting, TitleBuilder.Templates.STREAMER)

    def cleanTitleValue(self, value):
        if isinstance(value, basestring):
            return unicode(value).replace('\r\n', ' ').strip()
        else:
            return value

    def truncateTitle(self, title):        
        truncateSetting = self.plugin.get_setting('titletruncate', unicode)

        if truncateSetting == "true":
            shortTitle = title[:self.line_length]
            ending = (title[self.line_length:] and TitleBuilder.Templates.ELLIPSIS)
            return shortTitle + ending
        return title
