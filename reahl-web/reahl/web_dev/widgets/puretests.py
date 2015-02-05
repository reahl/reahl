# Copyright 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.tofu import vassert, scenario, expected, test

from reahl.webdev.tools import XPath, Browser

from reahl.webdev.tools import WidgetTester
from reahl.web_dev.fixtures import WebFixture

from reahl.web.fw import UserInterface
from reahl.web.ui import Panel, P, HTML5Page, Header, Footer

from reahl.component.exceptions import ProgrammerError, IsInstance
from reahl.web.pure import ColumnLayout, UnitSize, PageColumnLayout

class ColumnConstructionScenarios(WebFixture):
    @scenario
    def without_sizes(self):
        """Construct the ColumnLayout with a list of column names."""
        self.layout = ColumnLayout('column_a', 'column_b')
        self.expected_class_for_column_b = 'pure-u'

    @scenario
    def with_size(self):
        """You can optionally specify the sizes a column should adhere to."""
        self.layout = ColumnLayout('column_a', ('column_b', UnitSize(default='1/2')))
        self.expected_class_for_column_b = 'pure-u-1-2'


@test(ColumnConstructionScenarios)
def column_layout_basics(fixture):
    """A ColumnLayout turns its Widget into a sequence of columns, each of which is a Panel, 
       laid out next to each other."""

    widget = Panel(fixture.view)
    
    vassert( not widget.has_attribute('class') )
    vassert( not widget.children )
    
    widget.use_layout(fixture.layout)

    vassert( widget.get_attribute('class') == 'pure-g' )
    column_a, column_b = widget.children
    vassert( isinstance(column_a, Panel) )
    vassert( isinstance(column_b, Panel) )

    vassert( 'pure-u' in column_a.get_attribute('class') )    # never varies in scenarios
    vassert( fixture.expected_class_for_column_b in column_b.get_attribute('class')  )


@test(WebFixture)
def order_of_columns(fixture):
    """Columns are added in the order given to the ColumnLayout constructor, and the Panel representing each column
       can be obtained using dictionary access on Layout.columns."""

    widget = Panel(fixture.view).use_layout(ColumnLayout('column_name_a', 'column_name_b'))

    column_a = widget.layout.columns['column_name_a']
    column_b = widget.layout.columns['column_name_b']
    
    first_column, second_column = widget.children

    vassert( first_column is column_a )
    vassert( second_column is column_b )


@test(WebFixture)
def columns_classes(fixture):
    """The Panel added for each column specified to ColumnLayout is given a CSS class derived from the column name."""

    widget = Panel(fixture.view).use_layout(ColumnLayout('column_name_a'))
    column_a = widget.layout.columns['column_name_a']
    vassert( 'column-column_name_a' in column_a.get_attribute('class') )  


@test(WebFixture)
def adding_columns(fixture):
    """You can add additional columns after construction."""

    widget = Panel(fixture.view).use_layout(ColumnLayout())

    vassert( not widget.children )

    widget.layout.add_column()

    [added_column] = widget.children
    vassert( added_column.get_attribute('class') == 'pure-u' )


class SizingFixture(WebFixture):
    @scenario
    def all_sizes_given(self):
        self.sizes = dict(default='1/2', sm='1/3', md='2/3', lg='1/4', xl='3/4')
        self.expected_classes = ['pure-u-1-2','pure-u-lg-1-4','pure-u-md-2-3','pure-u-sm-1-3','pure-u-xl-3-4']

    @scenario
    def some_sizes_unspecified(self):
        self.sizes = dict(default='1/3', sm='2/3')
        self.expected_classes = ['pure-u-1-3','pure-u-sm-2-3']


@test(SizingFixture)
def sizing_when_adding(fixture):
    """When adding a column, the unit_size kwarg can be used to specify sizes for the added column."""

    widget = Panel(fixture.view).use_layout(ColumnLayout())

    widget.layout.add_column(unit_size=UnitSize(**fixture.sizes))

    widget.children[0].attributes['class'] == fixture.expected_classes




@test(WebFixture)
def page_column_layout_basics(fixture):
    """A PageColumnLayout adds a Panel to the body of its page (the page's document), containing a header, footer 
       with a div inbetween the two."""

    layout = PageColumnLayout()
    widget = HTML5Page(fixture.view).use_layout(layout)
    
    vassert( [layout.document] == widget.body.children[:-1] )
    header, contents_div, footer = layout.document.children

    vassert( isinstance(header, Header) )
    vassert( isinstance(contents_div, Panel) )
    vassert( isinstance(footer, Footer) )


@test(WebFixture)
def page_column_layout_content_layout(fixture):
    """A PageColumnLayout lays out its content (the bits between header and footer) using a ColumnLayout with the columns it is created with."""

    widget = HTML5Page(fixture.view).use_layout(PageColumnLayout('column_a', 'column_b'))
    
    contents_layout = widget.layout.contents.layout
    vassert( isinstance(contents_layout, ColumnLayout) )
    vassert( 'column_a' in contents_layout.columns )
    vassert( 'column_b' in contents_layout.columns )


@test(WebFixture)
def convenient_slots_created(fixture):
    """PageColumnLayout add a Slot for Header, Footer and each column defined. The Slot for each column is named the same as the column's name."""

    layout = PageColumnLayout('column_name_a', 'column_name_b')
    HTML5Page(fixture.view).use_layout(layout)

    header, contents_div, footer = layout.document.children

    vassert( 'header' in header.available_slots )
    vassert( 'footer' in footer.available_slots )

    column_a, column_b = contents_div.children
    vassert( 'column_name_a' in column_a.available_slots )
    vassert( 'column_name_b' in column_b.available_slots )


@test(WebFixture)
def page_column_layout_only_meant_for_html5page(fixture):
    """When an attempting to use a PageColumnLayout on something other than an HTML5Page, a useful exception is raised."""

    with expected(IsInstance):
        Panel(fixture.view).use_layout(PageColumnLayout())


@test(WebFixture)
def page_column_layout_convenience_features(fixture):
    """A PageColumnLayout exposes useful methods to get to its contents, and adds ids to certain elements for convenience in CSS."""

    layout = PageColumnLayout()
    widget = HTML5Page(fixture.view).use_layout(layout)
    header, contents_div, footer = layout.document.children
    
    vassert( layout.document.css_id == 'doc' )
    vassert( header.css_id == 'hd' )
    vassert( footer.css_id == 'ft' )
    vassert( contents_div.css_id == 'bd' )
    vassert( contents_div.get_attribute('role') == 'main' )
    
    vassert( layout.header is header )
    vassert( layout.contents is contents_div )
    vassert( layout.footer is footer )
    vassert( layout.columns is contents_div.layout.columns )




