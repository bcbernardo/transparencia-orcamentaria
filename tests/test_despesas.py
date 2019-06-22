# -*- coding: utf-8 -*-

import unittest
import random
from .. import despesas


class TestMainPage(unittest.TestCase):
    def setUp(self):
        self.main_page = despesas.MainPage()

    def test_current_year(self):
        """ Test year when no filter is provided. """
        self.assertEquals(self.year, "2019")

    def test_previous_year(self):
        """ Test whether a valid, previous year, will work. """
        try:
            year = random.randrange(2008, 2019)
            self.main_page_prev = despesas.MainPage(year=str(year))
        except Exception as e:
            self.fail("Unexpected exception raised!:", e)


if __name__ == "__main__":
    unittest.main()
