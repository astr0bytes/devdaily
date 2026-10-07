import unittest
from datetime import date

from devdaily.period import last_workday, parse_since

FRIDAY = date(2026, 10, 9)
MONDAY = date(2026, 10, 12)


class LastWorkdayTest(unittest.TestCase):
    def test_monday_goes_back_to_friday(self):
        self.assertEqual(last_workday(MONDAY), FRIDAY)

    def test_sunday_goes_back_to_friday(self):
        self.assertEqual(last_workday(date(2026, 10, 11)), FRIDAY)

    def test_other_days_use_previous_day(self):
        self.assertEqual(last_workday(FRIDAY), date(2026, 10, 8))
        self.assertEqual(last_workday(date(2026, 10, 13)), MONDAY)


class ParseSinceTest(unittest.TestCase):
    def test_keywords(self):
        self.assertEqual(parse_since("today", FRIDAY), FRIDAY)
        self.assertEqual(parse_since("Yesterday", FRIDAY), date(2026, 10, 8))

    def test_relative(self):
        self.assertEqual(parse_since("3d", FRIDAY), date(2026, 10, 6))
        self.assertEqual(parse_since("2w", FRIDAY), date(2026, 9, 25))
        self.assertEqual(parse_since("1 w", FRIDAY), date(2026, 10, 2))

    def test_iso_date(self):
        self.assertEqual(parse_since("2026-09-01", FRIDAY), date(2026, 9, 1))

    def test_invalid(self):
        with self.assertRaises(SystemExit):
            parse_since("last tuesday", FRIDAY)


if __name__ == "__main__":
    unittest.main()
