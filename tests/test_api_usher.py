# -*- encoding: utf-8 -*-
import unittest

import six

from twitch.api import usher
from twitch.api import v3 as twitch
from twitch.exceptions import ResourceUnavailableException


class TestApiUsher(unittest.TestCase):
    possible_qualities = ['Source', 'High', 'Medium', 'Low', 'Mobile']

    def test_live_offline(self):
        with self.assertRaises(ResourceUnavailableException):
            usher.live('test_channel')

    def test_resolve_top_featured(self):
        featured_name = twitch.streams.featured()['featured'][0]['stream']['channel']['name']
        r = usher.live(featured_name)
        self.assertNotEqual(r, {})
        for quality, url in six.iteritems(r):
            self.assertIn(quality, self.possible_qualities)
            self.assertIn('http://', url)

    def test_vod(self):
        top_video_id = twitch.videos.top()['videos'][0]['_id']
        vod = usher._vod(top_video_id)
        self.assertNotEqual(vod, {})
        for quality, url in six.iteritems(vod):
            self.assertIn(quality, self.possible_qualities)
            self.assertIn('http://', url)


# Need nose to run the legacy video generator
legacy_video_mapping = [
    ('a619273813', '/cobaltstreak/b/619273813'),
    ('c5928479', '/cobaltstreak/c/5928479')
]

def test_legacy_videos():
    for id, path in legacy_video_mapping:
        yield check_video, id, path

def check_video(id, expected_path):
    video = usher.video(id)
    video_path = video['path']
    assert video_path == expected_path
