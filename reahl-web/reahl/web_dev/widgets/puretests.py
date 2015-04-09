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
from reahl.web.ui import Div, P, HTML5Page, Header, Footer

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
    """The pure.ColumnLayout adds the correct classes for Pure to lay out its Widget as a pure grid with columns as pure units."""

    widget = Div(fixture.view)
    
    vassert( not widget.has_attribute('class') )
    
    widget.use_layout(fixture.layout)

    vassert( widget.get_attribute('class') == 'pure-g' )
    column_a, column_b = widget.children

    vassert( 'pure-u' in column_a.get_attribute('class') )    # never varies in scenarios
    vassert( fixture.expected_class_for_column_b in column_b.get_attribute('class')  )




class SizingFixture(WebFixture):
    @scenario
    def all_sizes_given(self):
        "The unit_size kwarg can be used to specify sizes for the added column"
        self.sizes = dict(default='1/2', sm='1/3', md='2/3', lg='1/4', xl='3/4')
        self.expected_classes = ['pure-u-1-2','pure-u-lg-1-4','pure-u-md-2-3','pure-u-sm-1-3','pure-u-xl-3-4']

    @scenario
    def no_sizes_specified(self):
        "If no size is given, the column is still a pure unit without a size"
        self.sizes = dict()
        self.expected_classes = ['pure-u']


@test(SizingFixture)
def adding(fixture):
    """You can add a column by calling add_column on the ColumnLayout"""

    widget = Div(fixture.view).use_layout(ColumnLayout())

    widget.layout.add_column(unit_size=UnitSize(**fixture.sizes))

    vassert( widget.children[0].attributes['class'].value == set(fixture.expected_classes) )


@test(WebFixture)
def allowed_sizes(fixture):
    """The device classes for which sizes can be specified, and how to specify a size."""
    size = UnitSize(default='1/2', sm='1/3', md='1/4', lg='1/5', xl='6/7')

    vassert( size == {'default':'1/2', 'sm':'1/3', 'md':'1/4', 'lg':'1/5', 'xl':'6/7'} )


@test(WebFixture)
def page_column_layout_basics(fixture):
    """A PageColumnLayout adds a Div to the body of its page (the page's document), containing a header, footer 
       with a div inbetween the two."""

    layout = PageColumnLayout()
    widget = HTML5Page(fixture.view).use_layout(layout)
    
    vassert( [layout.document] == widget.body.children[:-1] )
    header, contents_div, footer = layout.document.children

    vassert( isinstance(header, Header) )
    vassert( isinstance(contents_div, Div) )
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
        Div(fixture.view).use_layout(PageColumnLayout())


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




