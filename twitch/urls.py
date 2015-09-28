# TODO provide formatting interface for all urls similar to
# https://github.com/ingwinlu/simpleMediaCenter/blob/master/simpleMediaCenter/helpers/youtube/__init__.py

BASE = 'https://api.twitch.tv/kraken/'
FOLLOWED_CHANNELS = BASE + 'users/{0}/follows/channels'
GAMES = BASE + 'games/'
STREAMS = BASE + 'streams/'
SEARCH = BASE + 'search/'
TEAMS = BASE + 'teams?limit=25&offset={0}'

TEAMSTREAM = 'http://api.twitch.tv/api/team/{0}/live_channels.json'
CHANNEL_TOKEN = 'http://api.twitch.tv/api/channels/{0}/access_token'
VOD_TOKEN = 'http://api.twitch.tv/api/vods/{0}/access_token'

OPTIONS_OFFSET_LIMIT = '?offset={0}&limit={1}'
OPTIONS_OFFSET_LIMIT_GAME = OPTIONS_OFFSET_LIMIT + '&game={2}'
OPTIONS_OFFSET_LIMIT_QUERY = OPTIONS_OFFSET_LIMIT + '&q={2}'
OPTIONS_SEARCH_GAMES = '?q={0}&type={1}&live={2}'

HLS_PLAYLIST = ('http://usher.twitch.tv/api/channel/hls/{0}.m3u8?'
                'sig={1}&token={2}&allow_source=true')
VOD_PLAYLIST = 'http://usher.twitch.tv/vod/{0}?nauth={1}&nauthsig={2}'

CHANNEL_VIDEOS = ('https://api.twitch.tv/kraken/channels/{0}/videos?'
                  'limit=8&offset={1}&broadcasts={2}')
VIDEO_PLAYLIST = 'https://api.twitch.tv/api/videos/{0}'
VIDEO_INFO = 'https://api.twitch.tv/kraken/videos/{0}'
FOLLOWED_GAMES = 'https://api.twitch.tv/api/users/{0}/follows/games'
