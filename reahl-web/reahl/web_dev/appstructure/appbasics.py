# Copyright 2010-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from nose.tools import istest
from reahl.tofu import Fixture, test, vassert, expected, NoException, scenario
from reahl.stubble import EmptyStub

from reahl.web.fw import Region
from reahl.web.ui import HTML5Page, TwoColumnPage, P
from reahl.webdev.tools import Browser
from reahl.web_dev.fixtures import WebFixture, ReahlWSGIApplicationStub
from reahl.component.exceptions import ProgrammerError, IncorrectArgumentError, IsSubclass, IsInstance

@istest
class AppBasicsTests(object):
    class BasicScenarios(WebFixture):
        @scenario
        def view_with_page(self):
            class SimplePage(HTML5Page):
                def __init__(self, view):
                    super(SimplePage, self).__init__(view)
                    self.body.add_child(P(view, text=u'Hello world!'))

            class MainApp(Region):
                def assemble(self):
                    self.define_view(u'/', title=u'Hello', page=SimplePage.factory())

            self.MainApp = MainApp
            self.expected_content_length = 685
            self.content_includes_p = True

        @scenario
        def view_with_set_page(self):
            class SimplePage(HTML5Page):
                def __init__(self, view):
                    super(SimplePage, self).__init__(view)
                    self.body.add_child(P(view, text=u'Hello world!'))

            class MainApp(Region):
                def assemble(self):
                    home = self.define_view(u'/', title=u'Hello')
                    home.set_page(SimplePage.factory())

            self.MainApp = MainApp
            self.expected_content_length = 685
            self.content_includes_p = True

        @scenario
        def region_with_main_window(self):
            class MainApp(Region):
                def assemble(self):
                    self.define_main_window(TwoColumnPage)
                    self.define_view(u'/', title=u'Hello')

            self.MainApp = MainApp
            self.expected_content_length = 893
            self.content_includes_p = False

    @test(BasicScenarios)
    def basic_assembly(self, fixture):
        """An application is built by extending Region, and defining this Region in an .assemble() method.

        To define the Region, several Views are defined. Views are mapped to URLs. When a user GETs
        the URL of a View, a page is rendered back to the user. How that page is created
        can happen in different ways, as illustrated by each scenario of this test.
        """
        wsgi_app = fixture.new_wsgi_app(site_root=fixture.MainApp)
        browser = Browser(wsgi_app)

        # GETting the URL results in the HTML for that View
        browser.open('/')
        vassert( browser.title == u'Hello' )

        if fixture.content_includes_p:
            [message] = browser.lxml_html.xpath('//p')
            vassert( message.text == u'Hello world!' )

        # The headers are set correctly
        response = browser.last_response
        vassert( response.content_length == fixture.expected_content_length )
        vassert( response.content_type == 'text/html' )
        vassert( response.charset == 'utf-8' )

        # Invalid URLs do not exist
        browser.open('/nonexistantview/', status=404)



    @test(WebFixture)
    def basic_error1(self, fixture):
        """Sending the the wrong kind of thing as widget_class to define_main_window is reported to the programmer."""
        class MainApp(Region):
            def assemble(self):
                self.define_main_window(EmptyStub)
                self.define_view(u'/', title=u'Hello')

        wsgi_app = fixture.new_wsgi_app(site_root=MainApp)
        browser = Browser(wsgi_app)

        with expected(IsSubclass):
            browser.open('/')

    @test(WebFixture)
    def basic_error2(self, fixture):
        """Sending the the wrong arguments for the specified class to define_main_window is reported to the programmer."""
        class MainApp(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage, 1, 2)
                self.define_view(u'/', title=u'Hello')

        wsgi_app = fixture.new_wsgi_app(site_root=MainApp)
        browser = Browser(wsgi_app)

        def check_exc(ex):
            msg = str(ex)
            vassert( msg.startswith('define_main_window was called with arguments that do not match those expected by') )
        with expected(IncorrectArgumentError, test=check_exc):
            browser.open('/')

    @test(WebFixture)
    def basic_error3(self, fixture):
        """Forgetting to define either a main_window of a page for a View is reported to the programmer."""
        class MainApp(Region):
            def assemble(self):
                self.define_view(u'/', title=u'Hello')

        wsgi_app = fixture.new_wsgi_app(site_root=MainApp)
        browser = Browser(wsgi_app)

        def check_exc(ex):
            msg = str(ex)
            vassert( msg == 'there is no main_window defined for /' )
        with expected(ProgrammerError, test=check_exc):
            browser.open('/')

    class SlotScenarios(WebFixture):
        @scenario
        def main_window_on_region(self):
            class MainApp(Region):
                def assemble(self):
                    self.define_main_window(TwoColumnPage)
                    home = self.define_view(u'/', title=u'Hello')
                    home.set_slot(u'main', P.factory(text=u'Hello world'))
                    home.set_slot(u'footer', P.factory(text=u'I am the footer'))
            self.MainApp = MainApp

        @scenario
        def main_window_on_view(self):
            class MainApp(Region):
                def assemble(self):
                    home = self.define_view(u'/', title=u'Hello')
                    home.set_page(TwoColumnPage.factory())
                    home.set_slot(u'main', P.factory(text=u'Hello world'))
                    home.set_slot(u'footer', P.factory(text=u'I am the footer'))
            self.MainApp = MainApp

            
    @test(SlotScenarios)
    def slots(self, fixture):
        """A View modifies the main window by populating named Slots in the main window with Widgets."""
        wsgi_app = fixture.new_wsgi_app(site_root=fixture.MainApp)
        browser = Browser(wsgi_app)
        
        browser.open('/')
        vassert( browser.title == u'Hello' )
        [main_p, footer_p] = browser.lxml_html.xpath('//p')
        vassert( main_p.text == u'Hello world' )
        vassert( footer_p.text == u'I am the footer' )

    @test(WebFixture)
    def slot_error(self, fixture):
        """Supplying contents for a slot that does not exist results in s sensible error."""
        class MainApp(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                home = self.define_view(u'/', title=u'Hello')
                home.set_slot(u'main', P.factory(text=u'Hello world'))
                home.set_slot(u'nonexistantslotname', P.factory(text=u'I am breaking'))

        wsgi_app = fixture.new_wsgi_app(site_root=MainApp)
        browser = Browser(wsgi_app)

        def check_exc(ex):
            vassert( str(ex).startswith(u'An attempt was made to plug Widgets into the following slots that do not exist') )

        with expected(ProgrammerError, test=check_exc):
            browser.open('/')


    @test(WebFixture)
    def slot_defaults(self, fixture):
        """If a View does not specify contents for a Slot, the Slot will be populated by the window's default
           widget for that slot if specified, else it will be left empty.
        """
        class MainApp(Region):
            def assemble(self):
                main = self.define_main_window(TwoColumnPage)
                main.add_default_slot(u'main', P.factory(text=u'defaulted slot contents'))
                self.define_view(u'/', title=u'Hello')

        wsgi_app = fixture.new_wsgi_app(site_root=MainApp)
        browser = Browser(wsgi_app)
        
        browser.open('/')

        # The default widget for the main slot is used
        [p] = browser.lxml_html.xpath('//p')
        vassert( p.text == 'defaulted slot contents' )

        # The header slot has no default, and is thus left empty
        header_contents = browser.lxml_html.xpath('//header/*')
        vassert( not header_contents )
