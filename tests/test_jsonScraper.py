import json

from support import log, unittest
from twitch import *


@unittest.skip("Skipping Json/WebDataDownloader Tests")
class TestJsonScraper(unittest.TestCase):
    scraper=None
    badurl1='asdffdsaa'
    badurl2='www.google.com'
    goodurl='http://www.google.com'
    goodjsonurl='http://echo.jsontest.com/key1/value1/key2/value2'
    goodjsonurlunsorted='http://echo.jsontest.com/key2/value2/key1/value1'

    def setUp(self):
        self.scraper = JSONScraper(log)

    def tearDown(self):
        self.scraper = None


    def test_downloadWebData_fail_1(self):
        with self.assertRaises(ValueError):
            self.scraper.downloadWebData(self.badurl1)

    def test_downloadWebData_fail_2(self):
        with self.assertRaises(ValueError):
            self.scraper.downloadWebData(self.badurl2)
            
    def test_downloadWebData_1(self):
        retString = self.scraper.downloadWebData(self.goodurl)
        self.assertIsInstance(
            retString, 
            str, 
            msg='Returned Object is not a string')
        
    def test_getJson_fail_1(self):
        with self.assertRaises(ValueError):
            self.scraper.getJson(self.badurl1)

    def test_getJson_fail_2(self):
        with self.assertRaises(ValueError):
            self.scraper.getJson(self.badurl2)

    def test_getJson_fail_3(self):
        with self.assertRaises(TwitchException):
            self.scraper.getJson(self.goodurl)

    def test_getJson_1(self):
            retJson=self.scraper.getJson(self.goodjsonurl)
            retJson2=self.scraper.getJson(self.goodjsonurlunsorted)
            self.assertEqual(
                json.dumps(retJson,sort_keys=True),
                json.dumps(retJson2,sort_keys=True),
                'json not equal')
        
    def suite(self):
        testSuite = unittest.TestSuite()
        testSuite.addTest(unittest.makeSuite(TestJsonScraper))
        return testSuite

