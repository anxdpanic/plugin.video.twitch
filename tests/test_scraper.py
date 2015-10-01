import json
import os
import unittest

from twitch.api import v3
from twitch.scraper import get_json, download

from . import ci


@unittest.skipIf(ci, "Skipping scraper tests on travis")
class TestScraper(unittest.TestCase):
    badurl1='asdffdsaa'
    badurl2='www.google.com'
    goodurl='http://www.google.com'
    goodjsonurl='http://echo.jsontest.com/key1/value1/key2/value2'
    goodjsonurlunsorted='http://echo.jsontest.com/key2/value2/key1/value1'


    def test_download_fail_1(self):
        with self.assertRaises(ValueError):
            download(self.badurl1)

    def test_download_fail_2(self):
        with self.assertRaises(ValueError):
            download(self.badurl2)

    def test_download_1(self):
        retString = download(self.goodurl)
        self.assertIsInstance(
            retString, 
            str, 
            msg='Returned Object is not a string')

    def test_get_json_fail_1(self):
        with self.assertRaises(ValueError):
            get_json(self.badurl1)

    def test_get_json_fail_2(self):
        with self.assertRaises(ValueError):
            get_json(self.badurl2)

    def test_get_json_fail_3(self):
        with self.assertRaises(ValueError):
            get_json(self.goodurl)

    def test_get_json_1(self):
        retJson=get_json(self.goodjsonurl)
        retJson2=get_json(self.goodjsonurlunsorted)
        self.assertEqual(
            json.dumps(retJson,sort_keys=True),
            json.dumps(retJson2,sort_keys=True),
            'json not equal')

    def test_params(self):
        url = 'https://api.twitch.tv/kraken/streams'
        limit = 10
        r = get_json(url, parameters={'limit': limit})
        self.assertEqual(len(r.get('streams')), limit)
