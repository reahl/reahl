# Copyright 2019, 2020, 2021 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from reahl.tofu.pytestsupport import with_fixtures
from reahl.tofu import Fixture, scenario

from reahl.browsertools.browsertools import Browser, XPath

from reahl.web.fw import UserInterface, Widget, UrlBoundView, ErrorWidget, Url
from reahl.web.ui import HTML5Page, H, P, A

from reahl.web_dev.fixtures import WebFixture


class ErrorLocationFixture(Fixture):
    def new_MainUI(self):
        fixture = self
        class MainUI(UserInterface):
            def assemble(self):
                self.define_view('/a_page', page=fixture.BreakingWidget.factory())
        return MainUI

    @scenario
    def broken_during_widget_creation(self):
        class BreakingWidget(Widget):
            def __init__(self, view):
                super().__init__(view)
                raise Exception('breaking intentionally during __init__')
        self.BreakingWidget = BreakingWidget

    @scenario
    def broken_during_widget_rendering(self):
        class BreakingWidget(Widget):
            def render_contents(self):
                raise Exception('breaking intentionally during rendering')

        self.BreakingWidget = BreakingWidget

    @scenario
    def broken_during_creation_of_root_ui(self):
        class MainUI(UserInterface):
            def assemble(self):
                raise Exception('breaking intentionally during creation of root UserInterface')
                
        self.MainUI = MainUI

    @scenario
    def broken_during_creation_of_view(self):
        class BrokenView(UrlBoundView):
            def assemble(self):
                raise Exception('breaking intentionally during creation of the UrlBoundView')
            
        class MainUI(UserInterface):
            def assemble(self):
                self.define_view('/a_page', page=Widget.factory(), view_class=BrokenView)
        self.MainUI = MainUI


        
@with_fixtures(WebFixture, ErrorLocationFixture)
def test_error_page_shown_on_error(web_fixture, error_fixture):
    """If not in debug mode and an uncaught Exception is raised, the user is redirected to an error page."""

    wsgi_app = web_fixture.new_wsgi_app(site_root=error_fixture.MainUI)
    browser = Browser(wsgi_app)

    wsgi_app.config.reahlsystem.debug = False
    
    browser.open('/a_page')
    assert browser.current_url.path == '/error'
    


class ErrorDegradeFixture(Fixture):
    @scenario
    def no_page_specified(self):
        """If no page is defined for the root UserInterface, fall back to a basic html error page as given by Widget.get_error_page_factory"""
        class MainUI(UserInterface):
            pass
        self.MainUI = MainUI
        def check(browser):
            assert not browser.is_element_present(XPath.heading(1).with_text('An error occurred:').inside_of(XPath.div()))
            assert browser.is_element_present(XPath.heading(1).with_text('An error occurred:'))
        self.check_error_page_contents = check

    @scenario
    def page_specified_on_user_interface(self):
        """If a page is defined for the UserInterface, use its get_error_page_factory classmethod."""
        fixture = self
        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(HTML5Page)
        self.MainUI = MainUI
        def check(browser):
            assert browser.is_element_present(XPath.heading(1).with_text('An error occurred:').inside_of(XPath.div()))
        self.check_error_page_contents = check

    @scenario
    def expicit_call_to_define_error_view(self):
        """Force the use of a specific error page by calling UserInterface.define_error_view() explicitly"""
        class CustomErrorPage(HTML5Page):
            def __init__(self, view):
                super().__init__(view)
                error_widget = self.body.insert_child(0, ErrorWidget(view))
                error_widget.add_child(H(view, 1, text='My custom error page'))
                error_widget.add_child(P(view, text=error_widget.error_message))
                error_widget.add_child(A(view, Url(error_widget.error_source_href), description='Ok'))

            @classmethod
            def get_widget_bookmark_for_error(cls, error_message, error_source_bookmark):
                return ErrorWidget.get_widget_bookmark_for_error(error_message, error_source_bookmark)


        fixture = self
        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(HTML5Page)
                self.define_error_view(CustomErrorPage.factory())
        self.MainUI = MainUI
        def check(browser):
            assert browser.is_element_present(XPath.heading(1).with_text('My custom error page'))
        self.check_error_page_contents = check


        
@with_fixtures(WebFixture, ErrorDegradeFixture)
def test_error_page_degrades_gracefully(web_fixture, error_fixture):
    """The error page can be customised, and depending on what was specified for the app, degrades gracefully."""

    wsgi_app = web_fixture.new_wsgi_app(site_root=error_fixture.MainUI)
    web_fixture.reahl_server.set_app(wsgi_app)
#    browser = Browser(wsgi_app)
    browser = web_fixture.driver_browser

    browser.open('/error?error_message=something+went+wrong&error_source_href=/a_page')
    assert browser.current_url.path == '/error'
    error_fixture.check_error_page_contents(browser)
    assert browser.is_element_present(XPath.paragraph().including_text('something went wrong'))
    assert Url(browser.get_attribute(XPath.link().with_text('Ok'), 'href')).path == '/a_page'


