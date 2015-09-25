from support import log, unittest
from twitch import *


class TestTwitch(unittest.TestCase):
    twitch = None

    def setUp(self):
        self.twitch = Twitch(log)

    def tearDown(self):
        self.twitch = None

    def test_playback(self):
        featured = self.twitch.getFeaturedStream()
        featured = featured[0]['stream']['channel']['name']
        featuredUrl = self.twitch.getLiveStream(featured, 0)
        self.assertIn('http://',featuredUrl)

    def test_get_channels(self):
        channels = self.twitch.getChannels()
        channels = channels[0]['channel']['name']
        channelsurl = self.twitch.getLiveStream(channels, 0)
        self.assertIn('http://',channelsurl)

    def test_unavailable_channel(self):
        featured = self.twitch.getFeaturedStream()
        featured = featured[0]['stream']['channel']['name'] + "13456789152318561"
        with self.assertRaises(TwitchException) as context:
            self.twitch.getLiveStream(featured, 0)
        self.assertEqual(context.exception.code, TwitchException.HTTP_ERROR)

    def test_offline_channel(self):
        offlinechannel = "winlu"
        with self.assertRaises(TwitchException) as context:
            self.twitch.getLiveStream(offlinechannel, 0)
        self.assertEqual(context.exception.code, TwitchException.STREAM_OFFLINE)

    def test_get_games_streams(self):
        result = self.twitch.getGames(offset=0, limit=10)
        channels = self.twitch.getGameStreams(result[0]['game']['name'], offset=0, limit=10)
        url = self.twitch.getLiveStream(channels[0]['channel']['name'], 0)
        self.assertIn('http://',url)

    def test_get_teams_streams(self):#define fail state
        teams = self.twitch.getTeams(index=0)
        team = teams[0]['name']
        teamstreams = self.twitch.getTeamStreams(team)

    def test_search_streams(self):
        featured = self.twitch.getFeaturedStream()
        featured = featured[0]['stream']['channel']['name']
        result = []
        result = self.twitch.searchStreams(featured,offset=0, limit=10)
        self.assertNotEqual([],result)

    def test_following_channels(self):
        following = []
        following = self.twitch.getFollowingStreams("winlu")
        self.assertNotEqual([],following)

    def test_following_videos(self):
        channelname = "Ellohime"
        following = self.twitch.getFollowerVideos(channelname, offset=0, past=True)
        self.assertTrue(following['_total'] > 0,"total is not bigger then 0")

    def test_followed_games(self):
        expected = [{'box': {'large': 'http://static-cdn.jtvnw.net/ttv-boxart/Counter-Strike:%20Global%20Offensive-272x380.jpg', 'small': 'http://static-cdn.jtvnw.net/ttv-boxart/Counter-Strike:%20Global%20Offensive-52x72.jpg', 'medium': 'http://static-cdn.jtvnw.net/ttv-boxart/Counter-Strike:%20Global%20Offensive-136x190.jpg', 'template': 'http://static-cdn.jtvnw.net/ttv-boxart/Counter-Strike:%20Global%20Offensive-{width}x{height}.jpg'}, 'giantbomb_id': 36113, 'name': 'Counter-Strike: Global Offensive', '_links': {}, 'logo': {'large': 'http://static-cdn.jtvnw.net/ttv-logoart/Counter-Strike:%20Global%20Offensive-240x144.jpg', 'small': 'http://static-cdn.jtvnw.net/ttv-logoart/Counter-Strike:%20Global%20Offensive-60x36.jpg', 'medium': 'http://static-cdn.jtvnw.net/ttv-logoart/Counter-Strike:%20Global%20Offensive-120x72.jpg', 'template': 'http://static-cdn.jtvnw.net/ttv-logoart/Counter-Strike:%20Global%20Offensive-{width}x{height}.jpg'}, '_id': 32399, 'properties': {}}]
        following = []
        following = self.twitch.getFollowingGames("winlu")
        self.assertEqual(expected,following)

    def test_search_games(self):
        gamename = 'Terraria'
        result = self.twitch.searchGames(gamename)
        self.assertNotEqual([], result)

    @unittest.skip("Skip video playlist resolving due to moving urls for now")
    def test_video_playlist_c_chunked(self):
        videoid = 'c5928479'
        '''
        temporary solution, twitch moves the archived flv's to different servers
        expected_playlist = [
            ('', ('', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-613890547-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store24.media78/archives/2015-1-20/live_user_cobaltstreak_1421794812.flv', ('Resident Evil 1 HD Remaster - Part One - Part 1 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-613890547-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store60.media52/archives/2015-1-20/live_user_cobaltstreak_1421796525.flv', ('Resident Evil 1 HD Remaster - Part One - Part 2 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-613890547-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store143.media96/archives/2015-1-20/live_user_cobaltstreak_1421798235.flv', ('Resident Evil 1 HD Remaster - Part One - Part 3 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-613890547-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store57.media71/archives/2015-1-21/live_user_cobaltstreak_1421799946.flv', ('Resident Evil 1 HD Remaster - Part One - Part 4 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-613890547-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store111.media73/archives/2015-1-21/live_user_cobaltstreak_1421801656.flv', ('Resident Evil 1 HD Remaster - Part One - Part 5 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-613890547-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store123.media87/archives/2015-1-21/live_user_cobaltstreak_1421803367.flv', ('Resident Evil 1 HD Remaster - Part One - Part 6 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-613890547-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store130.media90/archives/2015-1-21/live_user_cobaltstreak_1421805077.flv', ('Resident Evil 1 HD Remaster - Part One - Part 7 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-613890547-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store147.media98/archives/2015-1-21/live_user_cobaltstreak_1421806789.flv', ('Resident Evil 1 HD Remaster - Part One - Part 8 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-613890547-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store70.media57/archives/2015-1-21/live_user_cobaltstreak_1421808499.flv', ('Resident Evil 1 HD Remaster - Part One - Part 9 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-613890547-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store161.media105/archives/2015-1-21/live_user_cobaltstreak_1421810210.flv', ('Resident Evil 1 HD Remaster - Part One - Part 10 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-613890547-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store92.media67/archives/2015-1-21/live_user_cobaltstreak_1421811920.flv', ('Resident Evil 1 HD Remaster - Part One - Part 11 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-613890547-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store91.media67/archives/2015-1-21/live_user_cobaltstreak_1421813631.flv', ('Resident Evil 1 HD Remaster - Part One - Part 12 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-613890547-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store82.media62/archives/2015-1-21/live_user_cobaltstreak_1421815341.flv', ('Resident Evil 1 HD Remaster - Part One - Part 13 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-613890547-320x240.jpg'))
        ]
        '''
        playlist = self.twitch.getVideoPlaylist(videoid, 0)
        self.assertEqual(len(playlist), 14)

    @unittest.skip("Skip video playlist resolving due to moving urls for now")
    def test_video_playlist_v_vod(self):
        videoid = 'v3709509'
        playlist = self.twitch.getVideoPlaylist(videoid, 0)
        self.assertIn(('http://vod.ak.hls.ttvnw.net/v1/AUTH_system/vods_1ddc/hutch_12752035712_193039230/chunked/index-dvr.m3u8',()), playlist)

    @unittest.skip("Skip video playlist resolving due to moving urls for now")
    def test_video_playlist_a_archived(self):
        videoid = 'a619273813'
        '''
        temporary solution, twitch moves the archived flv's to different servers
        expected_playlist = [
            ('', ('', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-619273813-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store155.media102/archives/2015-2-1/live_user_cobaltstreak_1422831905.flv', ('Darkest Dungeon - Early Access. Must kill more BOSSES! - Part 1 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-619273813-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store72.media53/archives/2015-2-1/live_user_cobaltstreak_1422833617.flv', ('Darkest Dungeon - Early Access. Must kill more BOSSES! - Part 2 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-619273813-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store47.media47/archives/2015-2-2/live_user_cobaltstreak_1422835329.flv', ('Darkest Dungeon - Early Access. Must kill more BOSSES! - Part 3 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-619273813-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store174.media112/archives/2015-2-2/live_user_cobaltstreak_1422837041.flv', ('Darkest Dungeon - Early Access. Must kill more BOSSES! - Part 4 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-619273813-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store92.media67/archives/2015-2-2/live_user_cobaltstreak_1422838751.flv', ('Darkest Dungeon - Early Access. Must kill more BOSSES! - Part 5 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-619273813-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store143.media96/archives/2015-2-2/live_user_cobaltstreak_1422840461.flv', ('Darkest Dungeon - Early Access. Must kill more BOSSES! - Part 6 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-619273813-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store102.media68/archives/2015-2-2/live_user_cobaltstreak_1422842174.flv', ('Darkest Dungeon - Early Access. Must kill more BOSSES! - Part 7 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-619273813-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store101.media76/archives/2015-2-2/live_user_cobaltstreak_1422843884.flv', ('Darkest Dungeon - Early Access. Must kill more BOSSES! - Part 8 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-619273813-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store165.media107/archives/2015-2-2/live_user_cobaltstreak_1422845595.flv', ('Darkest Dungeon - Early Access. Must kill more BOSSES! - Part 9 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-619273813-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store108.media72/archives/2015-2-2/live_user_cobaltstreak_1422847307.flv', ('Darkest Dungeon - Early Access. Must kill more BOSSES! - Part 10 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-619273813-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store165.media107/archives/2015-2-2/live_user_cobaltstreak_1422849017.flv', ('Darkest Dungeon - Early Access. Must kill more BOSSES! - Part 11 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-619273813-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store107.media70/archives/2015-2-2/live_user_cobaltstreak_1422850728.flv', ('Darkest Dungeon - Early Access. Must kill more BOSSES! - Part 12 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-619273813-320x240.jpg')),
            ('http://media-cdn.twitch.tv/store57.media71/archives/2015-2-2/live_user_cobaltstreak_1422852440.flv', ('Darkest Dungeon - Early Access. Must kill more BOSSES! - Part 13 of 13', 'http://static-cdn.jtvnw.net/jtv.thumbs/archive-619273813-320x240.jpg'))
        ]
        '''
        playlist = self.twitch.getVideoPlaylist(videoid, 0)
        self.assertEqual(len(playlist), 14)

    def suite(self):
        testSuite = unittest.TestSuite()
        testSuite.addTest(unittest.makeSuite(TestResolver))
        return testSuite
