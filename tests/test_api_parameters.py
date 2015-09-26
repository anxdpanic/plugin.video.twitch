import unittest

from twitch.api.parameters import _Parameter, Period, Boolean


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
