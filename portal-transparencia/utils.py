# -*- coding: utf-8 -*-


class JQGrid():
    """ Models a javascript query grid, with method to scrape its contents.

    Attributes:
        page (str): Page source in HTML.
    """

    def __init__(self, page: str):
        self.page = page
        self.grid = page.xpath(
            "//div[@id='main_content']/div[div/@id='gbox_list']")[0]
        self.fields = tuple(f for f in self.grid.xpath(
            "//thead/tr[@class='ui-jqgrid-labels']/th[@role='columnheader']"
            + "/div/text()"))
        self.rows = self.grid.xpath(
            "//table[@id='list']/tbody/tr[@id!='jqgfirstrow']")
        self.pager = page.xpath(
            "//div[@id='pg_pager']/table/tbody/tr")[0]
        self.page_no = self.pager.xpath("//span[@id='sp_1_pager']/text()")
        self.page_no = int(self.page_no[0])
        self.rows_per_page = self.pager.xpath(
            "//select/option[@selected='selected']/text()")[0]
        self.last_update = self.grid.xpath(
            "//div[@id='data_atualizacao']/text()")[0]

    def get_values(self):
        result = list()
        for r in self.rows:
            row_id = r.xpath("/@id")[0]
            row_data = {"id": row_id}
            for i in range(0, len(self.fields)+1):
                field = self.fields[i]
                value = r.xpath("/td[{i}]/text()")[0]
                row_data[field] = value
            result.append(row_data)
        return result


if __name__ == '__main__':
    import sys
    sys.exit()
