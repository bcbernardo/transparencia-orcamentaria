# -*- coding: utf-8 -*-


class JQGrid():
    """ Models a javascript query grid, with method to scrape its contents """
    def __init__(self, page):
        self.page = page
        self.grid = page.xpath(
            "/html/body/div[@id='main_content']/div[div[@id='gbox_list']]")
        self.fields = tuple(f for f in self.grid.xpath(
            "//thead/tr[@class='ui-jqgrid-labels']/th[@role='columnheader']" + 
            "/div/text()"))
        self.rows = self.grid.xpath(
            "//table[@id='list']/tbody/tr[@id!='jqgfirstrow']")
        self.pager = page.xpath("/div[@id='gbox_list']/div[@id='pager']/div"
        self.page_no = self.pager.xpath("//span[@id='sp_1_pager']/text()")
        self_rows_per_page = self.pager.xpath(
            "//select/option[@selected='selected']/text()")
        self.last_update = self.grid("/div[@id=data_atualizacao]")
    
    def get_values(self):
        result = dict()
        for r in self.rows:
            row_id = r.xpath["/@id"]
            row_entries = dict()
            for i in range(0, len(self.fields)):
                field = self.fields[i]
                value = r.xpath("/td[{i}]/text()")
                row_entries[field] = value
            result[row_id] = row_entries
        return result


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
