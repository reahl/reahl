# Copyright 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
#-*- encoding: utf-8 -*-
#
#    This file is part of Reahl.
#
#    Reahl is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation; version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.


from reahl.stubble import stubclass
from nose.tools import istest
from reahl.tofu import Fixture, test, scenario, set_up
from reahl.tofu import vassert

from reahl.webdev.tools import XPath
from reahl.web.ui import Panel
from reahl.web_dev.fixtures import WebBasicsMixin
from reahl.component.context import ExecutionContext

from reahl.web.table import DataTable, Column
from reahl.component.modelinterface import Field, IntegerField


class DataItem(object):
    row = None
    alpha = None

    def __init__(self, row, alpha):
        self.row = row
        self.alpha = alpha

        
class TableFixture(Fixture, WebBasicsMixin):

    items_per_page = 3
        
    def new_columns(self):
        return [Column(IntegerField(label=u'Row Number'), u'row', sort_key=lambda i: i.row),
                Column(Field(label=u'Alpha'), u'alpha', sort_key=lambda i: i.alpha)]

    def new_data(self):
        alphas = 'THEQUICKBROWNFXJMPSVLAZYDG'
        return [DataItem(number, alpha) for number, alpha in enumerate(alphas, start=1)]
        #[(1, 'T'), (2, 'H'), (3, 'E'), (4, 'Q'),...(23, 'Z'), (24, 'Y'), (25, 'D'), (26, 'G')]
    
    
    def new_MainWidget(self):
        fixture = self
        class MainWidget(Panel):
            def __init__(self, view):
                super(MainWidget, self).__init__(view)
                   
                fixture.data_table = DataTable(view, 
                                fixture.columns,
                                fixture.data,
                                items_per_page=fixture.items_per_page,
                                caption_text=u'All my friends', 
                                summary=u'Summary for screen reader',
                                css_id=u'my_table_data')
                self.add_child(fixture.data_table)
        return MainWidget

    def new_wsgi_app(self):
        return super(TableFixture, self).new_wsgi_app(enable_js=True, 
                                                      child_factory=self.MainWidget.factory())

    def table_caption_is(self, expected):
        return  self.driver_browser.find_element(XPath.caption_with_text(expected))
        #return self.driver_browser.execute_script('return window.jQuery("table caption").html() == "%s"' % expected)

    def table_summary_is(self, summary):
        return  self.driver_browser.find_element(XPath.table_with_summary(summary))
        #return self.driver_browser.web_driver.find_element_by_xpath('//table').get_attribute("summary") == expected

    def xpath_for_ascending_link_for_column(self, column_number):
        return '(((//table/thead/tr/th)[%s]/span)[2]/a)[1]' % column_number

    def xpath_for_descending_link_for_column(self, column_number):
        return '(((//table/thead/tr/th)[%s]/span)[2]/a)[2]' % column_number
        
    def table_column_name_is(self, column_number, expected):
        #return self.driver_browser.execute_script('return window.jQuery("table thead[%s] span").html() == "%s"' % (column_number, expected))
        return self.driver_browser.web_driver.find_element_by_xpath('((//table/thead/tr/th)[%s]/span)[1]' % column_number).text == expected

    def get_table_row(self, row_number):
        row_data = []
        for column_number in range(1,len(self.columns)+1):
            row_data.append(self.driver_browser.web_driver.find_element_by_xpath('((//table/tbody/tr)[%s]/td)[%s]' % (row_number, column_number)).text)
        return row_data

    def table_has_number_rows(self, expected_number):
        counted_number_of_rows = len(self.driver_browser.web_driver.find_elements_by_xpath('//table/tbody/tr'))
        return counted_number_of_rows == expected_number


