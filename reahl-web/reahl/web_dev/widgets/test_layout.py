# Copyright 2015-2021 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from reahl.tofu import Fixture, expected, scenario, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.browsertools.browsertools import Browser

from reahl.component.exceptions import IsInstance, ProgrammerError
from reahl.web.fw import UserInterface, Layout
from reahl.web.ui import P, HTML5Page, Div, Header, Footer
from reahl.web.layout import PageLayout

from reahl.web_dev.fixtures import WebFixture


@with_fixtures(WebFixture)
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

    
@with_fixtures(WebFixture)
def test_widget_layout_errors(web_fixture):
    """A Layout can only be used with a single Widget, and a Widget can only have a single Layout."""

    fixture = web_fixture

    widget_with_layout = Div(fixture.view).use_layout(Layout())

    with expected(ProgrammerError):
        widget_with_layout.use_layout(Layout())

    re_used_layout = Layout()
    widget_with_reused_layout = Div(fixture.view).use_layout(re_used_layout)
    with expected(ProgrammerError):
        Div(fixture.view).use_layout(re_used_layout)


@uses(web_fixture=WebFixture)
class WidgetCreationScenarios(Fixture):

    @property
    def view(self):
        return self.web_fixture.view

    def new_MyLayout(self):
        class MyLayout(Layout):
            def customise_widget(self):
                self.widget.add_child(P(self.view, text='This widget is using Mylayout'))
        return MyLayout

    @scenario
    def use_layout_with_factory_class_method(self):
        fixture = self
        class MainUI(UserInterface):
            def assemble(self):
                self.define_view('/', title='Hello', page=HTML5Page.factory().use_layout(fixture.MyLayout()))
        self.MainUI = MainUI
        
    @scenario
    def use_layout_with_define_page(self):
        fixture = self
        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(HTML5Page).use_layout(fixture.MyLayout())
                self.define_view('/', title='Hello')
        self.MainUI = MainUI


@with_fixtures(WebFixture, WidgetCreationScenarios)
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

    wsgi_app = web_fixture.new_wsgi_app(site_root=fixture.MainUI)
    browser = Browser(wsgi_app)

    browser.open('/')
    [p] = browser.lxml_html.xpath('//p')
    assert p.text == 'This widget is using Mylayout'


@with_fixtures(WebFixture)
def test_page_layout_basics(web_fixture):
    """A PageLayout adds a Div to the body of its page (the page's document), containing a header, footer 
       with a div inbetween the two for page contents."""

    fixture = web_fixture

    layout = PageLayout()
    widget = HTML5Page(fixture.view).use_layout(layout)

    assert [layout.document] == widget.body.children[1:-1]
    header, contents_div, footer = layout.document.children

    assert isinstance(header, Header)
    assert isinstance(contents_div, Div)
    assert isinstance(footer, Footer)


@with_fixtures(WebFixture)
def test_header_and_footer_slots(web_fixture):
    """PageLayout adds a Slot for Header and Footer."""

    fixture = web_fixture

    page = HTML5Page(fixture.view).use_layout(PageLayout())

    header, contents_div, footer = page.layout.document.children

    assert 'header' in header.available_slots
    assert 'footer' in footer.available_slots


@with_fixtures(WebFixture)
def test_page_layout_content_layout(web_fixture):
    """A PageLayout can be given a Layout it should use to lay out its contents Div."""

    fixture = web_fixture

    contents_layout = Layout()
    widget = HTML5Page(fixture.view).use_layout(PageLayout(contents_layout=contents_layout))

    assert widget.layout.contents.layout is contents_layout


@with_fixtures(WebFixture)
def test_page_layout_only_meant_for_html5page(web_fixture):
    """When an attempting to use a PageLayout on something other than an HTML5Page, a useful exception is raised."""

    fixture = web_fixture

    with expected(IsInstance):
        Div(fixture.view).use_layout(PageLayout())


@with_fixtures(WebFixture)
def test_page_layout_convenience_features(web_fixture):
    """A PageLayout exposes useful methods to get to its contents, and adds ids to certain elements for convenience in CSS."""

    fixture = web_fixture

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
