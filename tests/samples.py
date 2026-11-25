"""GraphQL nodes as Twitch returns them (trimmed), for the tests."""

STREAM = {
    'id': '318474441316', 'title': 'Speedrun practice', 'viewersCount': 42066, 'createdAt': '2026-11-25T10:00:00Z',
    'previewImageURL': 'https://static-cdn.jtvnw.net/previews-ttv/live_user_runner-1280x720.jpg',
    'game': {'name': 'Celeste', 'displayName': 'Celeste'},
    'broadcaster': {'login': 'runner', 'displayName': 'Runner', 'profileImageURL': 'https://cdn/runner.png'},
}
USER_STREAM = {k: v for k, v in STREAM.items() if k != 'broadcaster'}
VIDEO = {
    'id': '2939600059', 'title': 'Day 2', 'lengthSeconds': 3725, 'viewCount': 228366,
    'publishedAt': '2026-11-24T19:18:20Z', 'broadcastType': 'ARCHIVE',
    'previewThumbnailURL': 'https://static-cdn.jtvnw.net/cf_vods/x/thumb/thumb0-1280x720.jpg',
    'game': {'name': 'Celeste', 'displayName': 'Celeste'},
    'owner': {'login': 'runner', 'displayName': 'Runner', 'profileImageURL': 'https://cdn/runner.png'},
}
CLIP = {
    'id': '1242550613', 'slug': 'FunnyClipSlug', 'title': 'Big jump', 'viewCount': 3455,
    'createdAt': '2026-11-23T22:51:00Z', 'durationSeconds': 21, 'thumbnailURL': 'https://cdn/clip.jpg',
    'game': {'name': 'Celeste', 'displayName': 'Celeste'},
    'broadcaster': {'login': 'runner', 'displayName': 'Runner', 'profileImageURL': 'https://cdn/runner.png'},
}
USER = {
    'id': '1', 'login': 'runner', 'displayName': 'Runner', 'description': 'Fast runs.',
    'profileImageURL': 'https://cdn/runner.png', 'offlineImageURL': 'https://cdn/offline.jpg',
    'bannerImageURL': None, 'followers': {'totalCount': 12500}, 'stream': None,
}
GAME = {'id': '1', 'name': 'Celeste', 'displayName': 'Celeste', 'viewersCount': 3200,
        'boxArtURL': 'https://cdn/celeste-285x380.jpg', 'tags': [{'localizedName': 'Platformer'}]}


def connection(nodes, more=False):
    return {'edges': [{'cursor': 'c%d' % i, 'node': n} for i, n in enumerate(nodes)],
            'pageInfo': {'hasNextPage': more}}
