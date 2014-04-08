from twitch import *
import unittest
import logging
import os

class TestResolver(unittest.TestCase):
    resolver = None
    __playlist=os.path.expanduser('~/.playlist.m3u8')

    def setUp(self):
        self.resolver = TwitchVideoResolver(logging) 
        pass
        
    def tearDown(self):
        self.resolver = None
        if (os.path.isfile(self.__playlist)):
            os.remove(self.__playlist)
        
        
    def test_playlist(self):
        tTv = TwitchTV(logging)
        featured = tTv.getFeaturedStream()
        featured = featured[0]['stream']['channel']['name']
        logging.debug("found featured stream: " + featured)
        self.resolver.saveHLSToPlaylist(featured, 0, self.__playlist)
        #insert asserts
        
        
    def suite(self):
        testSuite = unittest.TestSuite()
        testSuite.addTest(unittest.makeSuite(TestResolver))
        return testSuite
        
        
        
