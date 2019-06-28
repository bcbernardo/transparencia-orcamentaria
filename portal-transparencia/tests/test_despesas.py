# -*- coding: utf-8 -*-

import unittest
import random
import despesas


class TestMainPage(unittest.TestCase):
    def setUp(self):
        self.main_page = despesas.MainPage()

    def test_driver(self):
        """ Test driver initialization. """
        try:
            self.main_page.driver.find_element_by_id("consulta_dados")
        except Exception as e:
            self.fail(
                "Failed to retrieve database views main page: {}".format(e))

    def test_validate_year(self):
        """ Test whether a valid, previous year, will be validated. """
        try:
            self.main_page.year = random.randrange(2008, 2019)
            self.main_page.validate_year()
            self.assertIsInstance(self.main_page.year, str)
        except Exception as e:
            self.fail("Unexpected exception raised!: {}".format(e))

    def test_invalidate_bad_year(self):
        """ Test whether an invalid year will raise ValueError. """
        self.main_page.year = "1888"
        with self.assertRaises(ValueError):
            self.main_page.validate_year()

    def test_set_year(self):
        """ Test whether a valid, previous year, can be set. """
        try:
            self.main_page.year = random.randrange(2008, 2019)
            self.main_page.set_year()
        except Exception as e:
            self.fail("Unexpected exception raised!: {}".format(e))

    def test_validate_period(self):
        """ Test whether a valid time period will be validated. """
        try:
            self.main_page.period = ("0101", "2802")
            self.main_page.validate_period()
            self.assertIsInstance(self.main_page.period, tuple)
            for date in self.main_page.period:
                self.assertIsInstance(date, str)
        except Exception as e:
            self.fail("Unexpected exception raised!: {}".format(e))

    def test_invalidate_bad_period(self):
        """ Test whether an invalid time period will raise ValueError. """
        self.main_page.period = ("3713", "0211")
        with self.assertRaises(ValueError):
            self.main_page.validate_period()

    def test_invalidate_inverted_period(self):
        """
        Test whether a time period with start date > end date will raise
        ValueError.
        """
        self.main_page.period = ("3003", "0102")
        with self.assertRaises(ValueError):
            self.main_page.validate_period()

    def test_set_period(self):
        """ Test whether a valid time period can be set. """
        try:
            self.main_page.period = ("0101", "2802")
            self.main_page.set_period()
        except Exception as e:
            self.fail("Unexpected exception raised!: {}".format(e))

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
            self.fail("Unexpected exception raised!: {}".format(e))

    def test_bad_view(self):
        description = "abaopdugbsakjçvb"
        with self.assertRaises(ValueError):
            self.main_page.access_view(descricao=description)


class TestByCreditor(unittest.TestCase):
    def setUp(self):
        _main_page = despesas.MainPage()
        _main_page.access_view("Despesas por Credor / Instituição")
        self.driver = _main_page.driver
        self.view = despesas.ByCreditors(driver=self.driver)

    def test_driver(self):
        """ Test access to correct view page. """
        try:
            self.driver.find_element_by_xpath(
                "//div[contains(string(), 'Credor')]")
        except Exception as e:
            self.fail(
                "Failed to retrieve expenses view by creditor: {}".format(e))

    def test_constructor(self):
        """ Test whether all attributes are set as expected. """
        self.assertEqual(self.view.curr_page, 1)
        self.assertIn("cpf_cnpj", self.view._filter_ids)
        self.assertIn("credor", self.view._filter_ids)

    def test_scrape(self):
        """ Test whether .scrape() method returns any data. """
        scraped = self.view.scrape(stop=3)
        print(len(scraped["results"]))
        self.assertGreater(len(scraped["results"]), 0)


if __name__ == "__main__":
    unittest.main()
