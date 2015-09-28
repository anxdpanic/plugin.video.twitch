NO_STREAM_URL = 0
STREAM_OFFLINE = 1
HTTP_ERROR = 2
JSON_ERROR = 3


class TwitchException(Exception):
    def __init__(self, code):
        Exception.__init__(self)
        self.code = code

    def __str__(self):
        return repr(self.code)


class NoStreamUrlException(TwitchException):
    def __init__(self):
        TwitchException.__init__(self, NO_STREAM_URL)


class StreamOfflineException(TwitchException):
    def __init__(self):
        TwitchException.__init__(self, STREAM_OFFLINE)


class HttpException(TwitchException):
    def __init__(self):
        TwitchException.__init__(self, HTTP_ERROR)


class JsonException(TwitchException):
    def __init__(self):
        TwitchException.__init__(self, JSON_ERROR)
