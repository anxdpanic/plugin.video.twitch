# -*- encoding: utf-8 -*-


class _Parameter(object):
    _valid = []

    @classmethod
    def validate(cls, value):
        if value in cls._valid:
            return value
        raise ValueError(value)


class Period(_Parameter):
    WEEK = 'week'
    MONTH = 'month'
    ALL = 'all'
    _valid = [WEEK, MONTH, ALL]


class Boolean(_Parameter):
    TRUE = 'true'
    FALSE = 'false'

    _valid = [TRUE, FALSE]


class Direction(_Parameter):
    DESC = 'desc'
    ASC = 'asc'

    _valid = [DESC, ASC]


class SortBy(_Parameter):
    CREATED_AT = 'created_at'
    LAST_BROADCAST = 'last_broadcast'
    LOGIN = 'login'

    _valid = [CREATED_AT, LAST_BROADCAST, LOGIN]
