# Copyright 2013-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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



import os.path
import warnings
import io
import itertools

from reahl.tofu import expected, scenario, Fixture, uses
from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import EmptyStub

from reahl.browsertools.browsertools import Browser, XPath

from reahl.component.exceptions import ProgrammerError, IncorrectArgumentError, IsSubclass
from reahl.web.fw import UserInterface
from reahl.web.ui import HTML5Page, P, Div

from reahl.web_dev.fixtures import WebFixture, BasicPageLayout


@uses(web_fixture=WebFixture)
class BasicScenarios(Fixture):

    def get_file_content(self, filename):
        with(io.open('%s/%s' % (os.path.dirname(__file__), filename))) as f:
            file_content = ''.join(f.readlines())
        return file_content[:-1]

    @property
    def view(self):
        return self.web_fixture.view

    expected_warnings = []
    @scenario
    def view_with_page(self):
        class SimplePage(HTML5Page):
            def __init__(self, view):
                super().__init__(view)
                self.body.add_child(P(view, text='Hello world!'))

        class MainUI(UserInterface):
            def assemble(self):
                self.define_view('/', title='Hello', page=SimplePage.factory())

        self.MainUI = MainUI
        self.content_includes_p = True

    @scenario
    def view_with_set_page(self):
        class SimplePage(HTML5Page):
            def __init__(self, view):
                super().__init__(view)
                self.body.add_child(P(view, text='Hello world!'))

        class MainUI(UserInterface):
            def assemble(self):
                home = self.define_view('/', title='Hello')
                home.set_page(SimplePage.factory())

        self.MainUI = MainUI
        self.content_includes_p = True

    @scenario
    def ui_with_page(self):
        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(HTML5Page)
                self.define_view('/', title='Hello')

        self.MainUI = MainUI
        self.content_includes_p = False


@with_fixtures(WebFixture, BasicScenarios)
def test_basic_assembly(web_fixture, basic_scenarios):
    """An application is built by extending UserInterface, and defining this UserInterface in an .assemble() method.

    To define the UserInterface, several Views are defined. Views are mapped to URLs. When a user GETs
    the URL of a View, a page is rendered back to the user. How that page is created
    can happen in different ways, as illustrated by each scenario of this test.
    """
    fixture = basic_scenarios

    wsgi_app = web_fixture.new_wsgi_app(site_root=fixture.MainUI)
    browser = Browser(wsgi_app)

    # GETting the URL results in the HTML for that View
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter('always')
        browser.open('/')
        assert browser.title == 'Hello'

    warning_messages = [str(i.message) for i in caught_warnings]
    assert len(warning_messages) == len(fixture.expected_warnings)
    for caught, expected_message in itertools.zip_longest(warning_messages, fixture.expected_warnings):
        assert expected_message in caught

    if fixture.content_includes_p:
        [message] = browser.xpath('//p')
        assert message.text == 'Hello world!'

    # The headers are set correctly
    response = browser.last_response
    assert response.content_type == 'text/html'
    assert response.charset == 'utf-8'
    assert str(response.cache_control) == 'no-store'

    # Invalid URLs do not exist
    with warnings.catch_warnings(record=True):
        browser.open('/nonexistantview/', status=404)


@with_fixtures(WebFixture)
def test_basic_error1(web_fixture):
    """Sending the the wrong kind of thing as widget_class to define_page is reported to the programmer."""
    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(EmptyStub)
            self.define_view('/', title='Hello')

    fixture = web_fixture

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    with expected(IsSubclass):
        browser.open('/')


@with_fixtures(WebFixture)
def test_basic_error2(web_fixture):
    """Sending the the wrong arguments for the specified class to define_page is reported to the programmer."""

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page, 1, 2)
            self.define_view('/', title='Hello')

    fixture = web_fixture

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    with expected(IncorrectArgumentError, test='define_page was called with arguments that do not match those expected by.*'):
        browser.open('/')


