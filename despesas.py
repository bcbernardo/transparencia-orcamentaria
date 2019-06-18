# -*- coding: utf-8 -*-

import datetime as dt
import logging
import lxml
import selenium
import time
from utils import JQGrid

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

BASE_URL = "http://portais.niteroi.rj.gov.br"
CURR_YEAR = int(dt.datetime.now().year)


class MainPage():
    """ Acesso à página principal de despesas do Portal da Transparência

    Atributos:
        exercicio (str, opcional): Ano do exercício fiscal. Por padrão,
            é o ano corrente.
        periodo (tuple[str, str], opcional): Periodo do ano para consulta, em
            formato 'DDMM'. Por padrão, inclui todo o período transcorrido.
    """

    def __init__(self, exercicio: str = CURR_YEAR,
                 periodo: tuple[str, str] = ("", "")):
        self.year = exercicio
        self.period = periodo

        # set up web driver
        logging.debug("Starting headless browser...")
        self.driver = selenium.webdriver.Chrome()
        logging.debug("Browser OK!")

        # access main page
        self.url = BASE_URL + "/portal-da-transparencia/despesas"
        logging.debug("Acessing {self.url}...")
        self.driver.get(BASE_URL + "/portal-da-transparencia/despesas")

        # optionally change year or set a time interval for the query
        if self.year != CURR_YEAR:
            logging.debug("Setting year filter...")
            self.set_year()
        if self.period != ("", ""):
            logging.debug("Setting period filter...")
            self.set_period()

        # get main page contents
        self.page = lxml.html.fromstring(self.driver.page_source)
        logging.debug("Main page contents returned sucessfully!")

    def set_year(self):
        """ Seleciona o ano do exercício fiscal.

        Levanta:
            ValueError: Se o ano informado como `exercicio` não
                estiver listado no Portal da Transparência.
        """
        # make sure the given year is valid and available in the portal
        years_available = self.page.xpath(
            "//select[@id='exercicioConsulta']/option/text()")
        try:
            assert self.year in years_available
        except AssertionError:
            logging.exception("Invalid year: {self.year}")
            raise ValueError("O ano deve estar entre {years_available[0]} "
                             + "e {years_available[1]}.")
        # select the given year
        year_field = self.driver.find_element_by_xpath(
            "//select[@id='exercicioConsulta']/"
            + "option[@text()={self.year}]")
        year_field.click()
        return

    def set_period(self):
        """ Seleciona o período de interesse.

        Levanta:
            ValueError: Se o `periodo` informado não for uma dupla de datas
                válidas, no formato ('DDMM', 'DDMM'), ou se a data de início
                for posterior à data do final do período.
        """
        # validate the given period
        try:
            self.period = str(ddmm for ddmm in self.period)
            start_date, end_date = self.period[0], self.period[1]
            assert int(start_date[0:1]) <= 31 and int(start_date[2:3]) <= 12
            assert int(end_date[0:1]) <= 31 and int(end_date[2:3]) <= 12
            assert end_date[2:3] + end_date[0:1] \
                > start_date[2:3] + start_date[0:1]
        except (TypeError, ValueError, IndexError, AssertionError):
            logging.exception("Invalid period: {str(self.period)}")
            raise ValueError("As datas de início e fim devem ser informadas"
                             + "como uma dupla no formato ('DDMM', 'DDMM'),"
                             + "respectivamente.")
        # set time filter
        start_date_field = self.driver.find_element_by_id("periodoInicio")
        start_date_field.send_keys(str(self.period[0]))
        end_date_field = self.driver.find_element_by_id("periodoFim")
        end_date_field.send_keys(str(self.period[0]))
        return


class GenericExpensesView():
    """ Classe genérica de acesso às visões da base de despesas.

    Atributos:
        descricao (str): Descrição por extenso da visão desejada.
        **kwargs: Argumentos opcionais *exercicio* e *periodo* para
            restringir a consulta (a serem passados para a classe
            :class:`MainPage`).
    """

    def __init__(self, descricao: str, **kwargs):
        # access home list of views
        logging.debug("Redirecting to Main Page by default...")
        main_page = MainPage(kwargs)
        self.driver = main_page.driver
        # access view page
        self.description = descricao
        logging.debug("Accessing dataset view '{self.description}'...")
        view_link = self.driver.find_element_by_xpath(
            "[@text()={self.description}]")
        view_link.click()
        self.curr_page = 1

    def scrape(self) -> tuple[dict, dict]:
        """ Raspa dados das tabelas jqGrid, até a última página da consulta.

        Retorna:
            tuple[dict, dict]: Tupla com um dicionário de metadados da raspagem
                e um dicionário com os dados propriamente ditos.
        """
        logging.info("Scraping started...")
        metadata = {}  # TODO
        results = dict()
        while True:
            time.sleep(3)
            self.page = lxml.html.fromstring(self.driver.page_source)
            table = JQGrid(self.page)
            logging.info("Scrapping page {self.curr_page}/{table.page_no}")
            page_results = table.get_values()
            results.update(page_results)
            if self.curr_page >= table.page_no:
                break
            else:
                next_pager = self.driver.find_element_by_xpath(
                    "//td[@id='next_pager']")
                next_pager.click()
                self.curr_page += 1
        logging.info("Scraped {len(results)} rows successfully.")
        return (metadata, results)


class ByCreditors(GenericExpensesView):
    """ Acesso às consultas de despesas por credor.

    Atributos:
        cpf_cnpj (str, opcional): Sequência de dígitos contidos no CPF ou CNPF
            do credor, sem pontos ou caracteres especiais. Por padrão, vazio.
        credor (str, opcional): Nome completo ou parcial do credor. Por padrão,
            vazio.
        ** kwargs : argumentos
    """

    def __init__(self, cpf_cnpj: str = "", credor: str = "", **kwargs):
        super().__init__("Despesas por Credor / Instituição", kwargs)
        self.cpf_cnpj = cpf_cnpj
        self.creditor = credor
        # optionally filter for CPF/CNPJ and/or creditor
        if self.cpf_cnpj != "":
            logging.debug("Setting CPF/CNPJ filter...")
            self.filter_cpf_cnpj
        if self.creditor != "":
            logging.debug("Setting Creditor filter...")
            self.filter_creditor
        # get values
        self.data = super().scrape()

        def filter_cpf_cnpj(self):  # TODO
            raise NotImplementedError

        def filter_creditor(self):  # TODO
            raise NotImplementedError


def main():
    raise NotImplementedError()  # TODO


if __name__ == "__main__":
    main()
