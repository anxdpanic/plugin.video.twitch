import unittest

import six

from twitch.queries import ApiQuery, assert_new


class TestQueries(unittest.TestCase):
    def test_assert_new(self):
        d = dict()
        k1 = 'k1'
        v1 = 'v1'

        assert_new(d, k1)
        d[k1] = v1
        
        with six.assertRaisesRegex(
                self,
                ValueError,
                "Key '{}' already set to '{}'".format(k1,v1)):
            assert_new(d, 'k1')

    def test_query_url_replacement(self):
        q = ApiQuery('stream/{channel}')
        with self.assertRaises(KeyError):
            q.url

        q.add_urlkw('channel','winlu')
        self.assertEqual(
                q.url,
                'https://api.twitch.tv/kraken/stream/winlu')