@with_fixtures(WebFixture)
def test_basic_error3(web_fixture):
    """Forgetting to define either a page of a page for a View is reported to the programmer."""
    class MainUI(UserInterface):
        def assemble(self):
            self.define_view('/', title='Hello')

    fixture = web_fixture

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    with expected(ProgrammerError, test='there is no page defined for /'):
        browser.open('/')


@uses(web_fixture=WebFixture)
class SlotScenarios(Fixture):
    @scenario
    def page_on_ui(self):
        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(HTML5Page).use_layout(BasicPageLayout())
                home = self.define_view('/', title='Hello')
                home.set_slot('main', P.factory(text='Hello world'))
                home.set_slot('footer', P.factory(text='I am the footer'))
        self.MainUI = MainUI

    @scenario
    def page_on_view(self):
        class MainUI(UserInterface):
            def assemble(self):
                home = self.define_view('/', title='Hello')
                home.set_page(HTML5Page.factory().use_layout(BasicPageLayout()))
                home.set_slot('main', P.factory(text='Hello world'))
                home.set_slot('footer', P.factory(text='I am the footer'))
        self.MainUI = MainUI


@with_fixtures(WebFixture, SlotScenarios)
def test_slots(web_fixture, slot_scenarios):
    """A View modifies the page by populating named Slots in the page with Widgets."""
    fixture = slot_scenarios

    wsgi_app = web_fixture.new_wsgi_app(site_root=fixture.MainUI)
    browser = Browser(wsgi_app)

    browser.open('/')
    assert browser.title == 'Hello'
    [main_p, footer_p] = browser.xpath('//p')
    assert main_p.text == 'Hello world'
    assert footer_p.text == 'I am the footer'


@with_fixtures(WebFixture)
def test_slot_error(web_fixture):
    """Supplying contents for a slot that does not exist results in s sensible error."""
    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            home = self.define_view('/', title='Hello')
            home.set_slot('main', P.factory(text='Hello world'))
            home.set_slot('nonexistantslotname', P.factory(text='I am breaking'))

    fixture = web_fixture

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    with expected(ProgrammerError, test='An attempt was made to plug Widgets into the following slots that do not exist.*'):
        browser.open('/')


@with_fixtures(WebFixture)
def test_slot_defaults(web_fixture):
    """If a View does not specify contents for a Slot, the Slot will be populated by the window's default
       widget for that slot if specified, else it will be left empty.
    """
    class MainUI(UserInterface):
        def assemble(self):
            main = self.define_page(HTML5Page).use_layout(BasicPageLayout())
            main.add_default_slot('main', P.factory(text='defaulted slot contents'))
            self.define_view('/', title='Hello')

    fixture = web_fixture

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    browser.open('/')

    # The default widget for the main slot is used
    [p] = browser.xpath('//p')
    assert p.text == 'defaulted slot contents'

    # The header slot has no default, and is thus left empty
    header_contents = browser.xpath('//header/*')
    assert not header_contents


@with_fixtures(WebFixture)
def test_out_of_bound_widgets(web_fixture):
    """When you need to add a widget to the page, but not as a child/descendant."""

    class MyPanel(Div):
        def __init__(self, view):
            super().__init__(view, css_id='main_panel')
            child_widget = self.add_child(P(view, text='Child Widget'))
            out_of_bound_widget = view.add_out_of_bound_widget(P(view, text='Out Of Bound Widget'))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            home = self.define_view('/', title='Hello')
            home.set_slot('main', MyPanel.factory())

    fixture = web_fixture

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    browser.open('/')

    main_panel = XPath.div().with_id('main_panel')
    assert browser.is_element_present(XPath.paragraph().with_text('Out Of Bound Widget'))
    assert not browser.is_element_present(XPath.paragraph().with_text('Out Of Bound Widget').inside_of(main_panel))
    assert browser.is_element_present(XPath.paragraph().with_text('Child Widget').inside_of(main_panel))
