from twitch import *
import unittest
import logging
import os

class TestJsonScraper(unittest.TestCase):
    scraper=None
    badurl1='asdffdsaa'
    badurl2='www.google.com'
    goodurl='http://www.google.com'
    goodjsonurl='http://echo.jsontest.com/insert-key-here/insert-value-here/key/value'

    def setUp(self):
        self.scraper = JSONScraper(logging)
        
    def tearDown(self):
        self.scraper = None
        
        
    def test_downloadWebData_fail_1(self):
        with self.assertRaises(TwitchException):
            self.scraper.downloadWebData(self.badurl1)
            
    def test_downloadWebData_fail_2(self):
        with self.assertRaises(TwitchException):
            self.scraper.downloadWebData(self.badurl2)
            
    def test_downloadWebData_1(self):
        retString = self.scraper.downloadWebData(self.goodurl)
        self.assertIsInstance(
            retString, 
            str, 
            msg='Returned Object is not a string')
        
    def test_getJson_fail_1(self):
        with self.assertRaises(TwitchException):
            self.scraper.getJson(self.badurl1)
            
    def test_getJson_fail_2(self):
        with self.assertRaises(TwitchException):
            self.scraper.getJson(self.badurl2)
            
    def test_getJson_fail_3(self):
        with self.assertRaises(TwitchException):
            self.scraper.getJson(self.goodurl)
            
    def test_getJson_1(self):
            self.scraper.getJson(self.goodjsonurl)
        
        
    def suite(self):
        testSuite = unittest.TestSuite()
        testSuite.addTest(unittest.makeSuite(TestJsonScraper))
        return testSuite
        
        
        
