# Twitch on Kodi

[![Build Status](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2Fanxdpanic%2Fplugin.video.twitch%2Fbadge&style=flat)](https://actions-badge.atrox.dev/anxdpanic/plugin.video.twitch/goto)
![License](https://img.shields.io/badge/license-GPL--3.0--only-success.svg)
![Kodi Version](https://img.shields.io/badge/kodi-nexus%2B-success.svg)
![Contributors](https://img.shields.io/github/contributors/anxdpanic/plugin.video.twitch.svg)

Watch your favorite gaming streams on Kodi with HEVC/H.265 support, low latency mode, and ad-free viewing (with Turbo/Subscriber benefits).

## Setup Guide

### Quick Start (Recommended)

You need **two tokens** for full functionality:

| Token | Purpose | Required? |
|-------|---------|-----------|
| **OAuth Token** | Helix API (browse streams, channels, games, followers) | Yes |
| **Website Token** | HEVC streams, ad-free viewing, private API | Optional but recommended |

### Step 1: Get OAuth Token

You need to create a Twitch Developer Application:

1. Go to [Twitch Developer Console](https://dev.twitch.tv/console/apps)
2. Click **Register Your Application**
3. Fill in:
   - **Name**: Any name (e.g., "Kodi Twitch")
   - **OAuth Redirect URLs**: `http://localhost`
   - **Category**: Application Integration
4. Click **Create**
5. Copy your **Client ID** and generate a **Client Secret**

Then run the token generator script:

```bash
python3 get_oauth_token.py
```

Enter your Client ID and Secret, then follow the on-screen instructions to authorize.

### Step 2: Get Website Token (Optional, for HEVC/Ad-free)

1. Open [twitch.tv](https://www.twitch.tv) in your browser and log in
2. Open Developer Tools (F12)
3. Go to **Application** → **Cookies** → `https://www.twitch.tv`
4. Find the cookie named `auth-token`
5. Copy its value

### Step 3: Configure the Addon

In Kodi, go to **Add-ons → Video Add-ons → Twitch → Settings**:

**Login Tab:**
- **Client ID**: Your Twitch Developer App Client ID  
  _(or leave default for Website Token only)_
- **OAuth Token**: The token from `get_oauth_token.py`
- **Website Token (HEVC)**: The `auth-token` cookie value

### Step 4: Configure Playback

Go to **Settings → Playback**:

- **Video Quality**: Set to **Adaptive** (recommended)
- **Low Latency Mode**: Enable for reduced stream delay

## Features

### HEVC/H.265 Support
- Automatically uses HEVC codec when available (requires Website Token)
- Better quality at lower bitrates
- Reduced bandwidth usage

### Low Latency Mode
- Reduces stream delay to ~2-5 seconds
- Enable in Settings → Playback → Low Latency Mode

### Adaptive Streaming
- Uses InputStream Adaptive for best quality
- Automatically selects highest quality your connection supports
- Smooth quality transitions

### Ad-Free Viewing
- With Twitch Turbo or channel subscriptions
- Requires Website Token configured

## Troubleshooting

### "OAuth token is required" Message
This appears when:
1. **IRC Chat is enabled** but no OAuth Token is configured
   - Solution: Either enter an OAuth Token or disable IRC Chat in Settings → IRC Chat

2. **No OAuth Token for Helix API**
   - Solution: Run `get_oauth_token.py` to generate a token

### Playback Issues (Buffering, Audio Desync)
1. Make sure **InputStream Adaptive** add-on is installed
2. Set Video Quality to **Adaptive** (not Source)
3. Try disabling Low Latency Mode if issues persist

### "Invalid or expired token"
- Your OAuth Token has expired
- Run `get_oauth_token.py` again to generate a new one
- Website Tokens expire when you log out of Twitch in your browser

### HEVC Not Working
- Ensure Website Token is configured
- Check your device supports HEVC decoding
- Verify the streamer is broadcasting in HEVC (not all do)

## Token Refresh

OAuth Tokens expire after some time. The `get_oauth_token.py` script provides a refresh token that can be used to get a new access token without re-authorizing.

Website Tokens (auth-token cookie) are tied to your browser session and expire when you log out of Twitch.

## FAQ

**Q: I can't find the Twitch add-on in Kodi's add-on manager!**
> Make sure you are using at least Kodi 20 (Nexus).

**Q: Do I need both tokens?**
> For basic functionality, only the OAuth Token is required. The Website Token adds HEVC support and ad-free viewing.

**Q: Can I use just the Website Token?**
> No, the Website Token doesn't work with Twitch's official Helix API. You need an OAuth Token from a registered Twitch App for browsing functionality.

**Q: Why are there two different tokens?**
> Twitch has two APIs:
> - **Helix API** (official): Requires OAuth Token from a registered app
> - **GQL/Private API** (unofficial): Uses Website Token from browser session

## Credits

Thanks to all the people who contributed to this add-on.
For a complete list, visit [CONTRIBUTORS](https://github.com/anxdpanic/plugin.video.twitch/blob/master/CONTRIBUTORS.md)
