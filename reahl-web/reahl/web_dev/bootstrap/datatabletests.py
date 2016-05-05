# Copyright 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from __future__ import print_function, unicode_literals, absolute_import, division

import six

from reahl.tofu import test, vassert, expected, scenario

from reahl.webdev.tools import XPath
from reahl.component.modelinterface import Field, IntegerField, exposed

from reahl.web_dev.fixtures import WebFixture

from reahl.web.bootstrap.ui import Div
from reahl.web.bootstrap.tables import StaticColumn, TableLayout, DataTable

import reahl.web_dev.widgets.tabletests


class DataItem(reahl.web_dev.widgets.tabletests.DataItem):
    @exposed
    def fields(self, fields):
        fields.row = IntegerField(label='Row', required=True, default=self.row)
        fields.alpha = Field(label='Alpha', required=True, default=self.alpha)


class DataTableFixture(reahl.web_dev.widgets.tabletests.TableFixture):

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
        class MainWidget(Div):
            def __init__(self, view):
                super(MainWidget, self).__init__(view)

                data_table = DataTable(view, fixture.columns, fixture.data,
                                       items_per_page=fixture.items_per_page,
                                       caption_text='All my friends',
                                       summary='Summary for screen reader',
                                       css_id='my_table_data')
                self.add_child(data_table)
        return MainWidget

    def new_wsgi_app(self):
        return super(DataTableFixture, self).new_wsgi_app(enable_js=False,
                                                      child_factory=self.MainWidget.factory())

    def new_webconfig(self):
        webconfig = super(DataTableFixture, self).new_webconfig()
        webconfig.frontend_libraries.enable_experimental_bootstrap()
        return webconfig

    def xpath_for_sort_link_for_column(self, column_number):
        return '(//table/thead/tr/th)[%s]/a' % column_number

    def does_column_have_sort_link(self, column_number):
        column_header = self.driver_browser.web_driver.find_element_by_xpath('(//table/thead/tr/th)[%s]' % (column_number))
        return len(column_header.find_elements_by_tag_name('a')) == 1
        
    def is_column_sorted(self, column_number, direction):
        header_link = self.driver_browser.web_driver.find_element_by_xpath('(//table/thead/tr/th)[%s]/a' % (column_number))
        if direction:
            expected_class = 'sorted-%s' % direction
            return expected_class in header_link.get_attribute('class').split(' ')
        else:
            return all([expected_class not in header_link.get_attribute('class').split(' ') 
                        for expected_class in ['sorted-ascending','sorted-descending']])



@test(DataTableFixture)
def paging_through_data(fixture):
    """DataTable splits its items into different pages (between which a user can navigate), showing only the items of a particular page at a time."""
    fixture.reahl_server.set_app(fixture.wsgi_app)
    fixture.driver_browser.open('/')

    #click to last page
    fixture.driver_browser.click(XPath.link_with_text('→'))
    fixture.driver_browser.click(XPath.link_with_text('9'))
    
    vassert( fixture.table_number_rows() == 2 )
    vassert( fixture.get_table_row(1) == ['25' ,'D'] )
    vassert( fixture.get_table_row(2) == ['26' ,'G'] )

    #click to page 4
    fixture.driver_browser.click(XPath.link_with_text('←'))
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
    vassert( not fixture.is_column_sorted(1, 'ascending') )
    vassert( not fixture.is_column_sorted(1, 'descending') )
    vassert( not fixture.is_column_sorted(2, 'ascending') )
    vassert( not fixture.is_column_sorted(2, 'descending') )

    #----- first click on column sorts ascending
    fixture.driver_browser.click(fixture.xpath_for_sort_link_for_column(1))
    vassert( fixture.is_column_sorted(1, 'ascending') )
    vassert( fixture.get_table_row(1) == ['1' ,'T'] )
    vassert( fixture.get_table_row(2) == ['2' ,'H'] )
    vassert( fixture.get_table_row(3) == ['3' ,'E'] )
    
    #----- sort ascending on alpha, the second column
    vassert( fixture.is_column_sorted(2, None) )
    fixture.driver_browser.click(fixture.xpath_for_sort_link_for_column(2))
    vassert( fixture.is_column_sorted(2, 'ascending') )
    vassert( fixture.is_column_sorted(1, None) )
    
    vassert( fixture.get_table_row(1) == ['22' ,'A'] )
    vassert( fixture.get_table_row(2) == ['9' ,'B'] )
    vassert( fixture.get_table_row(3) == ['7' ,'C'] )

    #----- sort descending on alpha, the second column
    fixture.driver_browser.click(fixture.xpath_for_sort_link_for_column(2))
    vassert( fixture.is_column_sorted(2, 'descending') )
    
    vassert( fixture.get_table_row(1) == ['23' ,'Z'] )
    vassert( fixture.get_table_row(2) == ['24' ,'Y'] )
    vassert( fixture.get_table_row(3) == ['15' ,'X'] )

    #----- sort order stays changed when paging
    fixture.driver_browser.click(XPath.link_with_text('4'))
    
    vassert( fixture.get_table_row(1) == ['4' ,'Q'] )
    vassert( fixture.get_table_row(2) == ['18' ,'P'] )
    vassert( fixture.get_table_row(3) == ['11' ,'O'] )

    #----- contents of the page you are on changes according to a new sort order
    fixture.driver_browser.click(fixture.xpath_for_sort_link_for_column(1))
    
    vassert( fixture.get_table_row(1) == ['10' ,'R'] )
    vassert( fixture.get_table_row(2) == ['11' ,'O'] )
    vassert( fixture.get_table_row(3) == ['12' ,'W'] )


@test(DataTableFixture)
def which_columns_can_cause_sorting(fixture):
    """Only columns with sort_key specified are sortable."""

    fixture.columns.append(StaticColumn(Field(label='Not sortable'), 'alpha'))

    fixture.reahl_server.set_app(fixture.wsgi_app)
    fixture.driver_browser.open('/')

    vassert( fixture.does_column_have_sort_link(1) )
    vassert( fixture.does_column_have_sort_link(2) )
    vassert( not fixture.does_column_have_sort_link(3) )


@test(DataTableFixture)
def layout_for_contained_table(fixture):
    """You can specify a Layout to use for the actual table inside the DataTable."""

    layout = TableLayout()
    data_table = DataTable(fixture.view, fixture.columns, fixture.data, 'my_css_id', table_layout=layout)

    vassert( data_table.table.layout is layout )




