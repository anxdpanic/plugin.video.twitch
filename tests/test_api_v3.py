import unittest

import six

from twitch.api import v3 as twitch
from twitch.exceptions import ResourceUnavailableException

from . import ci

class TestApiV3Root(unittest.TestCase):

    def test_root(self):
        expected = {
            u'_links': {
                u'channel': u'https://api.twitch.tv/kraken/channel',
                u'ingests': u'https://api.twitch.tv/kraken/ingests',
                u'search': u'https://api.twitch.tv/kraken/search',
                u'streams': u'https://api.twitch.tv/kraken/streams',
                u'teams': u'https://api.twitch.tv/kraken/teams',
                u'user': u'https://api.twitch.tv/kraken/user'
            },
            u'token': {
                u'authorization': None,
                u'valid': False
            }
        }
        self.assertDictEqual(twitch.root(), expected)


class TestApiV3Streams(unittest.TestCase):
    stream_keys = [u'scheduled', u'stream', u'title', u'text',
                   u'image', u'priority', u'sponsored']

    def test_streams(self):
        expected_keys = [u'_total', u'streams', u'_links']
        six.assertCountEqual(
                self,
                twitch.streams.all().keys(),
                expected_keys)

    def test_streams_limit_1(self):
        set_length = 1
        result = twitch.streams.all(limit=set_length)
        length = len(result.get('streams'))
        self.assertEqual(length,set_length)

    def test_featured(self):
        featured = twitch.streams.featured()
        top_featured_keys = featured.get('featured')[0].keys()

        six.assertCountEqual(self, top_featured_keys,self.stream_keys)

    def test_summary(self):
        summary_keys = twitch.streams.summary().keys()
        expected = [u'channels', u'_links', u'viewers']
        six.assertCountEqual(self, summary_keys, expected)

    def test_summary_viewers(self):
        viewers = twitch.streams.summary().get('viewers')
        viewers_dota = twitch.streams.summary(game='Dota 2').get('viewers')
        self.assertLess(viewers_dota, viewers)

    def test_channel_offline(self):
        stream_by_channel = twitch.streams.by_channel('winlu')
        self.assertIsNone(stream_by_channel.get('stream'))
        six.assertCountEqual(self, stream_by_channel.keys(), [u'stream', u'_links'])

    def test_channel_online(self):
        top_ftd = twitch.streams.featured(limit = 1).get('featured')[0]
        self.assertIsNotNone(top_ftd)

        top_ftd_stream = top_ftd.get('stream')
        self.assertIsNotNone(top_ftd_stream)

        top_ftd_stream_chnl = top_ftd_stream.get('channel')
        self.assertIsNotNone(top_ftd_stream_chnl)
        top_ftd_stream_chnl_name = top_ftd_stream_chnl.get('name')
        self.assertIsNotNone(top_ftd_stream_chnl_name)

        by_name = twitch.streams.by_channel(top_ftd_stream_chnl_name).get('stream')

        by_name_crtd_at = by_name.get('created_at')
        top_ftd_stream_crtd_at = by_name.get('created_at')

        self.assertIsNotNone(by_name_crtd_at)
        self.assertIsNotNone(top_ftd_stream_crtd_at)
        self.assertEqual(by_name_crtd_at, top_ftd_stream_crtd_at)


class TestApiV3Users(unittest.TestCase):
    user_keys = [u'bio', u'display_name', u'name', u'created_at',
                 u'updated_at', u'_links', u'logo', u'_id', u'type']

    def test_users(self):
        result = twitch.users.by_name('test_user1').keys()
        six.assertCountEqual(self, result, self.user_keys)

    def test_user(self):
        with self.assertRaises(NotImplementedError):
            twitch.users.user()

    def test_streams(self):
        with self.assertRaises(NotImplementedError):
            twitch.users.streams()

    def test_videos(self):
        with self.assertRaises(NotImplementedError):
            twitch.users.videos()


