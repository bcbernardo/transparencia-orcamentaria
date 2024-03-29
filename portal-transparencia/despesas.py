# -*- coding: utf-8 -*-

import coloredlogs
import datetime as dt
import logging
import selenium.webdriver
import time
from selenium.common.exceptions import NoSuchElementException
from typing import Tuple
from utils import JQGrid

coloredlogs.install()
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

    def __init__(self, driver: object = selenium.webdriver.Chrome(),
                 exercicio=CURR_YEAR, periodo: tuple = ("", "")):
        logging.debug("Accessing main page")
        self.driver = driver
        self.driver.get(URL)
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
        years_available = [y.text for y in self.driver.find_elements_by_xpath(
            "//select[@id='exercicioConsulta']/option")]

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
            "option[text()='{}']".format(self.year))
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
                             "como uma dupla no formato ('DDMM', 'DDMM'),"
                             "respectivamente.")

    def set_period(self):
        """ Seleciona o período de interesse. """
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
        logging.debug("Accessing dataset view '{}'...".format(descricao))
        try:
            view_link = self.driver.find_element_by_xpath(
                "//a[text()[normalize-space(.)='{}']]".format(descricao))
            view_link.click()
            time.sleep(3)
        except NoSuchElementException:
            logging.exception("No element with given description!")
            raise ValueError("A descrição fornecida não corresponde a"
                             "nenhuma das visualizações disponíveis"
                             "no Portal da Transparência.")


class GenericExpensesView():
    """ Classe genérica de acesso às visões da base de despesas.

    Atributos:
        driver (object): Instância já aberta de um objeto selenium.webdriver
            para raspagem.
        **kwargs (str): Argumentos nomeados opcionais, para filtrar os valores
            consultados.
    """

    def __init__(self, driver: object, **kwargs: str):
        self.driver = driver
        self.curr_page = 1
        self._filter_params = kwargs  # user-provided parameters for filtering
        self._filter_ids = dict()  # {'field name for filtering': 'filterid'}

    @property
    def rows_per_page(self) -> int:
        """ Obtém número de linhas por página na visualização atual.

        Retorna:
            int: O número de linhas por página na visualização atual.
        """
        logging.debug("Getting number of rows per page...")
        rows_xpath = "//table[@id='list']/tbody/tr[@class!='jqgfirstrow']"
        rows_in_view = self.driver.find_elements_by_xpath(rows_xpath)
        return len(rows_in_view)

    @rows_per_page.setter
    def rows_per_page(self, rows: int):
        """ Define o número de linhas retornadas em cada página da consulta

        Argumentos:
            rows (int): Número desejado de linhas por página (10, 20 ou 30).
        Levanta:
            ValueError: se o número fornecido não for o inteiro 10, 20 ou 30.
        """
        logging.debug("Setting number of rows per page...")
        try:
            assert isinstance(rows, int)
            assert rows in [10, 20, 30]
        except AssertionError:
            logging.exception("Invalid number of rows per page.")
            raise ValueError("O número de linhas por página deve ser o número"
                             "inteiro 10, 20 ou 30.")
        else:
            rows_setter_xpath = ("//td[@id='pager_center']//select"
                                 "/option[@value='{:d}']".format(rows))
            rows_setter = self.driver.find_element_by_xpath(rows_setter_xpath)
            rows_setter.click()
            time.sleep(3)

    def _apply_filters(self):
        """ Aplica um filtro para a consulta. """
        for field_name, filter_expression in self._filter_params.items():
            if filter_expression != "":
                element_id = self._filter_ids[field_name]
                input_element = self.driver.find_element_by_id(element_id)
                input_element.send_keys(filter_expression)

    def scrape(self, stop=1000) -> Tuple[dict, dict]:
        """ Raspa dados das tabelas jqGrid, até a última página da consulta.

        Argumentos:
            stop (int, opcional): Número da página máxima até a qual deve ir a
                raspagem. Em geral, não é necessário alterar o padrão (1000).
        Retorna:
            tuple[dict, dict]: Tupla com um dicionário de metadados da raspagem
                e um dicionário com os dados propriamente ditos.
        """
        self.rows_per_page = 30
        metadata = dict()  # TODO
        results = list()
        logging.info("Scraping started...")
        while True:
            time.sleep(3)
            table = JQGrid(page_source=self.driver.page_source)
            logging.info("Scrapping page {:d}/{:d}".format(
                self.curr_page, table.page_no))
            page_results = table.get_values()
            results.extend(page_results)
            if self.curr_page >= table.page_no or self.curr_page >= stop:
                break
            else:
                next_pager = self.driver.find_element_by_id("next_pager")
                next_pager.click()
                self.curr_page += 1
        logging.info("Scraped {:d} rows successfully.".format(len(results)))
        return {"metadata": metadata, "results": results}


class ByCreditors(GenericExpensesView):
    """ Acesso às consultas de despesas por credor.

    Atributos:
        driver (object): Instância já aberta de um objeto selenium.webdriver
            para raspagem.
        cpf_cnpj (str, opcional): Sequência de dígitos contidos no CPF ou
            CNPF do credor, sem pontos ou caracteres especiais. Por padrão,
            vazio.
        credor (str, opcional): Nome completo ou parcial do credor. Por
            padrão, vazio.
    """

    def __init__(self, driver: object, cpf_cnpj: str = "", credor: str = "",
                 **kwargs):
        super().__init__(driver=driver, cpf_cnpj=cpf_cnpj, credor=credor)
        self._filter_ids["cpf_cnpj"] = "gs_cpfcnpj"
        self._filter_ids["credor"] = "gs_nome"
        self._apply_filters()


def main(exercicio: str = CURR_YEAR,
         periodo: Tuple[str, str] = ("", ""),
         cpf_cnpj: str = "", credor: str = ""):
    pass  # TODO


if __name__ == "__main__":
    main()
    raise SystemExit()
