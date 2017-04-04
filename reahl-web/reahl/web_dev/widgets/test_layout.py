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

from reahl.tofu import Fixture, expected, scenario, uses
from reahl.tofu.pytest_support import with_fixtures
from reahl.stubble import stubclass, EmptyStub

from reahl.webdev.tools import Browser

from reahl.component.exceptions import IsInstance, ProgrammerError
from reahl.web.fw import UserInterface, Layout
from reahl.web.ui import P, HTML5Page, Div, Header, Footer
from reahl.web.layout import ResponsiveSize, ColumnLayout, PageLayout

from reahl.web_dev.fixtures import WebFixture2


@with_fixtures(WebFixture2)
def test_widget_layout(web_fixture):
    """A Layout is used to add children to the Widget in customised ways, and to customise the Widget itself upon construction."""

    class MyLayout(Layout):
        def customise_widget(self):
            self.widget.append_class('class-added-by-custom-layout')

        def add_wrapped(self, child):
            wrapper = self.widget.add_child(Div(self.view))
            wrapper.add_child(child)
            return child

    fixture = web_fixture
    with web_fixture.context:
        widget_with_layout = Div(fixture.view)

        assert not widget_with_layout.has_attribute('class')
        assert not widget_with_layout.children

        widget_with_layout.use_layout(MyLayout())

        assert widget_with_layout.get_attribute('class') == 'class-added-by-custom-layout'
        assert not widget_with_layout.children

        widget_to_add = P(fixture.view)
        widget_with_layout.layout.add_wrapped(widget_to_add)

        [wrapper] = widget_with_layout.children
        assert wrapper.children == [widget_to_add]

    
@with_fixtures(WebFixture2)
def test_widget_layout_errors(web_fixture):
    """A Layout can only be used with a single Widget, and a Widget can only have a single Layout."""

    fixture = web_fixture
    with web_fixture.context:
        widget_with_layout = Div(fixture.view).use_layout(Layout())

        with expected(ProgrammerError):
            widget_with_layout.use_layout(Layout())

        re_used_layout = Layout()
        widget_with_reused_layout = Div(fixture.view).use_layout(re_used_layout)
        with expected(ProgrammerError):
            Div(fixture.view).use_layout(re_used_layout)


@uses(web_fixture=WebFixture2)
class WidgetCreationScenarios(Fixture):

    @property
    def context(self):
        return self.web_fixture.context

    @property
    def view(self):
        return self.web_fixture.view

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


@with_fixtures(WebFixture2, WidgetCreationScenarios)
def test_widget_factory_creates_widget_with_layout(web_fixture, widget_creation_scenarios):
    """A Layout can be specified to any WidgetFactory or to UserInterface.define_page"""

    class MyLayout(Layout):
        def customise_widget(self):
            self.widget.add_child(P(self.view, text='This widget is using Mylayout'))

    layout_for_widget = MyLayout()

    class MainUI(UserInterface):
        def assemble(self):
            self.define_view('/', title='Hello', page=HTML5Page.factory(use_layout=layout_for_widget))

    fixture = widget_creation_scenarios
    with web_fixture.context:
        wsgi_app = web_fixture.new_wsgi_app(site_root=fixture.MainUI)
        browser = Browser(wsgi_app)

        browser.open('/')
        [p] = browser.lxml_html.xpath('//p')
        assert p.text == 'This widget is using Mylayout'


def test_responsive_size():
    """A ResponsiveSize acts like a dictionary mapping a device class to a size, but only if the size is not None."""

    size = ResponsiveSize(xs=1, sm='2',lg=None)

    assert size['xs'] == 1
    assert size['sm'] == '2'
    assert 'lg' not in size

    assert size == {'xs': 1, 'sm': '2'}


@with_fixtures(WebFixture2)
def test_column_layout_basics(web_fixture):
    """A ColumnLayout turns its Widget into a sequence of columns, each of which is a Div."""

    fixture = web_fixture
    with web_fixture.context:
        layout = ColumnLayout('column_a', 'column_b')
        widget = Div(fixture.view)

        assert not widget.children

        widget.use_layout(layout)

        column_a, column_b = widget.children
        assert isinstance(column_a, Div)
        assert isinstance(column_b, Div)


@with_fixtures(WebFixture2)
def test_column_layout_sizes(web_fixture):
    """You can also pass tuples to define columns with specified sizes. The size is passed to add_column which you can override."""

    fixture = web_fixture

    fixture.added_sizes = []
    @stubclass(ColumnLayout)
    class ColumnLayoutStub(ColumnLayout):
        def add_column(self, size):
            fixture.added_sizes.append(size)
            return super(ColumnLayoutStub, self).add_column(size)

    with web_fixture.context:
        specified_size = EmptyStub()
        widget = Div(fixture.view).use_layout(ColumnLayoutStub('column_a', ('column_b', specified_size)))

        assert isinstance(fixture.added_sizes[0], ResponsiveSize)
        assert not fixture.added_sizes[0]
        assert fixture.added_sizes[1] is specified_size


