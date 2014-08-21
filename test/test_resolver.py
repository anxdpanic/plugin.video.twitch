from twitch import *
import unittest
import logging
import os
import timeit

class TestResolver(unittest.TestCase):
    maxDiff = None
    resolver = None
    __playlist=os.path.expanduser('~/.playlist.m3u8')
    
    __preloaded_1 = './riotgamesoceania.m3u8'
    __preloaded_1_data = ''
    
    __result_1_0 = './riotgamesoceania_0.m3u8'
    __result_1_0_data = ''
    
    __result_1_1 = './riotgamesoceania_1.m3u8'
    __result_1_1_data = ''
    
    __preloaded_restricted = './restricted.m3u8'
    __preloaded_restricted_data = ''
    
    __result_restricted_0 = './restricted_0.m3u8' 
    __result_restricted_0_data = ''
    
    __result_restricted_3 = './restricted_3.m3u8' 
    __result_restricted_3_data = ''
    
    __result_restricted_4 = './restricted_4.m3u8' 
    __result_restricted_4_data = ''

    def setUp(self):
        #setup resolver
        self.resolver = TwitchVideoResolver(logging) 
        #load preloaded_1
        with open (self.__preloaded_1, "r") as file:
            self.__preloaded_1_data=file.read()
        with open (self.__result_1_0, "r") as file:
            self.__result_1_0_data=file.read()
        with open (self.__result_1_1, "r") as file:
            self.__result_1_1_data=file.read()
        #load restricted
        with open (self.__preloaded_restricted, "r") as file:
            self.__preloaded_restricted_data=file.read()
        with open (self.__result_restricted_0, "r") as file:
            self.__result_restricted_0_data=file.read()
        with open (self.__result_restricted_3, "r") as file:
            self.__result_restricted_3_data=file.read()
        with open (self.__result_restricted_4, "r") as file:
            self.__result_restricted_4_data=file.read()
        
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
        data=''
        with open (self.__playlist, "r") as playlist:
            data=playlist.read()
        self.assertIn('http://',data)
        
    def test_get_channels(self):
        tTv = TwitchTV(logging)
        channels = tTv.getChannels()
        channels = channels[0]['channel']['name']
        logging.debug("found channel: " + channels)
        self.resolver.saveHLSToPlaylist(channels, 0, self.__playlist)
        data=''
        with open (self.__playlist, "r") as playlist:
            data=playlist.read()
        self.assertIn('http://',data)
        
    def test_playlist_playlist_1_quality_0(self, do_print=False):
        custom_playlist = self.resolver._saveHLSToPlaylist(self.__preloaded_1_data,0)
        if(do_print):
            print()
            print('---------------------------------')
            print(custom_playlist)
            print('---------------------------------')
        self.assertEqual(self.__result_1_0_data,custom_playlist)
            
    def test_playlist_playlist_1_quality_1(self, do_print=False):
        custom_playlist = self.resolver._saveHLSToPlaylist(self.__preloaded_1_data,1)
        if(do_print):
            print()
            print('---------------------------------')
            print(custom_playlist)
            print('---------------------------------')
        self.assertEqual(self.__result_1_1_data,custom_playlist)
        
    def test_playlist_playlist_restricted_0(self, do_print=False):
        custom_playlist = self.resolver._saveHLSToPlaylist(self.__preloaded_restricted_data,0)
        if(do_print):
            print()
            print('---------------------------------')
            print(custom_playlist)
            print('---------------------------------')
        self.assertEqual(self.__result_restricted_0_data,custom_playlist)
        
    def test_playlist_playlist_restricted_3(self, do_print=False):
        custom_playlist = self.resolver._saveHLSToPlaylist(self.__preloaded_restricted_data,3)
        if(do_print):
            print()
            print('---------------------------------')
            print(custom_playlist)
            print('---------------------------------')
        self.assertEqual(self.__result_restricted_3_data,custom_playlist)
        
    def test_playlist_playlist_restricted_4(self, do_print=False):
        custom_playlist = self.resolver._saveHLSToPlaylist(self.__preloaded_restricted_data,4)
        if(do_print):
            print()
            print('---------------------------------')
            print(custom_playlist)
            print('---------------------------------')
        self.assertEqual(self.__result_restricted_4_data,custom_playlist)
        
        
    def test_speed_of_playlist_generator(self):
        #Speedtest Results: 3.674703420998412, on rpi at start
        #Speedtest Results: 1.4243742010003189s, that is 0.0014243742010003188s per loop at 13:17
        #Speedtest Results: 1.5008478810050292s, that is 0.0015008478810050292s per loop at 13:41
        #Speedtest Results: 1.186028003692627s, that is 0.001186028003692627s per loop with python2
        
        loops = 1000
        result = timeit.timeit(lambda: self.test_playlist_playlist_1_quality_0(do_print=False), number=loops)
        print('\nSpeedtest Results: ' + repr(result) + 's, that is ' + repr(result/loops) + 's per loop')
        
        
        
    def suite(self):
        testSuite = unittest.TestSuite()
        testSuite.addTest(unittest.makeSuite(TestResolver))
        return testSuite

