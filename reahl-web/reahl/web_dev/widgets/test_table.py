# Copyright 2014-2021 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from selenium.webdriver.common.by import By

from reahl.stubble import EmptyStub
from reahl.tofu import Fixture, scenario, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.browsertools.browsertools import XPath, WidgetTester
from reahl.web.fw import Widget
from reahl.web.ui import StaticColumn, DynamicColumn, Table, Thead, Span, Div, P, TextNode

from reahl.component.modelinterface import Field, BooleanField

from reahl.web_dev.fixtures import WebFixture
from reahl.dev.fixtures import ReahlSystemFixture


class DataItem:
    def __init__(self, row, alpha):
        self.row = row
        self.alpha = alpha


@uses(web_fixture=WebFixture)
class TableFixture(Fixture):

    def new_data(self):
        return [DataItem(1, 'T'), DataItem(2, 'H'), DataItem(3, 'E')]

    def table_caption_is(self, expected):
        return  self.web_fixture.driver_browser.find_element(XPath.caption().with_text(expected))

    def table_summary_is(self, summary):
        return  self.web_fixture.driver_browser.find_element(XPath.table_with_summary(summary))

    def table_column_name_is(self, column_number, expected):
        return self.web_fixture.driver_browser.web_driver.find_element(By.XPATH, '((//table/thead/tr/th)[%s]/span)[1]' % column_number).text == expected

    def get_table_row(self, row_number):
        row_data = []
        for column_number in list(range(1, self.table_number_columns()+1)):
            row_data.append(self.web_fixture.driver_browser.web_driver.find_element(By.XPATH, '((//table/tbody/tr)[%s]/td)[%s]' % (row_number, column_number)).text)
        return row_data

    def table_number_columns(self):
        return len(self.web_fixture.driver_browser.web_driver.find_elements(By.XPATH, '//table/thead/tr/th'))

    def table_number_rows(self):
        return len(self.web_fixture.driver_browser.web_driver.find_elements(By.XPATH, '//table/tbody/tr'))


@with_fixtures(WebFixture, TableFixture)
def test_table_basics(web_fixture, table_fixture):
    """A Table populated .with_data() displays a list of items as defined by a list of Columns"""

    class MainWidget(Div):
        def __init__(self, view):
            super().__init__(view)
            table = Table(view, caption_text='All my friends', summary='Summary for screen reader')
            table.with_data(
                            [StaticColumn(Field(label='Row Number'), 'row'),
                             StaticColumn(Field(label='Alpha'), 'alpha')],
                             table_fixture.data
                            )
            self.add_child(table)

    fixture = table_fixture

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    web_fixture.driver_browser.open('/')

    # The table has a caption and summary
    assert fixture.table_caption_is('All my friends')
    assert fixture.table_summary_is('Summary for screen reader')

    # Column headings are derived from given Column Fields
    assert fixture.table_column_name_is(1, 'Row Number')
    assert fixture.table_column_name_is(2, 'Alpha')

    # A string representation of the value of each Field of a given data item is shown in the appropriate cell
    assert fixture.table_number_rows() == 3

    assert fixture.get_table_row(1) == ['1', 'T']
    assert fixture.get_table_row(2) == ['2', 'H']
    assert fixture.get_table_row(3) == ['3', 'E']


@uses(reahl_system_fixture=ReahlSystemFixture)
class Scenarios(Fixture):
    @scenario
    def static_column(self):
        self.total_column = StaticColumn(Field(label='Alpha'), 'alpha', footer_label='Total')
        self.expected_total = 'Total'

    @scenario
    def dynamic_column(self):
        self.total_column = DynamicColumn('Heading', lambda view, item: Widget(view), 
                                          make_footer_widget=lambda view, item: TextNode(view, str(item.total)))
        self.expected_total = '123'


@with_fixtures(WebFixture, TableFixture, Scenarios)
def test_table_totals(web_fixture, table_fixture, scenario):
    """You can pass footer_items to with_data to add a footer with a row for each footer_item.
    Each column with footer content defined will have that content rendered in its footer row,
    columns inbetween will be collapsed with a colspan to ensure alignment.
    """

    class MainWidget(Div):
        def __init__(self, view):
            super().__init__(view)
            table = Table(view)
            table.with_data(
                            [StaticColumn(Field(label='Another Row Number'), 'row_another'),
                             StaticColumn(Field(label='Row Number'), 'row'),
                             scenario.total_column],
                             table_fixture.data,
                             footer_items=[EmptyStub(total=123)]
                            )
            self.add_child(table)

    fixture = table_fixture

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    filler_cell = XPath.table_cell()[1].inside_of(XPath.table_footer())
    assert browser.get_attribute(filler_cell, 'colspan') == '2'
    total_cell = XPath.table_cell()[2].inside_of(XPath.table_footer())
    assert browser.get_text(total_cell) == scenario.expected_total
    assert not browser.get_attribute(total_cell, 'colspan') 


@uses(web_fixture=WebFixture)
class ColumnScenarios(Fixture):
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


@with_fixtures(WebFixture, ColumnScenarios)
def test_different_kinds_of_columns(web_fixture, column_scenarios):
    """There are different kinds of Columns, allowing different levels of flexibility for defining a Table"""

    fixture = column_scenarios

    assert fixture.column.sort_key is fixture.sort_key

    # The heading
    widget_for_heading = fixture.column.heading_as_widget(web_fixture.view)
    actual = WidgetTester(widget_for_heading).render_html()

    assert actual == fixture.expected_heading_html

    # A cell
    widget_for_cell = fixture.column.as_widget(web_fixture.view, fixture.row_item)
    actual = WidgetTester(widget_for_cell).render_html()

    assert actual == fixture.expected_cell_html


@with_fixtures(WebFixture)
def test_table_thead(web_fixture):
    """Table can find its Thead element"""


    table = Table(web_fixture.view)
    thead = table.add_child(Thead(web_fixture.view))

    assert table.thead is thead