class TestApiV3Channels(unittest.TestCase):
    channel_keys = [u'updated_at', u'video_banner', u'logo', u'partner',
                    u'display_name', u'delay', u'followers', u'_links',
                    u'broadcaster_language', u'status', u'views', u'game',
                    u'background', u'banner', u'name', u'language', u'url',
                    u'created_at', u'mature',
                    u'profile_banner_background_color', u'_id',
                    u'profile_banner']

    channel_name = 'test_channel'

    def test_by_name(self):
        result = twitch.channels.by_name(self.channel_name).keys()
        for expected_key in self.channel_keys:
            self.assertIn(expected_key, result)

    def test_get_videos(self):
        count = 2
        videos = twitch.channels.get_videos('tornis', limit=count)['videos']
        self.assertEqual(len(videos), count)

    def test_channel_teams(self):
        result = twitch.channels.teams(self.channel_name)
        six.assertCountEqual(self, result, [u'_links', u'teams'])

    def test_channel(self):
        with self.assertRaises(NotImplementedError):
            twitch.channels.channel()

    def test_editors(self):
        with self.assertRaises(NotImplementedError):
            twitch.channels.editors(self.channel_name)

    def test_update(self):
        with self.assertRaises(NotImplementedError):
            twitch.channels.update(self.channel_name)

    def test_commercial(self):
        with self.assertRaises(NotImplementedError):
            twitch.channels.commercial(self.channel_name)


class TestApiV3Videos(unittest.TestCase):
    video_keys = [u'status', u'tag_list', u'description', u'title',
                  u'url', u'views', u'recorded_at', u'length', u'game',
                  u'_links', u'fps', u'broadcast_id', u'broadcast_type',
                  u'preview', u'resolutions', u'_id', u'created_at',
                  u'channel']
    test_video = 'c6055863'

    def test_by_name(self):
        result = twitch.videos.by_id(self.test_video).keys()
        for expected_key in self.video_keys:
            self.assertIn(expected_key, result)

    def test_by_channel(self):
        result = twitch.videos.by_channel('tornis')
        six.assertCountEqual(self, result, [u'_total', u'_links', u'videos'])

        from twitch.api.parameters import Boolean
        result2 = twitch.videos.by_channel('tornis', broadcasts=Boolean.TRUE)

        self.assertNotEqual(result, result2)


class TestApiV3Games(unittest.TestCase):
    game_keys = [u'name', u'box', u'logo', u'_links', u'_id', u'giantbomb_id']

    def test_top(self):
        result = twitch.games.top().get('top')[0].get('game')
        six.assertCountEqual(self, result, self.game_keys)


class TestApiV3Search(unittest.TestCase):

    def test_channels(self):
        result = twitch.search.channels('test_channel').get('channels')[0].keys()
        six.assertCountEqual(self, result, TestApiV3Channels.channel_keys)

    def test_streams(self):
        result = twitch.search.streams('starcraft').get('streams')[0].keys()
        expected =  [u'is_playlist', u'preview', u'created_at',
                     u'video_height', u'game', u'_links', u'channel',
                     u'average_fps', u'_id', u'viewers']
        six.assertCountEqual(self, result, expected)

    def test_games(self):
        result = twitch.search.games('starcraft').get('games')[0].keys()
        six.assertCountEqual(self, result, TestApiV3Games.game_keys + [u'popularity'])


