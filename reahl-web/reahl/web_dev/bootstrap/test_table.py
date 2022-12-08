# Copyright 2016-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.tofu import scenario, Fixture
from reahl.tofu.pytestsupport import with_fixtures

from reahl.browsertools.browsertools import XPath

import reahl.web_dev.widgets.test_table
from reahl.component.modelinterface import Field, IntegerField, ExposedNames
from reahl.web.bootstrap.ui import Div
from reahl.web.bootstrap.tables import Table, StaticColumn, TableLayout, DataTable

from reahl.web_dev.fixtures import WebFixture
from reahl.web_dev.widgets.test_table import TableFixture
from reahl.component_dev.test_i18n import LocaleContextStub


class LayoutScenarios(Fixture):
    @scenario
    def header_dark(self):
        self.layout_kwargs = dict(dark=True)
        self.expected_table_css_class = 'table table-dark'
        self.expected_main_css_class = None

    @scenario
    def border(self):
        self.layout_kwargs = dict(border='cells')
        self.expected_table_css_class = 'table table-bordered'
        self.expected_main_css_class = None

    @scenario
    def border(self):
        self.layout_kwargs = dict(border='borderless')
        self.expected_table_css_class = 'table table-borderless'
        self.expected_main_css_class = None

    @scenario
    def striped_rows(self):
        self.layout_kwargs = dict(striped=True)
        self.expected_table_css_class = 'table table-striped'
        self.expected_main_css_class = None

    @scenario
    def hovered_rows(self):
        self.layout_kwargs = dict(highlight_hovered=True)
        self.expected_table_css_class = 'table table-hover'
        self.expected_main_css_class = None

    @scenario
    def compacted_cells(self):
        self.layout_kwargs = dict(compact=True)
        self.expected_table_css_class = 'table table-sm'
        self.expected_main_css_class = None

    @scenario
    def responsive(self):
        self.layout_kwargs = dict(responsive='lg')
        self.expected_table_css_class = 'table'
        self.expected_main_css_class = 'table-responsive-lg'

    @scenario
    def responsive_for_device(self):
        self.layout_kwargs = dict(responsive=True)
        self.expected_table_css_class = 'table'
        self.expected_main_css_class = 'table-responsive'


@with_fixtures(WebFixture, LayoutScenarios)
def test_table_layout_options(web_fixture, layout_scenarios):
    """TableLayout uses Bootstrap to implement many table layout options."""

    layout = TableLayout(**layout_scenarios.layout_kwargs)
    Table(web_fixture.view).use_layout(layout)
    assert layout.widget.table.get_attribute('class') == layout_scenarios.expected_table_css_class
    if layout_scenarios.expected_main_css_class:
        assert layout.widget.html_representation.get_attribute('class') == layout_scenarios.expected_main_css_class


class LayoutHeaderThemeScenarios(WebFixture):

    @scenario
    def no_theme(self):
        self.theme = None

    @scenario
    def light(self):
        self.theme = 'light'
        self.expected_css_class = 'thead-light'

    @scenario
    def dark(self):
        self.theme = 'dark'
        self.expected_css_class = 'thead-dark'


@with_fixtures(WebFixture, LayoutHeaderThemeScenarios)
def test_table_layout_header_options(web_fixture, layout_scenarios):
    """TableLayout can style a table header row."""

    data = [DataItem(1, 'T'), DataItem(2, 'H'), DataItem(3, 'E')]

    column_definitions = [StaticColumn(Field(label='Row Number'), 'row'),
                          StaticColumn(Field(label='Alpha'), 'alpha')]

    layout = TableLayout(heading_theme=layout_scenarios.theme)
    table = Table(web_fixture.view).with_data(column_definitions, data)
    table.use_layout(layout)

    if layout_scenarios.theme is not None:
        assert layout.widget.thead.get_attribute('class') == '%s' % layout_scenarios.expected_css_class
    else:
        assert not layout.widget.thead.has_attribute('class')


class DataItem(reahl.web_dev.widgets.test_table.DataItem):
    fields = ExposedNames()
    fields.row = lambda i: IntegerField(label='Row', required=True, default=i.row)
    fields.alpha = lambda i: Field(label='Alpha', required=True, default=i.alpha)


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
        class MainWidget(Div):
            def __init__(self, view):
                super().__init__(view)

                data_table = DataTable(view, fixture.columns, fixture.data,
                                       items_per_page=fixture.items_per_page,
                                       caption_text='All my friends',
                                       summary='Summary for screen reader',
                                       css_id='my_table_data')
                self.add_child(data_table)
        return MainWidget

    def new_wsgi_app(self):
        return self.web_fixture.new_wsgi_app(enable_js=False, child_factory=self.MainWidget.factory())

    def xpath_for_sort_link_for_column(self, column_number):
        return '(//table/thead/tr/th)[%s]/a' % column_number

    def does_column_have_sort_link(self, column_number):
        column_header = self.web_fixture.driver_browser.web_driver.find_element(By.XPATH, '(//table/thead/tr/th)[%s]' % (column_number))
        return len(column_header.find_elements(By.TAG_NAME, 'a')) == 1
        
    def is_column_sorted(self, column_number, direction):
        header_link = self.web_fixture.driver_browser.web_driver.find_element(By.XPATH, '(//table/thead/tr/th)[%s]/a' % (column_number))
        if direction:
            expected_class = 'sorted-%s' % direction
            return expected_class in header_link.get_attribute('class').split(' ')
        else:
            return all([expected_class not in header_link.get_attribute('class').split(' ') 
                        for expected_class in ['sorted-ascending','sorted-descending']])


