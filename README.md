# Twitch (plugin.video.twitch)

A Kodi video add-on for Twitch with a TV layout: live channels, past broadcasts, highlights, uploads
and clips, in Kodi's own folders or in a full-screen TV interface. It targets Kodi 21 (Omega) and later.

## Features

- **Two ways to browse:** the add-on's folders in Kodi's video window, using the skin's views, or the TV
  interface, a full-screen window with a navigation rail, the focused tile's details and rows of tiles.
- **Pages:** Home (live channels you follow, top live channels, top categories), Following, Categories,
  a category's live channels, clips and videos, a channel's live stream, schedule, past broadcasts,
  highlights, uploads and clips, and search across live channels, channels and categories.
- **Sign-in:** a code at twitch.tv/activate (with a QR code), as Twitch's TV app. Several accounts can be
  signed in. Turbo and subscriber benefits come with the sign-in.
- **From a tile's menu:** play a live stream from the beginning, go to the channel or category, follow or
  unfollow the channel, and a QR code of its subscribe page to subscribe on a phone.
- **Playback:** live streams and past broadcasts as HLS, clips as MP4. Live streams play through
  InputStream Adaptive or, by choice, InputStream FFmpeg Direct; everything else through Adaptive.
  Optional H.265 and AV1, and an option to choose the quality each time.
- **Text and art:** full-HD fanart; characters the skin's fonts can't draw (emoji, text faces, scripts the
  font lacks) are left out of titles instead of showing as boxes.

## Addresses from earlier versions

Other add-ons (Eventvods, Rocket Beans), favourites and `.strm` files made with version 3 use
`plugin://plugin.video.twitch/?mode=...` addresses. These still work:

| Address | Opens |
|---|---|
| `?mode=play&video_id=ID` (`&seek_time=` seconds) | the past broadcast, at that time |
| `?mode=play&channel_name=NAME` or `&channel_id=ID` | the channel's live stream |
| `?mode=play&slug=SLUG` | the clip |
| `?mode=channel_videos&channel_name=NAME` or `&channel_id=ID` | the channel's page |
| `?mode=channel_video_list&broadcast_type=archive\|highlight\|upload&channel_id=ID` | those videos of the channel |
| `?mode=clips_list&channel_id=ID` | the channel's clips |
| `?mode=game_streams&game=NAME`, `?mode=game_lists&game_name=NAME` | the category |
| `?mode=following`, `followed`, `featured_streams`, `stream_list`, `browse`, `games`, `search`, `settings` | the matching page |

Other modes open the main menu.

## How it talks to Twitch

Everything goes through Twitch's GraphQL API with the TV app's client, signed in or not. The one
exception is the lists of followed channels: GraphQL refuses those to this client, so they come from
the Helix API (which is why the sign-in asks for `user:read:follows`), with the details from GraphQL.

## Development

```sh
pip install -r requirements-dev.txt
ruff check .
pytest
```

To build an installable zip for Kodi's **Install from zip file**:

```sh
python scripts/package.py
```

`--debug` builds a zip with `reuselanguageinvoker` turned off, so code copied onto a device takes effect
on the next run.

## Development repository

Pushing a `v*` or `*-dev` tag runs `.gitea/workflows/release-development-repository.yml`: it zips the add-on
and `repository.twitch_development` with `.scripts/.prepare_repository.py` and mirrors them over SFTP (the
`SFTP` secret) to https://download.osmc.tv/dev/anxdpanic/kodi/twitch/python3/, the development
repository's address.

## License

GPL-3.0-only. See [LICENSE](LICENSE).
