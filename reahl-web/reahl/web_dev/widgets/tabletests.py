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

from reahl.stubble import EmptyStub
from reahl.tofu import Fixture, test, scenario
from reahl.tofu import vassert

from reahl.webdev.tools import XPath, WidgetTester
from reahl.web.ui import StaticColumn, DynamicColumn, Table, Span, Panel, P
from reahl.web_dev.fixtures import WebBasicsMixin, WebFixture

from reahl.component.modelinterface import Field, BooleanField


class DataItem(object):
    def __init__(self, row, alpha):
        self.row = row
        self.alpha = alpha


class TableFixture(Fixture, WebBasicsMixin):
    def new_data(self):
        return [DataItem(1, 'T'), DataItem(2, 'H'), DataItem(3, 'E')]

    def table_caption_is(self, expected):
        return  self.driver_browser.find_element(XPath.caption_with_text(expected))

    def table_summary_is(self, summary):
        return  self.driver_browser.find_element(XPath.table_with_summary(summary))

    def table_column_name_is(self, column_number, expected):
        return self.driver_browser.web_driver.find_element_by_xpath('((//table/thead/tr/th)[%s]/span)[1]' % column_number).text == expected

    def get_table_row(self, row_number):
        row_data = []
        for column_number in range(1,self.table_number_columns()+1):
            row_data.append(self.driver_browser.web_driver.find_element_by_xpath('((//table/tbody/tr)[%s]/td)[%s]' % (row_number, column_number)).text)
        return row_data

    def table_number_columns(self):
        return len(self.driver_browser.web_driver.find_elements_by_xpath('//table/thead/tr/th'))

    def table_number_rows(self):
        return len(self.driver_browser.web_driver.find_elements_by_xpath('//table/tbody/tr'))


@test(TableFixture)
def table_basics(fixture):
    """A Table created .from_columns() displays a list of items as defined by a list of Columns"""

    class MainWidget(Panel):
        def __init__(self, view):
            super(MainWidget, self).__init__(view)
            table = Table.from_columns(view, 
                            [StaticColumn(Field(label='Row Number'), 'row'),
                             StaticColumn(Field(label='Alpha'), 'alpha')],
                            fixture.data,
                            caption_text='All my friends',
                            summary='Summary for screen reader',
                            css_id='my_table_data'
                            )
            self.add_child(table)

    wsgi_app = fixture.new_wsgi_app(enable_js=True, child_factory=MainWidget.factory())
    fixture.reahl_server.set_app(wsgi_app)
    fixture.driver_browser.open('/')
        
    # The table has a caption and summary
    vassert( fixture.table_caption_is('All my friends') )
    vassert( fixture.table_summary_is('Summary for screen reader') )

    # Column headings are derived from given Column Fields
    vassert( fixture.table_column_name_is(1, 'Row Number') )
    vassert( fixture.table_column_name_is(2, 'Alpha') )

    # A string representation of the value of each Field of a given data item is shown in the appropriate cell
    vassert( fixture.table_number_rows() == 3 )

    vassert( fixture.get_table_row(1) == ['1' ,'T'] )
    vassert( fixture.get_table_row(2) == ['2' ,'H'] )
    vassert( fixture.get_table_row(3) == ['3' ,'E'] )


class ColumnFixture(WebFixture):
    sort_key = EmptyStub()
    heading = 'A heading'
    row_item = EmptyStub(some_attribute=True)
    
    @scenario
    def static_column(self):
        """StaticColumn represents an attribute of the item in a row, using a Field to translate the value of that attribute into a string and to specify a column header."""
        self.column = StaticColumn(BooleanField(label=self.heading), 'some_attribute', sort_key=self.sort_key)
        self.expected_cell_html = 'on' # as translated by BooleanField
        self.expected_heading_html = '<span>A heading</span>'

    @scenario
    def dynamic_column(self):
        """DynamicColumn uses a function to create a Widget on the fly for each cell and uses the specified heading."""
        def make_span(view, data_item):
            return Span(view, text='Answer: %s' % (data_item.some_attribute))

        self.column = DynamicColumn(self.heading, make_span, sort_key=self.sort_key)
        self.expected_cell_html = '<span>Answer: True</span>' # raw attribute used
        self.expected_heading_html = '<span>A heading</span>'

    @scenario
    def dynamic_column_static_heading(self):
        """A DynamicColumn can also use a function to create its heading on the fly."""
        def make_span(view, data_item):
            return Span(view, text='Answer: %s' % (data_item.some_attribute))

        def make_heading(view):
            return P(view, text=self.heading)

        self.column = DynamicColumn(make_heading, make_span, sort_key=self.sort_key)
        self.expected_cell_html = '<span>Answer: True</span>' # raw attribute used
        self.expected_heading_html = '<p>A heading</p>'


@test(ColumnFixture)
def different_kinds_of_columns(fixture):
    """There are different kinds of Columns, allowing different levels of flexibility for defining a Table"""

    vassert( fixture.column.sort_key is fixture.sort_key )

    # The heading
    widget_for_heading = fixture.column.heading_as_widget(fixture.view)
    actual = WidgetTester(widget_for_heading).render_html()

    vassert( actual == fixture.expected_heading_html )

    # A cell
    widget_for_cell = fixture.column.as_widget(fixture.view, fixture.row_item)
    actual = WidgetTester(widget_for_cell).render_html()

    vassert( actual == fixture.expected_cell_html )


    
