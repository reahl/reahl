# Copyright 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.tofu import test, Fixture
from reahl.tofu import vassert, expected, scenario
from reahl.stubble import stubclass, EmptyStub

from reahl.component.exceptions import ProgrammerError

from reahl.webdev.tools import WidgetTester, Browser
from reahl.web_dev.fixtures import WebFixture

from reahl.component.exceptions import IsInstance
from reahl.web.fw import UserInterface
from reahl.web.ui import P, HTML5Page, Layout, Div, Widget, Header, Footer
from reahl.web.layout import ResponsiveSize, ColumnLayout, PageLayout

@test(WebFixture)
def widget_layout(fixture):
    """A Layout is used to add children to the Widget in customised ways, and to customise the Widget itself upon construction."""

    class MyLayout(Layout):
        def customise_widget(self):
            self.widget.append_class('class-added-by-custom-layout')

        def add_wrapped(self, child):
            wrapper = self.widget.add_child(Div(self.view))
            wrapper.add_child(child)
            return child

    widget_with_layout = Div(fixture.view)

    vassert( not widget_with_layout.has_attribute('class') )
    vassert( not widget_with_layout.children )

    widget_with_layout.use_layout(MyLayout())

    vassert( widget_with_layout.get_attribute('class') == 'class-added-by-custom-layout' )
    vassert( not widget_with_layout.children )

    widget_to_add = P(fixture.view)
    widget_with_layout.layout.add_wrapped(widget_to_add)

    [wrapper] = widget_with_layout.children
    vassert( wrapper.children == [widget_to_add] )

    


@test(WebFixture)
def widget_layout_errors(fixture):
    """A Layout can only be used with a single Widget, and a Widget can only have a single Layout."""

    widget_with_layout = Div(fixture.view).use_layout(Layout())

    with expected(ProgrammerError):
        widget_with_layout.use_layout(Layout())

    re_used_layout = Layout()
    widget_with_reused_layout = Div(fixture.view).use_layout(re_used_layout)
    with expected(ProgrammerError):
        Div(fixture.view).use_layout(re_used_layout)


class WidgetCreationScenarios(WebFixture):
    def new_layout(self):
        class MyLayout(Layout):
            def customise_widget(self):
                self.widget.add_child(P(self.view, text='This widget is using Mylayout'))
        return MyLayout()

    @scenario
    def use_layout_with_factory_class_method(self):
        fixture = self
        class MainUI(UserInterface):
            def assemble(self):
                self.define_view('/', title='Hello', page=HTML5Page.factory().use_layout(fixture.layout))
        self.MainUI = MainUI
        
    @scenario
    def use_layout_with_define_page(self):
        fixture = self
        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(HTML5Page).use_layout(fixture.layout)
                self.define_view('/', title='Hello')
        self.MainUI = MainUI


@test(WidgetCreationScenarios)
def widget_factory_creates_widget_with_layout(fixture):
    """A Layout can be specified to any WidgetFactory or to UserInterface.define_page"""

    class MyLayout(Layout):
        def customise_widget(self):
            self.widget.add_child(P(self.view, text='This widget is using Mylayout'))

    layout_for_widget = MyLayout()

    class MainUI(UserInterface):
        def assemble(self):
            self.define_view('/', title='Hello', page=HTML5Page.factory(use_layout=layout_for_widget))

    wsgi_app = fixture.new_wsgi_app(site_root=fixture.MainUI)
    browser = Browser(wsgi_app)

    browser.open('/')
    [p] = browser.lxml_html.xpath('//p')
    vassert( p.text == 'This widget is using Mylayout' )



@test(Fixture)
def responsive_size(fixture):
    """A ResponsiveSize acts like a dictionary mapping a device class to a size, but only if the size is not None."""

    size = ResponsiveSize(xs=1, sm='2',lg=None)

    vassert ( size['xs'] == 1 )
    vassert ( size['sm'] == '2' )
    vassert ( 'lg' not in size )

    vassert( size == {'xs': 1, 'sm': '2'} )


class ColumnConstructionScenarios(WebFixture):
    @scenario
    def without_sizes(self):
        """Construct the ColumnLayout with a list of column names."""
        self.layout = ColumnLayout('column_a', 'column_b')
        self.expected_class_for_column_b = 'pure-u'

    @scenario
    def with_size(self):
        """You can optionally specify the sizes a column should adhere to."""
        self.layout = ColumnLayout('column_a', ('column_b', ResponsiveSize(default='1/2')))
        self.expected_class_for_column_b = 'pure-u-1-2'


