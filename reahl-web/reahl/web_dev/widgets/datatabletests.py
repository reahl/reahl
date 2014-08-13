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

from __future__ import unicode_literals
from __future__ import print_function

from reahl.tofu import test
from reahl.tofu import vassert

from reahl.webdev.tools import XPath
from reahl.web.ui import Panel, Button, StaticColumn, DynamicColumn
from reahl.web_dev.widgets.tabletests import TableFixture

from reahl.web.table import DataTable
from reahl.component.modelinterface import Field, IntegerField, exposed



class DataItem(object):
    row = None
    alpha = None

    def __init__(self, row, alpha):
        self.row = row
        self.alpha = alpha
    
    @exposed
    def fields(self, fields):
        fields.row = IntegerField(label='Row', required=True, default = self.row)
        fields.alpha = Field(label='Alpha', required=True, default = self.alpha)

        
class DataTableFixture(TableFixture):

    items_per_page = 3
        
    def new_columns(self):
        return [StaticColumn(IntegerField(label='Row Number'), 'row', sort_key=lambda i: i.row),
                StaticColumn(Field(label='Alpha'), 'alpha', sort_key=lambda i: i.alpha),
                ]

    def new_data(self):
        alphas = 'THEQUICKBROWNFXJMPSVLAZYDG'
        return [DataItem(number, alpha) for number, alpha in enumerate(alphas, start=1)]
        #[(1, 'T'), (2, 'H'), (3, 'E'), (4, 'Q'),...(23, 'Z'), (24, 'Y'), (25, 'D'), (26, 'G')]

    def new_MainWidget(self):
        fixture = self
        class MainWidget(Panel):
            def __init__(self, view):
                super(MainWidget, self).__init__(view)

                data_table = DataTable(view,
                                 fixture.columns,
                                 fixture.data,
                                 items_per_page=fixture.items_per_page,
                                 caption_text='All my friends',
                                 summary='Summary for screen reader',
                                 css_id='my_table_data')
                self.add_child(data_table)
        return MainWidget

    def new_wsgi_app(self):
        return super(TableFixture, self).new_wsgi_app(enable_js=True,
                                                      child_factory=self.MainWidget.factory())

    def xpath_for_ascending_link_for_column(self, column_number):
        return '(((//table/thead/tr/th)[%s]/span)[2]/a)[1]' % column_number

    def xpath_for_descending_link_for_column(self, column_number):
        return '(((//table/thead/tr/th)[%s]/span)[2]/a)[2]' % column_number

    def get_table_header(self):
        header_data = []
        for column_number in range(1, len(self.columns)+1):
            header_data.append(self.driver_browser.web_driver.find_element_by_xpath('(//table/thead/tr/th)[%s]' % (column_number)).text)
        return header_data


@test(DataTableFixture)
def paging_through_data(fixture):
    """DataTable splits its items into different pages (between which a user can navigate), showing only the items of a particular page at a time."""
    fixture.reahl_server.set_app(fixture.wsgi_app)
    fixture.driver_browser.open('/')

    #click to last page
    fixture.driver_browser.click(XPath.link_with_text('>|'))
    fixture.driver_browser.click(XPath.link_with_text('9'))
    
    vassert( fixture.table_number_rows() == 2 )
    vassert( fixture.get_table_row(1) == ['25' ,'D'] )
    vassert( fixture.get_table_row(2) == ['26' ,'G'] )

    #click to page 4
    fixture.driver_browser.click(XPath.link_with_text('|<'))
    fixture.driver_browser.click(XPath.link_with_text('4'))
    
    vassert( fixture.table_number_rows() == 3 )
    vassert( fixture.get_table_row(1) == ['10' ,'R'] )
    vassert( fixture.get_table_row(2) == ['11' ,'O'] )
    vassert( fixture.get_table_row(3) == ['12' ,'W'] )


@test(DataTableFixture)
def sorting(fixture):
    """By clicking on special links in the column header, the table is sorted according to that column - ascending or descending."""
    fixture.reahl_server.set_app(fixture.wsgi_app)
    fixture.driver_browser.open('/')

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
    fixture.driver_browser.click(XPath.link_with_text('4'))
    
    vassert( fixture.get_table_row(1) == ['4' ,'Q'] )
    vassert( fixture.get_table_row(2) == ['18' ,'P'] )
    vassert( fixture.get_table_row(3) == ['11' ,'O'] )

    #----- contents of the page you are on changes according to a new sort order
    fixture.driver_browser.click(fixture.xpath_for_ascending_link_for_column(1))
    
    vassert( fixture.get_table_row(1) == ['10' ,'R'] )
    vassert( fixture.get_table_row(2) == ['11' ,'O'] )
    vassert( fixture.get_table_row(3) == ['12' ,'W'] )


@test(DataTableFixture)
def which_columns_can_cause_sorting(fixture):
    """Only columns with sort_key specified are sortable"""

    fixture.columns.append(StaticColumn(Field(label='Not sortable'), 'alpha'))

    fixture.reahl_server.set_app(fixture.wsgi_app)
    fixture.driver_browser.open('/')

    vassert( fixture.get_table_header() == ['Row Number▲▼', 'Alpha▲▼', 'Not sortable'] )

