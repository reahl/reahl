# Copyright 2013-2021 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from reahl.tofu import expected
from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import EmptyStub, stubclass

from reahl.browsertools.browsertools import WidgetTester, Browser

from reahl.component.exceptions import IncorrectArgumentError, IsInstance
from reahl.web.fw import UserInterface, Widget
from reahl.web.ui import Div, P, Slot


from reahl.web_dev.fixtures import WebFixture



@with_fixtures(WebFixture)
def test_basic_widget(web_fixture):
    """Basic widgets are created by adding children widgets to them, and the result is rendered in HTML"""

    class MyMessage(Div):
        def __init__(self, view):
            super().__init__(view)
            self.add_child(P(view, text='Hello World!'))
            self.add_children([P(view, text='a'), P(view, text='b')])

    fixture = web_fixture

    message = MyMessage(fixture.view)

    widget_tester = WidgetTester(message)
    actual = widget_tester.render_html()

    assert actual == '<div><p>Hello World!</p><p>a</p><p>b</p></div>'


@with_fixtures(WebFixture)
def test_visibility(web_fixture):
    """Widgets are rendered only if their .visible property is True."""

    class MyMessage(Widget):
        is_visible = True
        def __init__(self, view):
            super().__init__(view)
            self.add_child(P(view, text='你好世界!'))

        @property
        def visible(self):
            return self.is_visible

    fixture = web_fixture

    message = MyMessage(fixture.view)

    widget_tester = WidgetTester(message)

    # Case: when visible
    message.is_visible = True
    actual = widget_tester.render_html()
    assert actual == '<p>你好世界!</p>'

    # Case: when not visible
    message.is_visible = False
    actual = widget_tester.render_html()
    assert actual == ''


@with_fixtures(WebFixture)
def test_widget_factories_and_args(web_fixture):
    """Widgets can be created from factories which allow you to supply widget-specific args
       and/or kwargs before a view is available."""

    class WidgetWithArgs(Widget):
        def __init__(self, view, arg, kwarg=None):
            super().__init__(view)
            self.saved_arg = arg
            self.saved_kwarg = kwarg

    fixture = web_fixture

    factory = WidgetWithArgs.factory('a', kwarg='b')

    widget = factory.create(fixture.view)

    assert widget.saved_arg == 'a'
    assert widget.saved_kwarg == 'b'


def test_widget_factories_error():
    """Supplying arguments to .factory that do not match those of the Widget's __init__ is reported to the programmer.."""

    class WidgetWithArgs(Widget):
        def __init__(self, view, arg, kwarg=None):
            super().__init__(view)
            self.saved_arg = arg
            self.saved_kwarg = kwarg

    expected_message = 'An attempt was made to create a WidgetFactory for %r with arguments that do not match what is expected for %r' % (WidgetWithArgs, WidgetWithArgs)
    with expected(IncorrectArgumentError, test=expected_message):
        WidgetWithArgs.factory('a', 'b', 'c')


def test_widget_construct_error():
    """Passing anything other than a View as a Widget's view argument on construction results in an error."""

    with expected(IsInstance):
        Widget(EmptyStub())


@with_fixtures(WebFixture)
def test_widget_adding_error(web_fixture):
    """Passing anything other than other Widgets to .add_child or add_children results in an error."""
    fixture = web_fixture

    widget = Widget(fixture.view)

    with expected(IsInstance):
        widget.add_child(EmptyStub())

    with expected(IsInstance):
        widget.add_children([Widget(fixture.view), EmptyStub()])


@with_fixtures(WebFixture)
def test_basic_working_of_slots(web_fixture):
    """Slots are special Widgets that can be added to the page. The contents of a
       Slot are then supplied (differently) by different Views."""

    class MyPage(Widget):
        def __init__(self, view):
            super().__init__(view)
            self.add_child(Slot(view, 'slot1'))
            self.add_child(Slot(view, 'slot2'))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(MyPage)

            home = self.define_view('/', title='Home')
            home.set_slot('slot1', P.factory(text='a'))
            home.set_slot('slot2', P.factory(text='b'))

            other = self.define_view('/other', title='Other')
            other.set_slot('slot1', P.factory(text='other'))

    fixture = web_fixture

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    browser.open('/')
    [slot1_p, slot2_p] = browser.lxml_html.xpath('//p')
    assert slot1_p.text == 'a'
    assert slot2_p.text == 'b'

    browser.open('/other')
    [slot1_p] = browser.lxml_html.xpath('//p')
    assert slot1_p.text == 'other'


@with_fixtures(WebFixture)
def test_defaults_for_slots(web_fixture):
    """A Widget can have defaults for its slots."""

    class MyPage(Widget):
        def __init__(self, view):
            super().__init__(view)
            self.add_child(Slot(view, 'slot3'))
            self.add_default_slot('slot3', P.factory(text='default'))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(MyPage)
            self.define_view('/', title='Home')

    fixture = web_fixture

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    browser.open('/')
    [slot3_p] = browser.lxml_html.xpath('//p')
    assert slot3_p.text == 'default'


@with_fixtures(WebFixture)
def test_activating_javascript(web_fixture):
    """The JavaScript snippets of all Widgets are collected in a jQuery.ready() function by"""
    """ an automatically inserted Widget in the slot named reahl_footer.  Duplicate snippets are removed."""
    @stubclass(Widget)
    class WidgetWithJavaScript(Widget):
        def __init__(self, view, fake_js):
            super().__init__(view)
            self.fake_js = fake_js

        def get_js(self, context=None):
           return [self.fake_js]

    class MyPage(Widget):
        def __init__(self, view):
            super().__init__(view)
            self.add_child(WidgetWithJavaScript(view, 'js1'))
            self.add_child(WidgetWithJavaScript(view, 'js2'))
            self.add_child(WidgetWithJavaScript(view, 'js1'))#intended duplicate
            self.add_child(Slot(view, 'reahl_footer'))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(MyPage)
            self.define_view('/', title='Home')

    fixture = web_fixture
    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    browser.open('/')
    rendered_js = [i.text for i in browser.lxml_html.xpath('//script[@id="reahl-jqueryready"]')][0]
    assert rendered_js == '\njQuery(document).ready(function($){\n$(\'body\').addClass(\'enhanced\');\njs1\njs2\n\n});\n'

    number_of_duplicates = rendered_js.count('js1') - 1
    assert number_of_duplicates == 0