@with_fixtures(WebFixture2)
def test_order_of_columns(web_fixture):
    """Columns are added in the order given to the ColumnLayout constructor, and the Div representing each column
       can be obtained using dictionary access on Layout.columns."""

    fixture = web_fixture
    with web_fixture.context:
        widget = Div(fixture.view).use_layout(ColumnLayout('column_name_a', 'column_name_b'))

        column_a = widget.layout.columns['column_name_a']
        column_b = widget.layout.columns['column_name_b']

        first_column, second_column = widget.children

        assert first_column is column_a
        assert second_column is column_b


@with_fixtures(WebFixture2)
def test_columns_classes(web_fixture):
    """The Div added for each column specified to ColumnLayout is given a CSS class derived from the column name."""

    fixture = web_fixture
    with web_fixture.context:
        widget = Div(fixture.view).use_layout(ColumnLayout('column_name_a'))
        column_a = widget.layout.columns['column_name_a']
        assert 'column-column_name_a' in column_a.get_attribute('class')


@with_fixtures(WebFixture2)
def test_column_slots(web_fixture):
    """A ColumnLayout can be made that adds a Slot to each added column, named after the column it is added to."""

    fixture = web_fixture
    with web_fixture.context:
        widget = Div(fixture.view).use_layout(ColumnLayout('column_name_a', 'column_name_b').with_slots())

        column_a, column_b = widget.layout.columns.values()
        assert 'column_name_a' in column_a.available_slots
        assert 'column_name_b' in column_b.available_slots


@with_fixtures(WebFixture2)
def test_adding_unnamed_columns(web_fixture):
    """You can add a column by calling add_column on the ColumnLayout"""

    fixture = web_fixture
    with web_fixture.context:

        widget = Div(fixture.view).use_layout(ColumnLayout())

        assert not widget.children

        widget.layout.add_column(ResponsiveSize())

        assert len(widget.children) == 1
        assert isinstance(widget.children[0], Div)


@with_fixtures(WebFixture2)
def test_page_layout_basics(web_fixture):
    """A PageLayout adds a Div to the body of its page (the page's document), containing a header, footer 
       with a div inbetween the two for page contents."""

    fixture = web_fixture
    with web_fixture.context:
        layout = PageLayout()
        widget = HTML5Page(fixture.view).use_layout(layout)

        assert [layout.document] == widget.body.children[:-1]
        header, contents_div, footer = layout.document.children

        assert isinstance(header, Header)
        assert isinstance(contents_div, Div)
        assert isinstance(footer, Footer)


@with_fixtures(WebFixture2)
def test_header_and_footer_slots(web_fixture):
    """PageLayout adds a Slot for Header and Footer."""

    fixture = web_fixture
    with web_fixture.context:
        page = HTML5Page(fixture.view).use_layout(PageLayout())

        header, contents_div, footer = page.layout.document.children

        assert 'header' in header.available_slots
        assert 'footer' in footer.available_slots


@with_fixtures(WebFixture2)
def test_page_layout_content_layout(web_fixture):
    """A PageLayout can be given a Layout it should use to lay out its contents Div."""

    fixture = web_fixture
    with web_fixture.context:
        contents_layout = Layout()
        widget = HTML5Page(fixture.view).use_layout(PageLayout(contents_layout=contents_layout))

        assert widget.layout.contents.layout is contents_layout


@with_fixtures(WebFixture2)
def test_page_layout_only_meant_for_html5page(web_fixture):
    """When an attempting to use a PageLayout on something other than an HTML5Page, a useful exception is raised."""

    fixture = web_fixture
    with web_fixture.context:
        with expected(IsInstance):
            Div(fixture.view).use_layout(PageLayout())


@with_fixtures(WebFixture2)
def test_page_layout_convenience_features(web_fixture):
    """A PageLayout exposes useful methods to get to its contents, and adds ids to certain elements for convenience in CSS."""

    fixture = web_fixture
    with web_fixture.context:
        layout = PageLayout()
        widget = HTML5Page(fixture.view).use_layout(layout)
        header, contents_div, footer = layout.document.children

        assert layout.document.css_id == 'doc'
        assert header.css_id == 'hd'
        assert footer.css_id == 'ft'
        assert contents_div.css_id == 'bd'
        assert contents_div.get_attribute('role') == 'main'

        assert layout.header is header
        assert layout.contents is contents_div
        assert layout.footer is footer
