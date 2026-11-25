# Twitch (plugin.video.twitch)

A Kodi video add-on for Twitch with a TV layout: live channels, past broadcasts, highlights, uploads
and clips, in Kodi's own folders or in a full-screen TV interface. It targets Kodi 21 (Omega) and later.

## Features

- **Two ways to browse:** the add-on's folders in Kodi's video window, using the skin's views, or the TV
  interface, a full-screen window with a navigation rail, the focused tile's details and rows of tiles.
- **Pages:** Home (live channels you follow, top live channels, top categories), Following, Categories,
  a category's live channels, clips and videos, a channel's live stream, past broadcasts, highlights,
  uploads and clips, and search across live channels, channels and categories.
- **Sign-in:** a code at twitch.tv/activate (with a QR code), as Twitch's TV app. Several accounts can be
  signed in. Turbo and subscriber benefits come with the sign-in.
- **Playback:** live streams and past broadcasts as HLS through InputStream Adaptive, clips as MP4.
  Optional H.265 and AV1, and an option to choose the quality each time.

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

## License

GPL-3.0-only. See [LICENSE](LICENSE).
