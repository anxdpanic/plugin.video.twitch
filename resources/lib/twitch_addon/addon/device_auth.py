# -*- coding: utf-8 -*-
"""
    Device Code Grant Flow for Twitch OAuth

    Copyright (C) 2026 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

import json
import time
import requests
from urllib.parse import urlencode

from .common import kodi, log_utils
from . import utils
from .constants import SCOPES

# Twitch OAuth endpoints
DEVICE_AUTH_URL = 'https://id.twitch.tv/oauth2/device'
TOKEN_URL = 'https://id.twitch.tv/oauth2/token'
VALIDATE_URL = 'https://id.twitch.tv/oauth2/validate'

# Device Code Grant type
DEVICE_GRANT_TYPE = 'urn:ietf:params:oauth:grant-type:device_code'
REFRESH_GRANT_TYPE = 'refresh_token'


class DeviceAuthError(Exception):
    """Exception for Device Auth errors"""
    pass


class DeviceAuth:
    """
    Implements the Device Code Grant Flow for Twitch.
    
    This flow is designed for devices with limited input capabilities
    like set-top boxes, game consoles, and media centers (Kodi).
    """
    
    def __init__(self, client_id=None):
        """
        Initialize Device Auth with a client ID.
        
        Args:
            client_id: Twitch application Client ID. If None, uses the addon's configured client ID.
        """
        self.client_id = client_id or utils.get_client_id()
        self.proxies = utils.get_proxy_dict()
        
    def _make_request(self, url, data, method='POST'):
        """Make HTTP request with error handling"""
        try:
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            
            if method == 'POST':
                response = requests.post(url, data=urlencode(data), headers=headers, 
                                        proxies=self.proxies, timeout=30)
            else:
                response = requests.get(url, headers=headers, proxies=self.proxies, timeout=30)
            
            return response.json()
        except requests.exceptions.RequestException as e:
            log_utils.log('Device Auth request failed: %s' % str(e), log_utils.LOGERROR)
            raise DeviceAuthError('Network error: %s' % str(e))
        except json.JSONDecodeError as e:
            log_utils.log('Device Auth JSON decode failed: %s' % str(e), log_utils.LOGERROR)
            raise DeviceAuthError('Invalid response from Twitch')
    
    def start_device_flow(self, scopes=None):
        """
        Start the Device Code flow.
        
        Args:
            scopes: List of OAuth scopes to request. Defaults to SCOPES from constants.
            
        Returns:
            dict with device_code, user_code, verification_uri, expires_in, interval
        """
        if scopes is None:
            scopes = SCOPES
        
        scope_string = ' '.join(scopes)
        
        data = {
            'client_id': self.client_id,
            'scopes': scope_string
        }
        
        log_utils.log('Starting Device Code flow with client_id: %s' % self.client_id[:8] + '...', 
                     log_utils.LOGDEBUG)
        
        result = self._make_request(DEVICE_AUTH_URL, data)
        
        if 'error' in result:
            error_msg = result.get('message', result.get('error', 'Unknown error'))
            log_utils.log('Device Code flow failed: %s' % error_msg, log_utils.LOGERROR)
            raise DeviceAuthError(error_msg)
        
        required_fields = ['device_code', 'user_code', 'verification_uri']
        for field in required_fields:
            if field not in result:
                raise DeviceAuthError('Missing required field: %s' % field)
        
        log_utils.log('Device Code flow started. User code: %s' % result['user_code'], 
                     log_utils.LOGINFO)
        
        return result
    
    def poll_for_token(self, device_code, interval=5, timeout=1800, progress_callback=None):
        """
        Poll for the access token after user authorizes.
        
        Args:
            device_code: The device_code from start_device_flow()
            interval: Polling interval in seconds (default: 5)
            timeout: Maximum time to wait in seconds (default: 1800 = 30 min)
            progress_callback: Optional callback(elapsed, total) for progress updates
            
        Returns:
            dict with access_token, refresh_token, expires_in, scope, token_type
        """
        data = {
            'client_id': self.client_id,
            'device_code': device_code,
            'grant_type': DEVICE_GRANT_TYPE
        }
        
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            
            if elapsed >= timeout:
                raise DeviceAuthError('Authorization timeout')
            
            if progress_callback:
                progress_callback(int(elapsed), timeout)
            
            result = self._make_request(TOKEN_URL, data)
            
            if 'access_token' in result:
                log_utils.log('Device Code flow: Token received successfully', log_utils.LOGINFO)
                return result
            
            if 'status' in result:
                status = result['status']
                message = result.get('message', '')
                
                if status == 400 and message == 'authorization_pending':
                    # User hasn't authorized yet, keep polling
                    time.sleep(interval)
                    continue
                elif status == 400 and message == 'slow_down':
                    # We're polling too fast, increase interval
                    interval = min(interval + 5, 30)
                    log_utils.log('Device Code flow: Slowing down, new interval: %d' % interval, 
                                 log_utils.LOGDEBUG)
                    time.sleep(interval)
                    continue
                elif status == 400 and message == 'expired_token':
                    raise DeviceAuthError('Device code expired. Please try again.')
                elif status == 400 and message == 'access_denied':
                    raise DeviceAuthError('Authorization denied by user.')
                else:
                    raise DeviceAuthError('Authorization failed: %s' % message)
            
            # Unknown response, wait and retry
            time.sleep(interval)
    
    def refresh_token(self, refresh_token, client_secret=None):
        """
        Refresh an access token using a refresh token.
        
        For Public clients (no client_secret), the refresh token is one-time use.
        Store the new refresh_token from the response!
        
        Args:
            refresh_token: The refresh token to use
            client_secret: Optional client secret (for Confidential clients)
            
        Returns:
            dict with access_token, refresh_token, expires_in, scope, token_type
        """
        data = {
            'client_id': self.client_id,
            'grant_type': REFRESH_GRANT_TYPE,
            'refresh_token': refresh_token
        }
        
        if client_secret:
            data['client_secret'] = client_secret
        
        log_utils.log('Refreshing access token', log_utils.LOGDEBUG)
        
        result = self._make_request(TOKEN_URL, data)
        
        if 'error' in result or 'status' in result:
            error_msg = result.get('message', result.get('error', 'Token refresh failed'))
            log_utils.log('Token refresh failed: %s' % error_msg, log_utils.LOGERROR)
            raise DeviceAuthError(error_msg)
        
        if 'access_token' not in result:
            raise DeviceAuthError('Invalid response: no access_token')
        
        log_utils.log('Token refreshed successfully', log_utils.LOGINFO)
        return result
    
    @staticmethod
    def validate_token(token):
        """
        Validate an access token.
        
        Args:
            token: The access token to validate
            
        Returns:
            dict with client_id, login, scopes, user_id, expires_in
            or dict with status and message if invalid
        """
        try:
            headers = {'Authorization': 'OAuth %s' % token}
            response = requests.get(VALIDATE_URL, headers=headers, timeout=30)
            return response.json()
        except Exception as e:
            log_utils.log('Token validation failed: %s' % str(e), log_utils.LOGERROR)
            return {'status': 401, 'message': 'Validation request failed'}


def show_device_auth_dialog(client_id=None):
    """
    Show the Device Auth dialog to the user and handle the complete flow.
    
    Args:
        client_id: Optional Twitch Client ID
        
    Returns:
        dict with tokens on success, None on failure/cancel
    """
    i18n = utils.i18n
    
    auth = DeviceAuth(client_id)
    
    try:
        # Start the flow
        device_info = auth.start_device_flow()
        
        user_code = device_info['user_code']
        verification_uri = device_info['verification_uri']
        expires_in = device_info.get('expires_in', 1800)
        interval = device_info.get('interval', 5)
        device_code = device_info['device_code']
        
        # Show dialog with user code
        instructions = i18n('device_auth_instructions') % (verification_uri, user_code)
        progress = kodi.ProgressDialog(
            i18n('device_auth_title'),
            line1=instructions
        )
        
        def progress_callback(elapsed, total):
            percent = int((elapsed / total) * 100)
            progress.update(
                percent,
                line1=instructions,
                line2=i18n('device_auth_waiting')
            )
            if progress.is_canceled():
                raise DeviceAuthError('Cancelled by user')
        
        try:
            tokens = auth.poll_for_token(
                device_code, 
                interval=interval, 
                timeout=expires_in,
                progress_callback=progress_callback
            )
            
            if progress.pd:
                progress.pd.close()
            
            # Save the tokens
            save_device_tokens(tokens)
            
            kodi.notify(
                kodi.get_name(),
                i18n('device_auth_success'),
                sound=False
            )
            
            return tokens
            
        except DeviceAuthError as e:
            if progress.pd:
                progress.pd.close()
            if str(e) != 'Cancelled by user':
                kodi.Dialog().ok(i18n('device_auth_title'), str(e))
            return None
            
    except DeviceAuthError as e:
        kodi.Dialog().ok(i18n('device_auth_title'), str(e))
        return None


def save_device_tokens(tokens):
    """
    Save tokens from Device Code flow to addon settings.
    
    Args:
        tokens: dict with access_token, refresh_token, expires_in
    """
    access_token = tokens.get('access_token', '')
    refresh_token = tokens.get('refresh_token', '')
    expires_in = tokens.get('expires_in', 0)
    
    # Calculate expiry timestamp
    expires_at = int(time.time()) + expires_in if expires_in else 0
    
    # Save to settings - only save to oauth_token_helix (for Helix API)
    # Do NOT save to twitch_hevc_token - Device Auth tokens are third-party tokens
    # that don't work with the GQL/private API (causes 401). The GQL API works
    # anonymously with just a Client-ID, or with first-party website tokens.
    kodi.set_setting('oauth_token_helix', access_token)
    kodi.set_setting('device_refresh_token', refresh_token)
    kodi.set_setting('device_token_expires_at', str(expires_at))
    
    log_utils.log('Device tokens saved. Expires at: %s' % expires_at, log_utils.LOGDEBUG)


def get_device_tokens():
    """
    Get saved device tokens.
    
    Returns:
        dict with access_token, refresh_token, expires_at or None
    """
    access_token = kodi.get_setting('oauth_token_helix')
    refresh_token = kodi.get_setting('device_refresh_token')
    expires_at_str = kodi.get_setting('device_token_expires_at')
    
    if not access_token or not refresh_token:
        return None
    
    try:
        expires_at = int(expires_at_str) if expires_at_str else 0
    except ValueError:
        expires_at = 0
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_at': expires_at
    }


def is_token_expired():
    """
    Check if the current token is expired or about to expire.
    
    Returns:
        True if token is expired or expires within 5 minutes
    """
    tokens = get_device_tokens()
    if not tokens:
        return True
    
    expires_at = tokens.get('expires_at', 0)
    # Consider expired if less than 5 minutes remaining
    return time.time() >= (expires_at - 300)


def auto_refresh_token():
    """
    Automatically refresh the token if it's expired.
    
    Returns:
        True if token is valid (or was refreshed), False if refresh failed
    """
    tokens = get_device_tokens()
    if not tokens:
        log_utils.log('No device tokens found for auto-refresh', log_utils.LOGDEBUG)
        return False
    
    if not is_token_expired():
        return True
    
    refresh_token = tokens.get('refresh_token')
    if not refresh_token:
        log_utils.log('No refresh token available', log_utils.LOGWARNING)
        return False
    
    try:
        auth = DeviceAuth()
        new_tokens = auth.refresh_token(refresh_token)
        save_device_tokens(new_tokens)
        log_utils.log('Token auto-refreshed successfully', log_utils.LOGINFO)
        return True
    except DeviceAuthError as e:
        log_utils.log('Token auto-refresh failed: %s' % str(e), log_utils.LOGWARNING)
        # Clear invalid tokens
        kodi.set_setting('device_refresh_token', '')
        kodi.set_setting('device_token_expires_at', '')
        return False


def clear_device_tokens():
    """Clear all saved device tokens (does not touch twitch_hevc_token)."""
    kodi.set_setting('oauth_token_helix', '')
    kodi.set_setting('device_refresh_token', '')
    kodi.set_setting('device_token_expires_at', '')
    log_utils.log('Device tokens cleared', log_utils.LOGINFO)
