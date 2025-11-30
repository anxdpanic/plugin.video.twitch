# Twitch on Kodi - AI Coding Agent Instructions

## Project Overview

This is a Kodi video addon for streaming Twitch content (live streams, VODs, clips). The addon is written in Python 3 (Kodi 20+ Nexus) and integrates with the Twitch API via the separate `script.module.python.twitch` module.

## Architecture

### Core Components

- **Entry Points**: `addon_runner.py` (plugin) and `service_runner.py` (background service)
  - Both set HTTP/HTTPS proxy environment variables early in execution
  - Import from `twitch_addon/` package which is added to `sys.path`

- **Router Pattern**: `router.py` uses `URL_Dispatcher` decorator pattern to map modes to route handlers
  - Routes registered with `@dispatcher.register(MODES.MODE_NAME, args=['required'], kwargs=['optional'])`
  - All routes wrapped with `@error_handler` decorator (optionally `route_type=1` for directory routes)
  - Routes lazy-load their implementations: `from .routes import module_name`

- **Routes**: Individual handlers in `routes/` directory (e.g., `main.py`, `play.py`, `streams.py`)
  - Each has a `route(api, ...)` function that builds Kodi directory listings via `kodi.create_item()`
  - Routes call `api.*` methods (Twitch API wrapper) and use converters to transform responses

- **API Layer**: `addon/api.py` contains `Twitch` class wrapping `script.module.python.twitch`
  - Manages OAuth tokens, validates scopes, handles app/user authentication
  - API methods decorated with `@cache.cache_method(cache_limit=N)` for caching
  - Imports from external module: `from twitch import queries, oauth`, `from twitch.api import helix, usher`

- **Kodi Abstraction**: `addon/common/kodi.py` wraps `xbmcaddon`, `xbmcplugin`, `xbmcgui`, `xbmc`
  - Use these wrappers instead of direct Kodi imports for consistency
  - Example: `kodi.create_item()`, `kodi.Dialog()`, `kodi.get_setting()`

- **Background Service**: `service.py` runs notifications thread for live stream alerts
  - Uses `kodi.Window(10000)` for inter-process communication with properties

## Key Patterns & Conventions

### Route Registration
```python
@dispatcher.register(MODES.MODE_NAME, args=['required_arg'], kwargs=['optional_arg'])
@error_handler(route_type=1)  # route_type=1 for directory listings
def _handler_name(required_arg, optional_arg='default'):
    from .routes import module
    module.route(twitch_api, required_arg, optional_arg)
```

### Error Handling
- All routes use `@error_handler` which catches Twitch exceptions and shows Kodi notifications
- Custom exceptions in `twitch_exceptions.py`: `SubRequired`, `NotFound`, `PlaybackFailed`, `TwitchException`
- API errors caught and user-friendly messages displayed via `kodi.notify()`

### Caching
- Decorator-based caching via `@cache.cache_method(cache_limit=N)` on API methods
- Cache duration set in `addon/cache.py` from user setting `cache_expire_time`
- Cache stored in `addon/common/cache.py`

### OAuth Token Management
- Tokens stored via `utils.get_oauth_token()` and validated with scope checking
- Two token types: user OAuth token and private OAuth token (for following games)
- Token validation in `api.valid_token()` checks client_id match and required scopes
- Scopes defined in `constants.py` as `SCOPES = scopes` (imported from `twitch.oauth.helix`)

### Settings
- Settings defined in `resources/settings.xml` as Kodi XML format
- Access via `kodi.get_setting('setting_id')` and `kodi.set_setting('setting_id', value)`
- Menu visibility controlled by boolean settings like `menu_browse_live`, `menu_following_channels`

### Converters
- `converter.py` contains `JsonListItemConverter` to transform API JSON to Kodi ListItems
- Methods like `game_to_listitem()`, `stream_to_listitem()` create uniform display items
- Uses `TitleBuilder` for configurable title formatting based on user preferences

### Internationalization
- All user-facing strings via `i18n('string_id')` function (from `utils.py`)
- String IDs mapped in `strings.py` as `STRINGS` dict
- Multiple language packs in `resources/language/resource.language.*/`

## Development Workflow

### Testing & Validation
- **No unit tests exist** in this codebase - testing is manual via Kodi
- CI validation uses `kodi-addon-checker` in `.github/workflows/addon-validations.yml`
- Run locally: `kodi-addon-checker plugin.video.twitch --branch=nexus`

### Making Changes
1. Modify code in `resources/lib/twitch_addon/`
2. Test by installing as zip in Kodi or symlinking to Kodi's addons directory
3. Check Kodi logs for errors: `log_utils.log(msg, log_utils.LOGLEVEL)`
4. Increment version in `addon.xml` and document in `changelog.txt`

### Dependencies
- **External**: `script.module.requests`, `script.module.python.twitch` (declared in `addon.xml`)
- **Kodi modules**: `xbmc`, `xbmcaddon`, `xbmcplugin`, `xbmcgui`, `xbmcvfs`
- Minimum Kodi version: 20.0 (Nexus), Python 3.8+

### Release Process
- CI workflows automate releases: `make-release.yml`, `submit-release.yml`
- Translations managed via Weblate: `sync-addon-metadata-translations.yml`
- Contributors list auto-updated: `contributors.yml`

## Common Gotchas

- **Proxy handling**: Always set both uppercase and lowercase env vars (`HTTP_PROXY` and `http_proxy`)
- **Route types**: Directory routes need `@error_handler(route_type=1)` and must call `kodi.end_of_directory()`
- **Lazy imports**: Routes use `from .routes import module` inside functions to avoid circular imports
- **Token validation**: New OAuth tokens required when API scopes change (e.g., Helix migration)
- **InputStream Adaptive**: Video quality setting requires checking for InputStream Adaptive addon availability
- **Path handling**: Use `kodi.translate_path()` for Kodi paths, not `os.path` directly

## File Organization

```
resources/
  lib/
    addon_runner.py          # Plugin entry point
    service_runner.py        # Service entry point
    twitch_addon/
      router.py              # URL dispatcher & route registration
      service.py             # Background service (notifications)
      addon/
        api.py               # Twitch API wrapper
        utils.py             # Utilities & i18n
        constants.py         # Modes, keys, configs
        converter.py         # JSON to ListItem converters
        error_handling.py    # Exception handling decorators
        common/              # Kodi abstraction layer
          kodi.py
          url_dispatcher.py
          cache.py
      routes/                # Individual route handlers
        main.py, play.py, streams.py, etc.
  settings.xml             # Addon settings definition
  language/                # Translation files
```