@test(WebFixture)
def column_layout_basics(fixture):
    """A ColumnLayout turns its Widget into a sequence of columns, each of which is a Div."""

    layout = ColumnLayout('column_a', 'column_b')
    widget = Div(fixture.view)
    
    vassert( not widget.children )
    
    widget.use_layout(layout)

    column_a, column_b = widget.children
    vassert( isinstance(column_a, Div) )
    vassert( isinstance(column_b, Div) )


@test(WebFixture)
def column_layout_sizes(fixture):
    """You can also pass tuples to define columns with specified sizes. The size is passed to add_column which you can override."""

    fixture.added_sizes = []
    @stubclass(ColumnLayout)
    class ColumnLayoutStub(ColumnLayout):
        def add_column(self, size): 
            fixture.added_sizes.append(size)
            return super(ColumnLayoutStub, self).add_column(size)
            
    specified_size = EmptyStub()
    widget = Div(fixture.view).use_layout(ColumnLayoutStub('column_a', ('column_b', specified_size)))

    vassert( isinstance(fixture.added_sizes[0], ResponsiveSize) )
    vassert( not fixture.added_sizes[0] )
    vassert( fixture.added_sizes[1] is specified_size )


@test(WebFixture)
def order_of_columns(fixture):
    """Columns are added in the order given to the ColumnLayout constructor, and the Div representing each column
       can be obtained using dictionary access on Layout.columns."""

    widget = Div(fixture.view).use_layout(ColumnLayout('column_name_a', 'column_name_b'))

    column_a = widget.layout.columns['column_name_a']
    column_b = widget.layout.columns['column_name_b']
    
    first_column, second_column = widget.children

    vassert( first_column is column_a )
    vassert( second_column is column_b )


@test(WebFixture)
def columns_classes(fixture):
    """The Div added for each column specified to ColumnLayout is given a CSS class derived from the column name."""

    widget = Div(fixture.view).use_layout(ColumnLayout('column_name_a'))
    column_a = widget.layout.columns['column_name_a']
    vassert( 'column-column_name_a' in column_a.get_attribute('class') )  


@test(WebFixture)
def column_slots(fixture):
    """A ColumnLayout can be made that adds a Slot to each added column, named after the column it is added to."""

    widget = Div(fixture.view).use_layout(ColumnLayout('column_name_a', 'column_name_b').with_slots())

    column_a, column_b = widget.layout.columns.values()
    vassert( 'column_name_a' in column_a.available_slots )
    vassert( 'column_name_b' in column_b.available_slots )


@test(WebFixture)
def adding_unnamed_columns(fixture):
    """You can add a column by calling add_column on the ColumnLayout"""

    widget = Div(fixture.view).use_layout(ColumnLayout())

    vassert( not widget.children )

    widget.layout.add_column(ResponsiveSize())

    vassert( len(widget.children) == 1 )
    vassert( isinstance(widget.children[0], Div) )


@test(WebFixture)
def page_layout_basics(fixture):
    """A PageLayout adds a Div to the body of its page (the page's document), containing a header, footer 
       with a div inbetween the two for page contents."""

    layout = PageLayout()
    widget = HTML5Page(fixture.view).use_layout(layout)
    
    vassert( [layout.document] == widget.body.children[:-1] )
    header, contents_div, footer = layout.document.children

    vassert( isinstance(header, Header) )
    vassert( isinstance(contents_div, Div) )
    vassert( isinstance(footer, Footer) )


@test(WebFixture)
def header_and_footer_slots(fixture):
    """PageLayout adds a Slot for Header and Footer."""

    page = HTML5Page(fixture.view).use_layout(PageLayout())

    header, contents_div, footer = page.layout.document.children

    vassert( 'header' in header.available_slots )
    vassert( 'footer' in footer.available_slots )


@test(WebFixture)
def page_layout_content_layout(fixture):
    """A PageLayout can be given a Layout it should use to lay out its contents Div."""

    contents_layout = Layout()
    widget = HTML5Page(fixture.view).use_layout(PageLayout(contents_layout=contents_layout))
    
    vassert( widget.layout.contents.layout is contents_layout )


@test(WebFixture)
def page_layout_only_meant_for_html5page(fixture):
    """When an attempting to use a PageLayout on something other than an HTML5Page, a useful exception is raised."""

    with expected(IsInstance):
        Div(fixture.view).use_layout(PageLayout())

@test(WebFixture)
def page_layout_convenience_features(fixture):
    """A PageLayout exposes useful methods to get to its contents, and adds ids to certain elements for convenience in CSS."""

    layout = PageLayout()
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

