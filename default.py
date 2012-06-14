import xbmcplugin
import xbmcgui
import sys
import urllib2,urllib,re
import xbmcaddon
import os
import xbmcvfs
try:
    import json
except:
    import simplejson as json
try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

thisPlugin = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.twitch')

def downloadWebData(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	data=response.read()
	response.close()
	return data
	
def createMainListing():
	addDir('Games','','games','')
	addDir('Following','','following','')
	addDir('Settings','','settings','')
	xbmcplugin.endOfDirectory(thisPlugin)
	
def createFollowingList():
	username = settings.getSetting('username').lower()
	if not username:
		settings.openSettings()
		username = settings.getSetting('username').lower()
	link=downloadWebData(url='http://api.justin.tv/api/user/favorites/'+username+'.xml?limit=20&offset=0')
	channels=re.compile('(?<=<channel>).+?(?=</channel>)', re.MULTILINE|re.DOTALL).findall(link)
	onlineStreams = downloadWebData(url='http://api.justin.tv/api/stream/list.xml')
	for x in channels:
		name = re.compile('(?<=<title>).+?(?=</title>)').findall(x)[0]
		image = re.compile('(?<=<image_url_huge>).+?(?=</image_url_huge>)').findall(x)[0]
		loginname = re.compile('(?<=<login>).+?(?=</login>)').findall(x)[0]
		isOnline = onlineStreams.count(loginname) > 0
		if isOnline:
			addLink(name,loginname,'play',image,loginname)
	xbmcplugin.endOfDirectory(thisPlugin)
	
def createChannelListing():
	link=downloadWebData(url='http://de.twitch.tv/directory')
	match=re.compile("(?<=<h5 class='title'>).+?(?=</h5>)", re.MULTILINE|re.DOTALL).findall(link)
	for x in match:
		name = re.compile('(?<=\>).+?(?=</a>)').findall(x)[0]
		dir = re.compile("(?<=<a href=').+?(?='>)").findall(x)[0]
		addDir(name,dir,'channel','')
	xbmcplugin.endOfDirectory(thisPlugin)
	
def createList(url):
	url=url.replace(' ','%20')
	url='http://de.twitch.tv'+url
	link=downloadWebData(url)
	match=re.compile('(?<=<p class=\'title\'>).+?(?=</a></p>)').findall(link)
	for x in match:
		name = re.compile('(?<=\>).+?\Z').findall(x)[0]
		channelname = re.compile('(?<=<a href="/).+?(?=">)').findall(x)[0]
		addLink(name,'...','play','',channelname)
	xbmcplugin.endOfDirectory(thisPlugin)	
	
def addLink(name,url,mode,iconimage,channelname):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&channelname="+channelname
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok
		
def addLiveLink(name,title,url,mode,iconimage,description,showcontext=True):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)
        ok=True
        liz=xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": title, "Plot": description } )
        liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok
		
def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok
		
def get_request(url, headers=None):
        try:
            if headers is None:
                headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
                           'Referer' : 'http://www.justin.tv/'}
            req = urllib2.Request(url,None,headers)
            response = urllib2.urlopen(req)
            link=response.read()
            response.close()
            return link
        except urllib2.URLError, e:
            errorStr = str(e.read())
            if hasattr(e, 'code'):
                if str(e.code) == '403':
                    if 'archive' in url:
                        xbmc.executebuiltin("XBMC.Notification(TwitchTv,No archives found for "+name+",5000,"+ICON+")")
                xbmc.executebuiltin("XBMC.Notification(TwitchTv,HTTP ERROR: "+str(e.code)+",5000,"+ICON+")")

	
def parameters_string_to_dict(parameters):
        ''' Convert parameters encoded in a URL to a dict. '''
        paramDict = {}
        if parameters:
            paramPairs = parameters[1:].split("&")
            for paramsPair in paramPairs:
                paramSplits = paramsPair.split('=')
                if (len(paramSplits)) == 2:
                    paramDict[paramSplits[0]] = paramSplits[1]
        return paramDict
		
def getSwfUrl(channel_name):
        """Helper method to grab the swf url, resolving HTTP 301/302 along the way"""
        base_url = 'http://www.justin.tv/widgets/live_embed_player.swf?channel=%s' % channel_name
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
                   'Referer' : 'http://www.justin.tv/'+channel_name}
        req = urllib2.Request(base_url, None, headers)
        response = urllib2.urlopen(req)
        return response.geturl()		
		
def playLive(name, play=False, password=None):
        swf_url = getSwfUrl(name)
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
                   'Referer' : swf_url}
        url = 'http://usher.justin.tv/find/'+name+'.json?type=live&group='
        data = json.loads(get_request(url,headers))
        if data == []:
            xbmc.executebuiltin("XBMC.Notification(Twitch.tv,No Live Data Not Found)")
            return
        try:
            token = ' jtv='+data[0]['token'].replace('\\','\\5c').replace(' ','\\20').replace('"','\\22')
        except:
            xbmc.executebuiltin("XBMC.Notification(Twitch.tv,User Token Error ,5000,"+ICON+")")
            return
        rtmp = data[0]['connect']+'/'+data[0]['play']
        swf = ' swfUrl=%s swfVfy=1 live=1' % swf_url
        Pageurl = ' Pageurl=http://www.justin.tv/'+name
        url = rtmp+token+swf+Pageurl
        if play == True:
            info = xbmcgui.ListItem(name)
            playlist = xbmc.PlayList(1)
            playlist.clear()
            playlist.add(url, info)
            xbmc.executebuiltin('playlist.playoffset(video,0)')
        else:
            item = xbmcgui.ListItem(path=url)
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
url=params.get('url')
channelname=params.get('channelname')
if type(url)==type(str()):
	url=urllib.unquote_plus(url)
if mode == 'games':
	createChannelListing()  
elif mode == 'channel':
	createList(url)
elif mode == 'play':
	playLive(channelname)
elif mode == 'following':
	createFollowingList()
elif mode == 'settings':
	settings.openSettings()
else:
	createMainListing()

