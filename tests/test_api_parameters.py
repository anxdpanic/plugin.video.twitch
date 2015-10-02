import unittest

from twitch.api.parameters import (_Parameter, Period, Boolean, Direction,
                                   SortBy)


class TestApiParameters(unittest.TestCase):

    def test_period(self):
        Period.validate(Period.WEEK)
        Period.validate(Period.MONTH)
        Period.validate(Period.ALL)
        Period.validate('week')
        Period.validate('month')
        Period.validate('all')

        with self.assertRaises(ValueError):
            Period.validate(0)
        with self.assertRaises(ValueError):
            Period.validate(-1)
        with self.assertRaises(ValueError):
            Period.validate('')
        with self.assertRaises(ValueError):
            Period.validate('year')
        with self.assertRaises(ValueError):
            Period.validate(9.4124)

    def test_boolean(self):
        Boolean.validate(Boolean.TRUE)
        Boolean.validate(Boolean.FALSE)
        Boolean.validate('true')
        Boolean.validate('false')

        with self.assertRaises(ValueError):
            Boolean.validate(True)
        with self.assertRaises(ValueError):
            Boolean.validate(False)
        with self.assertRaises(ValueError):
            Boolean.validate('')

    def test_direction(self):
        Direction.validate(Direction.DESC)
        Direction.validate(Direction.ASC)
        Direction.validate('desc')
        Direction.validate('asc')

        with self.assertRaises(ValueError):
            Direction.validate(True)
        with self.assertRaises(ValueError):
            Direction.validate(12)
        with self.assertRaises(ValueError):
            Direction.validate('')

    def test_sort_by(self):
        SortBy.validate(SortBy.CREATED_AT)
        SortBy.validate(SortBy.LAST_BROADCAST)
        SortBy.validate(SortBy.LOGIN)

        with self.assertRaises(ValueError):
            SortBy.validate('logoff')
