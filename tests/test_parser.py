import unittest

from twitch.parser import m3u8_to_dict


class TestM3U(unittest.TestCase):
    live = """
#EXTM3U
#EXT-X-TWITCH-INFO:NODE="video2.prg01",MANIFEST-NODE="video2.prg01",SERVER-TIME="1400918840.88",USER-IP="123.456.789.123",CLUSTER="prg01",MANIFEST-CLUSTER="prg01"
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="chunked",NAME="Source",AUTOSELECT=YES,DEFAULT=YES
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=2576820,RESOLUTION=1280x720,VIDEO="chunked"
http://video2.prg01.hls.twitch.tv/hls106/riotgamesoceania_9652805392_98328050/chunked/index-live.m3u8?token=id=7828074928424501897,bid=9652805392,exp=1401005240,node=video2-1.prg01.hls.justin.tv,nname=video2.prg01,fmt=chunked&sig=b9cd78d1ae4e9b08da21cc0fec718b2fe506af92
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="high",NAME="High",AUTOSELECT=YES,DEFAULT=YES
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1760000,VIDEO="high"
http://video2.prg01.hls.twitch.tv/hls106/riotgamesoceania_9652805392_98328050/high/index-live.m3u8?token=id=7828074928424501897,bid=9652805392,exp=1401005240,node=video2-1.prg01.hls.justin.tv,nname=video2.prg01,fmt=high&sig=7c20fa2263c78892c0f15c818620f0e85557cabf
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="medium",NAME="Medium",AUTOSELECT=YES,DEFAULT=YES
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=928000,VIDEO="medium"
http://video2.prg01.hls.twitch.tv/hls106/riotgamesoceania_9652805392_98328050/medium/index-live.m3u8?token=id=7828074928424501897,bid=9652805392,exp=1401005240,node=video2-1.prg01.hls.justin.tv,nname=video2.prg01,fmt=medium&sig=6c93f95701cd27818f5cc45da2f1a7abf23a1d1a
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="low",NAME="Low",AUTOSELECT=YES,DEFAULT=YES
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=596000,VIDEO="low"
http://video2.prg01.hls.twitch.tv/hls106/riotgamesoceania_9652805392_98328050/low/index-live.m3u8?token=id=7828074928424501897,bid=9652805392,exp=1401005240,node=video2-1.prg01.hls.justin.tv,nname=video2.prg01,fmt=low&sig=089be1e11a1556877ca575b3eada7a24acc7ea5a
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="mobile",NAME="Mobile",AUTOSELECT=YES,DEFAULT=YES
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=164000,VIDEO="mobile"
http://video2.prg01.hls.twitch.tv/hls106/riotgamesoceania_9652805392_98328050/mobile/index-live.m3u8?token=id=7828074928424501897,bid=9652805392,exp=1401005240,node=video2-1.prg01.hls.justin.tv,nname=video2.prg01,fmt=mobile&sig=087b4221fdd0653456b55b5b77756ca3cadd0226"""
    
    restricted = """
#EXTM3U
#EXT-X-TWITCH-INFO:NODE="video16.prg01",MANIFEST-NODE="video16.prg01",SERVER-TIME="1400927815.96",USER-IP="11.22.33.44",CLUSTER="prg01",MANIFEST-CLUSTER="prg01"
#EXT-X-TWITCH-RESTRICTED:GROUP-ID="chunked",NAME="Source",RESTRICTION="chansub"
#EXT-X-TWITCH-RESTRICTED:GROUP-ID="high",NAME="High",RESTRICTION="chansub"
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="medium",NAME="Medium",AUTOSELECT=YES,DEFAULT=YES
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=928000,VIDEO="medium"
http://video16.prg01.hls.twitch.tv/hls18/ongamenet_9656195424_98434331/medium/index-live.m3u8?token=id=6125541036366455728,bid=9656195424,exp=1401014215,node=video16-1.prg01.hls.justin.tv,nname=video16.prg01,fmt=medium&sig=f1f4f1ee9f9cf47c826ddc95ef1f60d9a2f6a2ce
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="low",NAME="Low",AUTOSELECT=YES,DEFAULT=YES
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=596000,VIDEO="low"
http://video16.prg01.hls.twitch.tv/hls18/ongamenet_9656195424_98434331/low/index-live.m3u8?token=id=6125541036366455728,bid=9656195424,exp=1401014215,node=video16-1.prg01.hls.justin.tv,nname=video16.prg01,fmt=low&sig=754158e9e20ce4fcae5614a1f07d8b37dbc3e1a2
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="mobile",NAME="Mobile",AUTOSELECT=YES,DEFAULT=YES
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=164000,VIDEO="mobile"
http://video16.prg01.hls.twitch.tv/hls18/ongamenet_9656195424_98434331/mobile/index-live.m3u8?token=id=6125541036366455728,bid=9656195424,exp=1401014215,node=video16-1.prg01.hls.justin.tv,nname=video16.prg01,fmt=mobile&sig=cadce653f0b6b663f2a25c4e946788a30f559447"""

    quality_select = """
#EXTM3U
#EXT-X-TWITCH-INFO:NODE="video2.prg01",MANIFEST-NODE="video2.prg01",SERVER-TIME="1400918840.88",USER-IP="61.111.117.211",CLUSTER="prg01",MANIFEST-CLUSTER="prg01"
#EXT-X-TWITCH-RESTRICTED:GROUP-ID="chunked",NAME="Source",RESTRICTION="chansub"
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="high",NAME="High",AUTOSELECT=YES,DEFAULT=YES
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1760000,VIDEO="high"
http://video2.prg01.hls.twitch.tv/hls106/riotgamesoceania_9652805392_98328050/high/index-live.m3u8?token=id=7828074928424501897,bid=9652805392,exp=1401005240,node=video2-1.prg01.hls.justin.tv,nname=video2.prg01,fmt=high&sig=7c20fa2263c78892c0f15c818620f0e85557cabf
#EXT-X-TWITCH-RESTRICTED:GROUP-ID="medium",NAME="Medium",RESTRICTION="chansub"
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="low",NAME="Low",AUTOSELECT=YES,DEFAULT=YES
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=596000,VIDEO="low"
http://video2.prg01.hls.twitch.tv/hls106/riotgamesoceania_9652805392_98328050/low/index-live.m3u8?token=id=7828074928424501897,bid=9652805392,exp=1401005240,node=video2-1.prg01.hls.justin.tv,nname=video2.prg01,fmt=low&sig=089be1e11a1556877ca575b3eada7a24acc7ea5a
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="mobile",NAME="Mobile",AUTOSELECT=YES,DEFAULT=YES
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=164000,VIDEO="mobile"
http://video2.prg01.hls.twitch.tv/hls106/riotgamesoceania_9652805392_98328050/mobile/index-live.m3u8?token=id=7828074928424501897,bid=9652805392,exp=1401005240,node=video2-1.prg01.hls.justin.tv,nname=video2.prg01,fmt=mobile&sig=087b4221fdd0653456b55b5b77756ca3cadd0226"""

    vod = """
#EXTM3U
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="chunked",NAME="Source",AUTOSELECT=YES,DEFAULT=YES
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=3733604,CODECS="avc1.4D4029,mp4a.40.2",VIDEO="chunked"
http://vod.ak.hls.ttvnw.net/v1/AUTH_system/vods_1ddc/hutch_12752035712_193039230/chunked/index-dvr.m3u8
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="high",NAME="High",AUTOSELECT=YES,DEFAULT=YES
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1578365,CODECS="avc1.42C01F,mp4a.40.2",VIDEO="high"
http://vod.ak.hls.ttvnw.net/v1/AUTH_system/vods_1ddc/hutch_12752035712_193039230/high/index-dvr.m3u8
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="medium",NAME="Medium",AUTOSELECT=YES,DEFAULT=YES
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=885579,CODECS="avc1.42C01E,mp4a.40.2",VIDEO="medium"
http://vod.ak.hls.ttvnw.net/v1/AUTH_system/vods_1ddc/hutch_12752035712_193039230/medium/index-dvr.m3u8
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="low",NAME="Low",AUTOSELECT=YES,DEFAULT=YES
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=622726,CODECS="avc1.42C01E,mp4a.40.2",VIDEO="low"
http://vod.ak.hls.ttvnw.net/v1/AUTH_system/vods_1ddc/hutch_12752035712_193039230/low/index-dvr.m3u8
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="mobile",NAME="Mobile",AUTOSELECT=YES,DEFAULT=YES
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=270006,CODECS="avc1.42C00D,mp4a.40.2",VIDEO="mobile"
http://vod.ak.hls.ttvnw.net/v1/AUTH_system/vods_1ddc/hutch_12752035712_193039230/mobile/index-dvr.m3u8"""

    def test_live_0(self):
        expected = 'http://video2.prg01.hls.twitch.tv/hls106/riotgamesoceania_9652805392_98328050/chunked/index-live.m3u8?token=id=7828074928424501897,bid=9652805392,exp=1401005240,node=video2-1.prg01.hls.justin.tv,nname=video2.prg01,fmt=chunked&sig=b9cd78d1ae4e9b08da21cc0fec718b2fe506af92'
        url = m3u8_to_dict(self.live)['Source']
        self.assertEqual(url, expected)

    def test_live_2(self):
        expected = 'http://video2.prg01.hls.twitch.tv/hls106/riotgamesoceania_9652805392_98328050/medium/index-live.m3u8?token=id=7828074928424501897,bid=9652805392,exp=1401005240,node=video2-1.prg01.hls.justin.tv,nname=video2.prg01,fmt=medium&sig=6c93f95701cd27818f5cc45da2f1a7abf23a1d1a'
        url = m3u8_to_dict(self.live)['Medium']
        self.assertEqual(url, expected)

    def test_restr_0_2(self):
        expected = 'http://video16.prg01.hls.twitch.tv/hls18/ongamenet_9656195424_98434331/medium/index-live.m3u8?token=id=6125541036366455728,bid=9656195424,exp=1401014215,node=video16-1.prg01.hls.justin.tv,nname=video16.prg01,fmt=medium&sig=f1f4f1ee9f9cf47c826ddc95ef1f60d9a2f6a2ce'
        with self.assertRaises(KeyError):
            m3u8_to_dict(self.restricted)['Source']
        url = m3u8_to_dict(self.restricted)['Medium']
        self.assertEqual(url, expected)

    def test_restr_3(self):
        expected = 'http://video16.prg01.hls.twitch.tv/hls18/ongamenet_9656195424_98434331/low/index-live.m3u8?token=id=6125541036366455728,bid=9656195424,exp=1401014215,node=video16-1.prg01.hls.justin.tv,nname=video16.prg01,fmt=low&sig=754158e9e20ce4fcae5614a1f07d8b37dbc3e1a2'
        url = m3u8_to_dict(self.restricted)['Low']
        self.assertEqual(url, expected)

    def test_vod_0(self):
        expected = 'http://vod.ak.hls.ttvnw.net/v1/AUTH_system/vods_1ddc/hutch_12752035712_193039230/chunked/index-dvr.m3u8'
        url = m3u8_to_dict(self.vod)['Source']
        self.assertEqual(url, expected)