class TestApiV3Follows(unittest.TestCase):

    def test_by_channel(self):
        result = twitch.follows.by_channel('tornis')['follows']
        self.assertEqual(len(result), 25)

    def test_by_user(self):
        def get_self_link(r, n):
            return r['follows'][n]['_links']['self']
        result = twitch.follows.by_user(TestApiV3Channels.channel_name)
        result_rev = twitch.follows.by_user(TestApiV3Channels.channel_name, direction='asc')

        s_l_1 = get_self_link(result, 0)
        s_l_2 = get_self_link(result_rev, 1)
        self.assertEqual(s_l_1, s_l_2)

    def test_status(self):
        def get_channel_from_r(r, n):
            return r['follows'][n]['channel']['name']
        result = twitch.follows.by_user(TestApiV3Channels.channel_name)
        channel_1 = get_channel_from_r(result, 0)

        with self.assertRaises(ResourceUnavailableException):
            twitch.follows.status(TestApiV3Channels.channel_name, channel_1 + 'asffweafwefa')

        with self.assertRaises(ResourceUnavailableException):
            twitch.follows.status(TestApiV3Channels.channel_name + 'asfweaf', channel_1)

        with self.assertRaises(ResourceUnavailableException):
            twitch.follows.status(TestApiV3Channels.channel_name, 'tornis')

        f = twitch.follows.status(TestApiV3Channels.channel_name, channel_1)
        self.assertEqual(f['created_at'], "2010-04-15T05:59:08+00:00")

    def test_follow(self):
        with self.assertRaises(NotImplementedError):
            twitch.follows.follow('a','b')

    def test_unfollow(self):
        with self.assertRaises(NotImplementedError):
            twitch.follows.unfollow('a','b')

    def test_streams(self):
        with self.assertRaises(NotImplementedError):
            twitch.follows.streams()


class TestApiV3Blocks(unittest.TestCase):

    def test_by_name(self):
        with self.assertRaises(NotImplementedError):
            twitch.blocks.by_name('a')

    def test_add_block(self):
        with self.assertRaises(NotImplementedError):
            twitch.blocks.add_block('a', 'b')

    def test_del_block(self):
        with self.assertRaises(NotImplementedError):
            twitch.blocks.del_block('a', 'b')


class TestApiV3Chat(unittest.TestCase):

    def test_channel(self):
        r = twitch.chat.by_channel(TestApiV3Channels.channel_name)
        expected = {
                u'_links': {
                        u'emoticons': u'https://api.twitch.tv/kraken/chat/test_channel/emoticons',
                        u'self': u'https://api.twitch.tv/kraken/chat/test_channel',
                        u'badges': u'https://api.twitch.tv/kraken/chat/test_channel/badges'
                }
        }
        self.assertEqual(r, expected)

    def test_badges(self):
        r1 = twitch.chat.badges(TestApiV3Channels.channel_name)
        r2 = twitch.chat.badges('tornis')
        self.assertNotEqual(r1,r2)

    @unittest.skipIf(ci, "skip on ci since answer is not paginated")
    def test_emoticons(self):
        e = twitch.chat.emoticons()['emoticons']
        self.assertGreaterEqual(len(e), 36306)


class TestApiV3Ingests(unittest.TestCase):

    def test_ingests(self):
        r = twitch.ingests.get()['ingests']
        self.assertGreaterEqual(len(r), 26)


class TestApiV3Subscriptions(unittest.TestCase):

    def test_by_channel(self):
        with self.assertRaises(NotImplementedError):
            twitch.subscriptions.by_channel('a')

    def test_channel_to_user(self):
        with self.assertRaises(NotImplementedError):
            twitch.subscriptions.channel_to_user('a', 'b')

    def test_user_to_channel(self):
        with self.assertRaises(NotImplementedError):
            twitch.subscriptions.user_to_channel('a', 'b')


class TestApiV3Teams(unittest.TestCase):

    team_keys = [u'_id', u'_links', u'background', u'banner', u'created_at',
                 u'display_name', u'info', u'logo', u'name', u'updated_at']

    def test_active(self):
        r = twitch.teams.active(limit=25)['teams']
        for team in r:
            six.assertCountEqual(self, self.team_keys, team.keys())

    def test_by_name(self):
        team_name = 'eg'
        eg = twitch.teams.by_name(team_name)['name']
        self.assertEqual(team_name, eg)
