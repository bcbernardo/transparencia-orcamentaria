# -*- coding: utf-8 -*-

import unittest
import random
import despesas


class TestMainPage(unittest.TestCase):
    def setUp(self):
        self.main_page = despesas.MainPage()

    def test_driver(self):
        """ Test year when no filter is provided. """
        try:
            self.main_page.driver.find_element_by_id("consulta_dados")
        except Exception as e:
            self.fail("Failed to retrieve database views main page: ", e)

    def test_validate_year(self):
        """ Test whether a valid, previous year, will be validated. """
        try:
            year = random.randrange(2008, 2019)
            year_validated = self.main_page.validate_year(year)
            self.assertIsInstance(year_validated, str)
        except Exception as e:
            self.fail("Unexpected exception raised!: ", e)

    def test_invalidate_bad_year(self):
        """ Test whether an invalid year will raise ValueError. """
        year = "1888"
        with self.assertRaises(ValueError):
            self.main_page.validate_year(year)

    def test_set_year(self):
        """ Test whether a valid, previous year, can be set. """
        try:
            year = random.randrange(2008, 2019)
            self.main_page.set_year(year)
        except Exception as e:
            self.fail("Unexpected exception raised!: ", e)

    def test_validate_period(self):
        """ Test whether a valid time period will be validated. """
        try:
            period = ("0101", "2802")
            period_validated = self.main_page.validate_period(period)
            self.assertIsInstance(period_validated, tuple)
            for date in period_validated:
                self.assertIsInstance(period_validated, str)
        except Exception as e:
            self.fail("Unexpected exception raised!: ", e)

    def test_invalidate_bad_period(self):
        """ Test whether an invalid time period will raise ValueError. """
        period = ("3713", "0211")
        with self.assertRaises(ValueError):
            self.main_page.validate_period(period)

    def test_invalidate_inverted_period(self):
        """
        Test whether a time period with start date > end date will raise
        ValueError.
        """
        period = ("3003", "0102")
        with self.assertRaises(ValueError):
            self.main_page.validate_period(period)

    def test_set_period(self):
        """ Test whether a valid time period can be set. """
        try:
            period = ("0101", "2802")
            self.main_page.set_period(period)
        except Exception as e:
            self.fail("Unexpected exception raised!: ", e)

    def test_access_view(self):
        descriptions = [
            "Despesas por Instituição / Orgão",
            "Despesas por Credor / Instituição",
            "Tipos de Despesas ( Elementos )"]
        try:
            for descr in descriptions:
                self.main_page.access_view(descricao=descr)
                self.setUp()
        except Exception as e:
            self.fail("Unexpected exception raised!: ", e)

    def test_bad_view(self):
        description = "abaopdugbsakjçvb"
        with self.assertRaises(ValueError):
            self.main_page.access_view(descricao=description)


if __name__ == "__main__":
    unittest.main()
