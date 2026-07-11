Twitch on Kodi
==================

[![Build Status](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2Fanxdpanic%2Fplugin.video.twitch%2Fbadge&style=flat)](https://actions-badge.atrox.dev/anxdpanic/plugin.video.twitch/goto)
![License](https://img.shields.io/badge/license-GPL--3.0--only-success.svg)
![Kodi Version](https://img.shields.io/badge/kodi-nexus%2B-success.svg)
![Contributors](https://img.shields.io/github/contributors/anxdpanic/plugin.video.twitch.svg)

Watch your favorite gaming streams on Kodi.

LOGIN
----------------

1. Go to __Settings - Login - Login (device code)__
2. Visit [twitch.tv/activate](https://www.twitch.tv/activate) on any device, sign in, and enter the code shown in Kodi

The add-on stores the tokens and refreshes them automatically. Automatic refresh
requires a public Client ID — the bundled Client ID cannot refresh tokens, so you
will be asked to log in again once the token expires. To enable automatic refresh:

1. Register your own application at [dev.twitch.tv/console/apps](https://dev.twitch.tv/console/apps)
   (OAuth Redirect URL: `http://localhost`, Client Type: __Public__)
2. Enter its Client ID in __Settings - Developer - OAuth Client ID__
3. Log in again via __Settings - Login - Login (device code)__

AD-FREE PLAYBACK (TURBO / SUBSCRIPTIONS)
----------------

If your Twitch account has Turbo, or you are subscribed to a channel, you can use
__Settings - Subscriber and Turbo Benefits - Login: ad-free playback / Turbo (device code)__
and authorize with that account to watch without ads (where Twitch grants it).

FAQ
----------------

* I can't find the Twitch.tv add-on in the Kodi add-on manager!

> Make sure you are using at least Kodi 20 (Nexus).

* I'm having issues with the playback of streams (buffering, dropping, stuttering).

> This Add-on does not handle any aspect of the playback of Twitch streams (that would be the Kodi Video Player), it simply tells Kodi what to play.
> The Add-on does however provide Quality Options which may help if your internet connection / computer specs are below requirements for HD streams.
> Try making sure that the Kodi Add-on "InputStream Adaptive" is installed, and Adaptive Quality is enabled in Twitch.tv's Add-on settings.

What's next?
----------------

Things that need to be done next:

* Suggestions welcome.

Credit where credit is due.
-------------

Thanks to all the people who contributed to this add-on. 
For a complete list of the people who have shaped this add-on, visit [CONTRIBUTORS](https://github.com/anxdpanic/plugin.video.twitch/blob/master/CONTRIBUTORS.md)
