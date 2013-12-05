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
from reahl.tofu import Fixture, test, vassert, expected, NoException
from reahl.stubble import EmptyStub

from reahl.web.fw import Region
from reahl.web.ui import TwoColumnPage, P
from reahl.webdev.tools import Browser
from reahl.web_dev.fixtures import WebFixture, ReahlWebApplicationStub
from reahl.component.exceptions import ProgrammerError, IncorrectArgumentError, IsSubclass, IsInstance

@istest
class AppBasicsTests(object):
    @test(WebFixture)
    def basic_assembly(self, fixture):
        """An application is built by extending ReahlWebApplication and providing an assemble method.
        
        The most basic application needs a main window and a view. Views are mapped to Urls.
        """
        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_view(u'/', title=u'Hello')

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)

        # GETting the URL results in the HTML for that View
        browser.open('/')
        vassert( browser.title == u'Hello' )

        # The headers are set correctly
        response = browser.last_response
        vassert( response.content_length == 893 )
        vassert( response.content_type == 'text/html' )
        vassert( response.charset == 'utf-8' )

        # Invalid URLs do not exist
        browser.open('/nonexistantview/', status=404)

    @test(WebFixture)
    def basic_error1(self, fixture):
        """Sending the the wrong kind of thing as widget_class to define_main_window is reported to the programmer."""
        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(EmptyStub)
                self.define_view(u'/', title=u'Hello')

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)

        with expected(IsSubclass):
            browser.open('/')

    @test(WebFixture)
    def basic_error2(self, fixture):
        """Sending the the wrong arguments for the specified class to define_main_window is reported to the programmer."""
        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage, 1, 2)
                self.define_view(u'/', title=u'Hello')

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)

        def check_exc(ex):
            msg = str(ex)
            vassert( msg.startswith('define_main_window was called with arguments that do not match those expected by') )
        with expected(IncorrectArgumentError, test=check_exc):
            browser.open('/')

    @test(WebFixture)
    def basic_error3(self, fixture):
        """Forgetting to define a main_window is reported to the programmer."""
        class MainRegion(Region):
            def assemble(self):
                self.define_view(u'/', title=u'Hello')

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)

        def check_exc(ex):
            msg = str(ex)
            vassert( msg == 'there is no main_window defined for /' )
        with expected(ProgrammerError, test=check_exc):
            browser.open('/')
            
    @test(WebFixture)
    def slots(self, fixture):
        """A View modifies the main window by populating named Slots in the main window with Widgets."""
        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                home = self.define_view(u'/', title=u'Hello')
                home.set_slot(u'main', P.factory(text=u'Hello world'))
                home.set_slot(u'footer', P.factory(text=u'I am the footer'))

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)
        
        browser.open('/')
        vassert( browser.title == u'Hello' )
        [main_p, footer_p] = browser.lxml_html.xpath('//p')
        vassert( main_p.text == u'Hello world' )
        vassert( footer_p.text == u'I am the footer' )

    @test(WebFixture)
    def slot_error(self, fixture):
        """Supplying contents for a slot that does not exist results in s sensible error."""
        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                home = self.define_view(u'/', title=u'Hello')
                home.set_slot(u'main', P.factory(text=u'Hello world'))
                home.set_slot(u'nonexistantslotname', P.factory(text=u'I am breaking'))

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)

        def check_exc(ex):
            vassert( str(ex).startswith(u'An attempt was made to plug Widgets into the following slots that do not exist') )

        with expected(ProgrammerError, test=check_exc):
            browser.open('/')


    @test(WebFixture)
    def slot_defaults(self, fixture):
        """If a View does not specify contents for a Slot, the Slot will be populated by the window's default
           widget for that slot if specified, else it will be left empty.
        """
        class MainRegion(Region):
            def assemble(self):
                main = self.define_main_window(TwoColumnPage)
                main.add_default_slot(u'main', P.factory(text=u'defaulted slot contents'))
                self.define_view(u'/', title=u'Hello')

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)
        
        browser.open('/')

        # The default widget for the main slot is used
        [p] = browser.lxml_html.xpath('//p')
        vassert( p.text == 'defaulted slot contents' )

        # The header slot has no default, and is thus left empty
        header_contents = browser.lxml_html.xpath('//header/*')
        vassert( not header_contents )
