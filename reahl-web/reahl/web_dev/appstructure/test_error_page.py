# Copyright 2019 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.tofu.pytestsupport import with_fixtures
from reahl.tofu import Fixture, scenario

from reahl.webdev.tools import Browser

from reahl.web.fw import UserInterface, Widget, FactoryDict, UserInterfaceFactory, RegexPath, UrlBoundView
from reahl.web.ui import HTML5Page, P, A, Div, Slot

from reahl.web_dev.fixtures import WebFixture, BasicPageLayout


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
                super(BreakingWidget, self).__init__(view)
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
    class BreakingWidget(Widget):
        def __init__(self, view):
            super(BreakingWidget, self).__init__(view)
            raise Exception('breaking intentionally during __init__')

    @scenario
    def page_specified_on_view(self):
        class MainUI(UserInterface):
            def assemble(self):
                self.define_view('/a_page', page=self.BreakingWidget.factory())
        self.MainUI = MainUI

    @scenario
    def page_specified_on_user_interface(self):
        todo

    @scenario
    def expicit_call_to_define_error_view(self):
        todo

        
@with_fixtures(WebFixture, ErrorDegradeFixture)
def test_error_page_degrades_gracefully(web_fixture, error_fixture):
    """The error page can be customised, and depending on what was specified for the app, degrades gracefully."""

    wsgi_app = web_fixture.new_wsgi_app(site_root=error_fixture.MainUI)
    browser = Browser(wsgi_app)

    wsgi_app.config.reahlsystem.debug = False
    
    browser.open('/a_page')
    assert browser.current_url.path == '/error'


# If an uncaught error occurs, the user is sent to an error page that displays the message.
#  scenarios:
#    - where the view is defined by page= (ie, no page defined on the UI)
#    - where UserInterface.define_page() was called in its assemble() 
#    - where we explicitly call UserInterface.define_error_view()
