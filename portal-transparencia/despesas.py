# -*- coding: utf-8 -*-

import datetime as dt
import logging
import lxml.html
import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from typing import Tuple
from utils import JQGrid

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

URL = "http://portais.niteroi.rj.gov.br/portal-da-transparencia/despesas"
CURR_YEAR = str(dt.datetime.now().year)


class MainPage():
    """ Acesso à página principal de despesas do Portal da Transparência

    Atributos:
        exercicio (opcional): Ano do exercício fiscal (valor inteiro ou
            texto). Por padrão,é o ano corrente.
        periodo (tuple, opcional): Periodo do ano para consulta, em
            formato 'DDMM'. Por padrão, inclui todo o período transcorrido.
    """

    def __init__(self, driver: object = webdriver.Chrome(),
                 exercicio=CURR_YEAR, periodo: tuple = ("", "")):
        logging.debug("Accessing main page")
        self.driver = driver
        self.driver.get(URL)
        self.page = lxml.html.fromstring(self.driver.page_source)
        # optionally change year for the query
        self.year = exercicio
        if self.year != CURR_YEAR:
            self.validate_year()
            self.set_year()
        # optionally set a time interval for the query
        self.period = periodo
        if self.period != ("", ""):
            self.validate_period()
            self.set_period()
        logging.debug("Main page contents returned sucessfully.")

    def validate_year(self):
        """ Valida o ano do exercício.

        Levanta:
            ValueError: Se o ano informado como `exercicio` não
                estiver listado no Portal da Transparência.
        """
        logging.debug("Validating fiscal year...")
        self.year = str(self.year)
        years_available = self.page.xpath(
            "//select[@id='exercicioConsulta']/option/text()")
        try:
            assert self.year in years_available
        except AssertionError:
            logging.exception("Invalid year: {}".format(self.year))
            raise ValueError("O ano deve estar entre {} e {}!".format(
                years_available[0], years_available[-1]))

    def set_year(self):
        """ Seleciona o ano do exercício fiscal. """
        logging.debug("Setting fiscal year filter...")
        year_field = self.driver.find_element_by_xpath(
            "//select[@id='exercicioConsulta']/"
            + "option[text()='{}']".format(self.year))
        year_field.click()

    def validate_period(self):
        """ Valida o período informado.

        Levanta:
            ValueError: Se `period` não for uma dupla de datas válidas,
                no formato ('DDMM', 'DDMM'), ou se a data de início for
                posterior à data do final do período.
        """
        logging.debug("Validating time period...")
        try:
            self.period = tuple(str(ddmm) for ddmm in self.period)
            assert len(self.period) == 2
            start_date, end_date = self.period[0], self.period[1]
            assert int(start_date[0:1]) <= 31 and int(start_date[2:3]) <= 12
            assert int(end_date[0:1]) <= 31 and int(end_date[2:3]) <= 12
            assert end_date[2:3] + end_date[0:1] \
                > start_date[2:3] + start_date[0:1]
        except (TypeError, ValueError, IndexError, AssertionError):
            logging.exception("Invalid period: {}".format(str(self.period)))
            raise ValueError("As datas de início e fim devem ser informadas"
                             + "como uma dupla no formato ('DDMM', 'DDMM'),"
                             + "respectivamente.")

    def set_period(self):
        """ Seleciona o período de interesse.

        Retorna:
            object: WebDriver com filtro de período configurado.
        """
        logging.debug("Setting period filter...")
        start_date_field = self.driver.find_element_by_id("periodoInicio")
        start_date_field.send_keys(str(self.period[0]))
        end_date_field = self.driver.find_element_by_id("periodoFim")
        end_date_field.send_keys(str(self.period[1]))

    def access_view(self, descricao: str):
        """Acessa a 1ª página de um dos modos de visualização de despesas.

        Args:
            descricao (str): Descrição por extenso da visão desejada.
        """
        logging.debug("Accessing dataset view '{description}'...")
        try:
            view_link = self.driver.find_element_by_xpath(
                "//a[text()[normalize-space(.)='{}']]".format(descricao))
            view_link.click()
        except NoSuchElementException:
            logging.exception("No element with given description!")
            raise ValueError("A descrição fornecida não corresponde a"
                             + "nenhuma das visualizações disponíveis"
                             + "no Portal da Transparência.")


class GenericExpensesView():
    """ Classe genérica de acesso às visões da base de despesas.

    Atributos:
        driver (object): Instância já aberta de WebDriver para raspagem.
    """

    _filters = []  # list of filter methods

    def __init__(self, driver: str, **kwargs):
        self.driver = driver
        self.curr_page = 1
        self.apply_filters(**kwargs)

    def apply_filters(self, **kwargs):
        """ Aplica filtros opcionais para a consulta.

        Consulte as implementações específicas pelas subclasses.

        Argumentos:
            **kwargs: Argumentos nomeados opcionais para aplicar filtros.
        """
        for filter in self._filters:
            filter(**kwargs)

    def rows_per_page(self, rows=10):
        raise NotImplementedError()  # TODO

    def scrape(self) -> Tuple[dict, dict]:
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
        return {"metadata": metadata, "results": results}


class ByCreditors(GenericExpensesView):
    """ Acesso às consultas de despesas por credor.

    Atributos:
        driver (object): Instância já aberta de WebDriver para raspagem.
        cpf_cnpj (str, opcional): Sequência de dígitos contidos no CPF ou
            CNPF do credor, sem pontos ou caracteres especiais. Por padrão,
            vazio.
        credor (str, opcional): Nome completo ou parcial do credor. Por
            padrão, vazio.
        ** kwargs : argumentos
    """

    def __init__(self, driver: object, cpf_cnpj: str = "",
                 credor: str = "", **kwargs):
        super().__init__(driver=driver, **kwargs)
        self.cpf_cnpj = cpf_cnpj
        self.creditor = credor
        # optionally filter for CPF/CNPJ
        self.cpf_cnpj = cpf_cnpj
        if self.cpf_cnpj != "":
            self.filter_cpf_cnpj()
        # optionally filter for creditor name
        self.creditor = credor
        if self.creditor != "":
            self.filter_creditor()

        def filter_cpf_cnpj(self):  # TODO
            logging.debug("Setting CPF/CNPJ filter...")
            raise NotImplementedError

        def filter_creditor(self):  # TODO
            logging.debug("Setting Creditor filter...")
            raise NotImplementedError


def main(exercicio: str = CURR_YEAR,
         periodo: Tuple[str, str] = ("", ""),
         cpf_cnpj: str = "", credor: str = ""):
    logging.debug("Starting headless browser...")
    driver = webdriver.Chrome()
    logging.debug("Browser OK!")
    main_page = MainPage(
        driver=driver, exercicio=exercicio, periodo=periodo)
    raise NotImplementedError()  # TODO


if __name__ == "__main__":
    main()
    raise SystemExit()
