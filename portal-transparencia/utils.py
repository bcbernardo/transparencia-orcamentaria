# -*- coding: utf-8 -*-

import lxml.html


class JQGrid():
    """ Models a javascript query grid, with method to scrape its contents.

    Attributes:
        page (str): Page source in HTML.
    """

    def __init__(self, page_source: str):
        self.page = lxml.html.fromstring(page_source)
        self.grid = self.page.xpath(
            "//div[@id='main_content']/div[3]")[0]
        self.fields = tuple(elem.text_content() for elem in self.grid.xpath(
            "//thead/tr[@role='rowheader'][1]/th/div"))
        self.rows = self.grid.xpath(
            "//table[@id='list']/tbody/tr[@id!='jqgfirstrow']")
        self.pager = self.page.xpath(
            "//div[@id='pg_pager']/table/tbody/tr")[0]
        self.page_no = self.pager.xpath("//td[@dir='ltr']//text()")
        self.page_no = int(self.page_no[-1])
        self.rows_per_page = self.pager.xpath(
            "//select/option[@selected='selected']/text()")[0]
        self.last_update = self.grid.xpath(
            "//div[@id='data_atualizacao']/text()")[0]

    def get_values(self):
        result = list()
        for r in self.rows:
            row_id = r.get("id")
            row_data = {"id": row_id}
            for i in range(0, len(self.fields)):
                field = self.fields[i]
                value = r.xpath("./td")[i].get("title")
                row_data[field] = value
            result.append(row_data)
        return result


if __name__ == '__main__':
    import sys
    sys.exit()