@istest
class TableTests(object):

    @test(TableFixture)
    def table_basics(self, fixture):
        """A DataTable displays a list of items as defined by a list of Columns"""
        fixture.reahl_server.set_app(fixture.wsgi_app)
        fixture.driver_browser.open(u'/')

        # The table has a caption and summary
        vassert( fixture.table_caption_is(u'All my friends') )
        vassert( fixture.table_summary_is(u'Summary for screen reader') )

        # Column headings are derived from given Column Fields
        vassert( fixture.table_column_name_is(1, u'Row Number') )
        vassert( fixture.table_column_name_is(2, u'Alpha') )

        # A string representation of the value of each Field of a given data item is shown in the appropriate cell
        vassert( fixture.table_has_number_rows(fixture.items_per_page))

        vassert( fixture.get_table_row(1) == ['1' ,'T'] )
        vassert( fixture.get_table_row(2) == ['2' ,'H'] )
        vassert( fixture.get_table_row(3) == ['3' ,'E'] )


    @test(TableFixture)
    def paging_through_data(self, fixture):
        """DataTable splits its items into different pages (between which a user can navigate), showing only the items of a particular page at a time."""
        fixture.reahl_server.set_app(fixture.wsgi_app)
        fixture.driver_browser.open(u'/')

        #click to last page
        fixture.driver_browser.click(XPath.link_with_text(u'>|'))
        fixture.driver_browser.click(XPath.link_with_text(u'9'))
        
        vassert( fixture.table_has_number_rows(2) )
        vassert( fixture.get_table_row(1) == ['25' ,'D'] )
        vassert( fixture.get_table_row(2) == ['26' ,'G'] )

        #click to page 4
        fixture.driver_browser.click(XPath.link_with_text(u'|<'))
        fixture.driver_browser.click(XPath.link_with_text(u'4'))
        
        vassert( fixture.table_has_number_rows(3) )
        vassert( fixture.get_table_row(1) == ['10' ,'R'] )
        vassert( fixture.get_table_row(2) == ['11' ,'O'] )
        vassert( fixture.get_table_row(3) == ['12' ,'W'] )


    @test(TableFixture)
    def sorting(self, fixture):
        """By clicking on special links in the column header, the table is sorted according to that column - ascending or descending."""
        fixture.reahl_server.set_app(fixture.wsgi_app)
        fixture.driver_browser.open(u'/')

        #----- by default, not sorted
        vassert( fixture.get_table_row(1) == ['1' ,'T'] )
        vassert( fixture.get_table_row(2) == ['2' ,'H'] )
        vassert( fixture.get_table_row(3) == ['3' ,'E'] )
        
        #----- sort ascending on alpha, the second column
        fixture.driver_browser.click(fixture.xpath_for_ascending_link_for_column(2))
        
        vassert( fixture.get_table_row(1) == ['22' ,'A'] )
        vassert( fixture.get_table_row(2) == ['9' ,'B'] )
        vassert( fixture.get_table_row(3) == ['7' ,'C'] )

        #----- sort descending on alpha, the second column
        fixture.driver_browser.click(fixture.xpath_for_descending_link_for_column(2))
        
        vassert( fixture.get_table_row(1) == ['23' ,'Z'] )
        vassert( fixture.get_table_row(2) == ['24' ,'Y'] )
        vassert( fixture.get_table_row(3) == ['15' ,'X'] )

        #----- sort order stays changed when paging
        fixture.driver_browser.click(XPath.link_with_text(u'4'))
        
        vassert( fixture.get_table_row(1) == ['4' ,'Q'] )
        vassert( fixture.get_table_row(2) == ['18' ,'P'] )
        vassert( fixture.get_table_row(3) == ['11' ,'O'] )

        #----- contents of the page you are on changes according to a new sort order
        fixture.driver_browser.click(fixture.xpath_for_ascending_link_for_column(1))
        
        vassert( fixture.get_table_row(1) == ['10' ,'R'] )
        vassert( fixture.get_table_row(2) == ['11' ,'O'] )
        vassert( fixture.get_table_row(3) == ['12' ,'W'] )
        
