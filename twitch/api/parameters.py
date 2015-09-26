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
