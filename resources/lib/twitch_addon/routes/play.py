# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import utils
from ..addon.common import kodi, log_utils
from ..addon.constants import Keys, LINE_LENGTH
from ..addon.converter import JsonListItemConverter
from ..addon.twitch_exceptions import PlaybackFailed, SubRequired, TwitchException
from ..addon.watch_history import get_watch_history


def route(api, seek_time=0, channel_id=None, video_id=None, slug=None, ask=False, use_player=False, quality=None, channel_name=None):
    converter = JsonListItemConverter(LINE_LENGTH)
    window = kodi.Window(10000)
    use_ia = utils.use_inputstream_adaptive()

    def _reset():
        window.clearProperty(kodi.get_id() + '-_seek')
        window.clearProperty(kodi.get_id() + '-seek_time')
        window.clearProperty(kodi.get_id() + '-twitch_playing')

    def _reset_live():
        window.clearProperty(kodi.get_id() + '-livestream')

    def _get_seek():
        _result = window.getProperty(kodi.get_id() + '-_seek')
        if _result:
            return _result.split(',')
        return None, None

    def _set_playing():
        window.setProperty(kodi.get_id() + '-twitch_playing', str(True))

    def _set_live(_id, _name, _display_name, _quality):
        window.setProperty(kodi.get_id() + '-livestream', '%s,%s,%s,%s' % (_id, _name, _display_name, _quality))

    def _set_seek_time(value):
        window.setProperty(kodi.get_id() + '-seek_time', str(value))

    try:
        _reset_live()
        videos = item_dict = name = None
        seek_time = int(seek_time)
        is_live = False
        if video_id:
            seek_id, _seek_time = _get_seek()
            if seek_id == video_id:
                seek_time = int(_seek_time)
            restricted = False
            unrestricted = None
            result = api.get_video_by_id(video_id)
            result = result.get(Keys.DATA, [{}])[0]

            video_id = result[Keys.ID]
            channel_id = result[Keys.USER_ID]
            channel_name = result[Keys.USER_NAME] if result[Keys.USER_NAME] else result[Keys.USER_LOGIN]
            try:
                extra_info = api._get_video_token(video_id)  # NOQA
            except TwitchException:
                extra_info = dict()
            if api.access_token:
                try:
                    subscribed = api.check_subscribed(channel_id)
                except TwitchException as e:
                    if ('status' in e.message) and (e.message['status'] == 422):
                        subscribed = True  # no subscription program
                    else:
                        raise
            else:
                subscribed = False
            if not subscribed:
                unrestricted = result.get(Keys.RESOLUTIONS, dict())
                if unrestricted:
                    unrestricted[u'audio_only'] = u''
                if ('chansub' in extra_info) and ('restricted_bitrates' in extra_info['chansub']):
                    log_utils.log('Restricted qualities |%s|' % extra_info['chansub']['restricted_bitrates'], log_utils.LOGDEBUG)
                    for res in extra_info['chansub']['restricted_bitrates']:
                        if res in unrestricted:
                            del unrestricted[res]
                    if unrestricted == {}:
                        restricted = True
            if not restricted:
                _videos = api.get_vod(video_id)
                if unrestricted:
                    videos = list()
                    for _video in _videos:
                        if _video['id'] in list(unrestricted.keys()):
                            videos.append(_video)
                else:
                    videos = _videos
                item_dict = converter.video_to_playitem(result)
                if not quality:
                    quality = utils.get_default_quality('video', channel_id)
                    if quality:
                        quality = quality[str(channel_id)]['quality']
            else:
                raise SubRequired(channel_name)
        elif channel_id or channel_name:
            if channel_name and not channel_id:
                result = api.get_user_ids(channel_name)
                if result:
                    channel_id = result[0]
            if channel_id:
                if not quality:
                    quality = utils.get_default_quality('stream', channel_id)
                    if quality:
                        quality = quality[str(channel_id)]['quality']
                id_only = False
                result = api.get_channel_stream(channel_id)[Keys.DATA]
                if result:
                    result = result[0]
                    channel_name = result[Keys.USER_NAME] \
                        if result[Keys.USER_NAME] else result[Keys.USER_LOGIN]
                    name = result[Keys.USER_LOGIN]
                else:  # rerun
                    user = api.get_users(user_ids=channel_id)
                    if user.get(Keys.DATA, [{}]):
                        user = user[Keys.DATA][0]
                        id_only = True
                        name = user.get(Keys.LOGIN)
                        result = {
                            Keys.USER_NAME: user.get(Keys.DISPLAY_NAME, Keys.LOGIN),
                            Keys.USER_LOGIN: user.get(Keys.LOGIN),
                            Keys.USER_ID: user.get(Keys.ID),
                        }  # make a dummy result to continue with playback
                if name:
                    videos = api.get_live(name)
                    item_dict = converter.stream_to_playitem(result, id_only=id_only)
                    is_live = True
        elif slug:
            result = api.get_clip_by_slug(slug)
            result = result.get(Keys.DATA, [{}])[0]

            channel_id = result[Keys.BROADCASTER_ID]
            if not quality:
                quality = utils.get_default_quality('clip', channel_id)
                if quality:
                    quality = quality[str(channel_id)]['quality']
            videos = api.get_clip(slug)
            item_dict = converter.clip_to_playitem(result)
        _reset()
        if item_dict and videos:
            clip = False if slug is None else True
            result = converter.get_video_for_quality(videos, ask=ask, quality=quality, clip=clip)
            if result:
                quality_label = result['name']
                log_utils.log('Selected quality: %s, use_ia: %s, result keys: %s' % 
                            (quality_label, use_ia, list(result.keys())), log_utils.LOGDEBUG)

                request = None
                play_url = None
                if 'Adaptive' in quality_label and use_ia:
                    if video_id:
                        request = api.video_request(video_id)
                    elif is_live:
                        request = api.live_request(name)
                    log_utils.log('Adaptive quality requested - use_ia: %s, is_live: %s, request: %s' % 
                                (use_ia, is_live, 'None' if request is None else 'received'), log_utils.LOGDEBUG)
                    if request:
                        log_utils.log('Request keys: %s' % list(request.keys()), log_utils.LOGDEBUG)
                        if kodi.get_kodi_version().major >= 18:
                            request['headers']['verifypeer'] = 'false'
                        play_url = request['url'] + utils.append_headers(request['headers'])
                        log_utils.log('Built play_url from request: %s' % play_url[:100], log_utils.LOGDEBUG)

                if not play_url:
                    play_url = result['url']
                    headers = {}
                    if kodi.get_kodi_version().major >= 18:
                        headers['verifypeer'] = 'false'
                    if 'request' in locals() and request and 'headers' in request:
                        headers.update(request['headers'])
                    play_url += utils.append_headers(headers)

                if is_live:
                    _set_live(channel_id, name, channel_name, quality_label)
                log_utils.log('Attempting playback using quality |%s| @ |%s|' % (quality_label, play_url), log_utils.LOGINFO)
                item_dict['path'] = play_url
                playback_item = kodi.create_item(item_dict, add=False)
                stream_info = {
                    'video': {},
                    'audio': {
                        'channels': '2'
                    }
                }
                if result:
                    language = result.get(Keys.CHANNEL, {}).get(Keys.BROADCASTER_LANGUAGE)
                    if language:
                        stream_info['audio']['language'] = language
                playback_item.addStreamInfo('video', stream_info.get('video'))
                playback_item.addStreamInfo('audio', stream_info.get('audio'))
                if not clip:
                    try:
                        playback_item.setContentLookup(False)
                        playback_item.setMimeType('application/x-mpegURL')
                    except AttributeError:
                        pass
                elif clip and play_url.endswith('mp4'):
                    try:
                        playback_item.setContentLookup(False)
                        playback_item.setMimeType('video/mp4')
                    except AttributeError:
                        pass
                if 'Adaptive' in quality_label and use_ia:
                    inputstream_property = 'inputstream'
                    kodi_version = kodi.get_kodi_version()
                    if kodi_version.major < 19:
                        inputstream_property += 'addon'
                    playback_item.setProperty(inputstream_property, 'inputstream.adaptive')
                    # manifest_type is deprecated on Kodi 21+ (auto-detected)
                    if kodi_version.major < 21:
                        playback_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
                    
                    # Use 'fixed-res' mode to select the highest quality stream from the start
                    # and keep it fixed without adaptive bandwidth-based switching.
                    # 
                    # This ensures:
                    # - HEVC 1440p+ streams are selected when available (with correct audio)
                    # - H.264 1080p streams are selected at full quality (not downgraded to 720p)
                    # - No mid-stream quality switching that could cause audio desync
                    playback_item.setProperty('inputstream.adaptive.stream_selection_type', 'fixed-res')
                    
                    # Set maximum resolution to 4K to allow all available qualities
                    # Valid values: 480p, 640p, 720p, 1080p, 2K, 1440p, 4K
                    playback_item.setProperty('inputstream.adaptive.chooser_resolution_max', '4K')
                    
                    # IMPORTANT: Ignore display resolution to allow 4K/8K streams on any display
                    playback_item.setProperty('inputstream.adaptive.ignore_display_resolution', 'true')
                    
                    # Prefer HEVC codec over H.264 when both are available
                    # Order: HEVC variants > AV1 > H.264 > Audio
                    playback_item.setProperty('inputstream.adaptive.preferred_codecs', 'hev1,hvc1,av1,avc1,mp4a')
                    
                    # Configure proxy for inputstream.adaptive
                    from urllib.parse import urlparse
                    proxy_dict = utils.get_proxy_dict()
                    if proxy_dict:
                        proxy_url = proxy_dict['http']
                        parsed = urlparse(proxy_url)
                        playback_item.setProperty('inputstream.adaptive.proxy_host', parsed.hostname)
                        playback_item.setProperty('inputstream.adaptive.proxy_port', str(parsed.port or 8080))
                        if parsed.username and parsed.password:
                            playback_item.setProperty('inputstream.adaptive.proxy_username', parsed.username)
                            playback_item.setProperty('inputstream.adaptive.proxy_password', parsed.password)
                        log_utils.log('Configured inputstream.adaptive proxy: {}:{}'.format(
                            parsed.hostname, parsed.port or 8080), log_utils.LOGINFO)
                else:
                    # Configure proxy for regular video player (non-adaptive)
                    proxy_dict = utils.get_proxy_dict()
                    if proxy_dict:
                        proxy_url = proxy_dict['http']
                        playback_item.setProperty('http-proxy', proxy_url)
                        playback_item.setProperty('proxy', proxy_url)  # Alternative parameter name
                        log_utils.log('Configured video player proxy: {}'.format(proxy_url), log_utils.LOGINFO)
                        
                if (seek_time > 0) and video_id:
                    _set_seek_time(seek_time)
                _set_playing()
                
                # Save to watch history
                try:
                    watch_history = get_watch_history()
                    if utils.get_watch_history_size() > 0:
                        if is_live and name:
                            # Live stream
                            watch_history.add(
                                content_type='stream',
                                content_id=channel_id,
                                channel_id=channel_id,
                                channel_name=channel_name or name,
                                title=item_dict.get('info', {}).get('title', ''),
                                thumbnail=item_dict.get('thumbnail', ''),
                                game_name=item_dict.get('info', {}).get('genre', '')
                            )
                        elif video_id:
                            # VOD
                            watch_history.add(
                                content_type='video',
                                content_id=video_id,
                                channel_id=channel_id,
                                channel_name=channel_name or '',
                                title=item_dict.get('info', {}).get('title', ''),
                                thumbnail=item_dict.get('thumbnail', ''),
                                game_name=item_dict.get('info', {}).get('genre', ''),
                                duration=item_dict.get('info', {}).get('duration', '')
                            )
                        elif slug:
                            # Clip
                            watch_history.add(
                                content_type='clip',
                                content_id=slug,
                                channel_id=channel_id,
                                channel_name=channel_name or '',
                                title=item_dict.get('info', {}).get('title', ''),
                                thumbnail=item_dict.get('thumbnail', '')
                            )
                except Exception as e:
                    log_utils.log('Failed to save watch history: %s' % str(e), log_utils.LOGWARNING)
                
                if use_player:
                    kodi.Player().play(item_dict['path'], playback_item)
                else:
                    kodi.set_resolved_url(playback_item)
                if (not slug and not video_id) and (name is not None):
                    if utils.irc_enabled() and api.access_token:
                        username = api.get_username()
                        if username:
                            utils.exec_irc_script(username, name)
                return
            else:
                kodi.set_resolved_url(kodi.ListItem(), succeeded=False)
                return

        raise PlaybackFailed()
    except:
        _reset()
        _reset_live()
        raise