@with_fixtures(WebFixture, DataTableFixture)
def test_paging_through_data(web_fixture, data_table_fixture):
    """DataTable splits its items into different pages (between which a user can navigate), showing only the items of a particular page at a time."""

    web_fixture.reahl_server.set_app(data_table_fixture.wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    #click to last page
    browser.click(XPath.link().with_text_starting('→'))
    browser.click(XPath.link().with_text('9'))

    assert data_table_fixture.table_number_rows() == 2
    assert data_table_fixture.get_table_row(1) == ['25' ,'D']
    assert data_table_fixture.get_table_row(2) == ['26' ,'G']

    #click to page 4
    browser.click(XPath.link().with_text_starting('←'))
    browser.click(XPath.link().with_text('4'))

    assert data_table_fixture.table_number_rows() == 3
    assert data_table_fixture.get_table_row(1) == ['10' ,'R']
    assert data_table_fixture.get_table_row(2) == ['11' ,'O']
    assert data_table_fixture.get_table_row(3) == ['12' ,'W']


@with_fixtures(WebFixture, DataTableFixture)
def test_sorting(web_fixture, data_table_fixture):
    """By clicking on special links in the column header, the table is sorted according to that column - ascending or descending."""

    web_fixture.reahl_server.set_app(data_table_fixture.wsgi_app)
    web_fixture.quit_browser() # To ensure that a previous one is not still running with cached javascript scripts
    browser = web_fixture.driver_browser
    browser.open('/')

    #----- by default, not sorted
    assert not data_table_fixture.is_column_sorted(1, 'ascending')
    assert not data_table_fixture.is_column_sorted(1, 'descending')
    assert not data_table_fixture.is_column_sorted(2, 'ascending')
    assert not data_table_fixture.is_column_sorted(2, 'descending')

    #----- first click on column sorts ascending
    browser.click(data_table_fixture.xpath_for_sort_link_for_column(1))
    assert data_table_fixture.is_column_sorted(1, 'ascending')
    assert data_table_fixture.get_table_row(1) == ['1' ,'T']
    assert data_table_fixture.get_table_row(2) == ['2' ,'H']
    assert data_table_fixture.get_table_row(3) == ['3' ,'E']

    #----- sort ascending on alpha, the second column
    assert data_table_fixture.is_column_sorted(2, None)
    browser.click(data_table_fixture.xpath_for_sort_link_for_column(2))
    assert data_table_fixture.is_column_sorted(2, 'ascending')
    assert data_table_fixture.is_column_sorted(1, None)

    assert data_table_fixture.get_table_row(1) == ['22' ,'A']
    assert data_table_fixture.get_table_row(2) == ['9' ,'B']
    assert data_table_fixture.get_table_row(3) == ['7' ,'C']

    #----- sort descending on alpha, the second column
    browser.click(data_table_fixture.xpath_for_sort_link_for_column(2))
    assert data_table_fixture.is_column_sorted(2, 'descending')

    assert data_table_fixture.get_table_row(1) == ['23' ,'Z']
    assert data_table_fixture.get_table_row(2) == ['24' ,'Y']
    assert data_table_fixture.get_table_row(3) == ['15' ,'X']

    #----- sort order stays changed when paging
    browser.click(XPath.link().with_text('4'))

    assert data_table_fixture.get_table_row(1) == ['4' ,'Q']
    assert data_table_fixture.get_table_row(2) == ['18' ,'P']
    assert data_table_fixture.get_table_row(3) == ['11' ,'O']

    #----- contents of the page you are on changes according to a new sort order
    browser.click(data_table_fixture.xpath_for_sort_link_for_column(1))

    assert data_table_fixture.get_table_row(1) == ['10' ,'R']
    assert data_table_fixture.get_table_row(2) == ['11' ,'O']
    assert data_table_fixture.get_table_row(3) == ['12' ,'W']


@with_fixtures(WebFixture, DataTableFixture)
def test_sorting_i18n(web_fixture, data_table_fixture):
    """Sorting works correctly when the current View is translated to another i18n locale."""

    with LocaleContextStub(locale='af'):

        web_fixture.reahl_server.set_app(data_table_fixture.wsgi_app)
        browser = web_fixture.driver_browser
        browser.open('/af/')

        assert not data_table_fixture.is_column_sorted(1, 'ascending')
        assert not data_table_fixture.is_column_sorted(1, 'descending')
        browser.click(data_table_fixture.xpath_for_sort_link_for_column(1))
        assert data_table_fixture.is_column_sorted(1, 'ascending')


@with_fixtures(WebFixture, DataTableFixture)
def test_which_columns_can_cause_sorting(web_fixture, data_table_fixture):
    """Only columns with sort_key specified are sortable."""

    data_table_fixture.columns.append(StaticColumn(Field(label='Not sortable'), 'alpha'))

    web_fixture.reahl_server.set_app(data_table_fixture.wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    assert data_table_fixture.does_column_have_sort_link(1)
    assert data_table_fixture.does_column_have_sort_link(2)
    assert not data_table_fixture.does_column_have_sort_link(3)


@with_fixtures(WebFixture, DataTableFixture)
def test_layout_for_contained_table(web_fixture, data_table_fixture):
    """You can specify a Layout to use for the actual table inside the DataTable."""

    layout = TableLayout(heading_theme='light')  # heading_theme is here to give coverage of a previous bug
    data_table = DataTable(web_fixture.view, data_table_fixture.columns, data_table_fixture.data, 'my_css_id', table_layout=layout)

    assert data_table.table.layout is layout


