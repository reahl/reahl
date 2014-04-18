# Copyright 2011, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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
from reahl.tofu import Fixture, test, scenario
from reahl.tofu import vassert, expected

from reahl.component.modelinterface import Field, IntegerField, exposed, Event
from reahl.web.fw import ReahlWSGIApplication, UserInterface, UrlBoundView, IdentityDictionary, CannotCreate
from reahl.web.ui import HTML5Page, TwoColumnPage, P, A, Form, Button
from reahl.webdev.tools import Browser, WidgetTester, XPath
from reahl.web_dev.fixtures import WebFixture, ReahlWSGIApplicationStub


@istest
class ParameterisedTests(object):
    class ParameterisedScenarios(WebFixture):
        class ParameterisedView(UrlBoundView):
            def assemble(self, some_arg=None):
                if some_arg == u'doesnotexist':
                    raise CannotCreate()
                self.title = u'View for: %s' % some_arg
                self.set_slot(u'main', P.factory(text=u'content for %s' % some_arg))

        @scenario
        def normal_arguments(self):
            """Arguments can be sent from where the View is defined."""
            self.argument = u'some arg'
            self.expected_value = u'some arg'
            self.url = u'/aregion/aview'
            self.should_exist = True
        
        @scenario
        def url_arguments(self):
            """Arguments can be parsed from an URL, iff they are specified to the definition as Fields."""
            self.argument = Field()
            self.expected_value = u'test1'
            self.url = u'/aregion/aview/test1'
            self.should_exist = True
            
        @scenario
        def define_entire_page(self):
            """The dynamically defined View can also be define its entire page to be rendered, instead of slots"""
            self.url_arguments() # same setup as this except:
            class SimplePage(HTML5Page):
                def __init__(self, view, some_arg):
                    super(SimplePage, self).__init__(view)
                    self.body.add_child(P(view, text=u'content for %s' % some_arg))

            class ParameterisedView(UrlBoundView):
                def assemble(self, some_arg=None):
                    if some_arg == u'doesnotexist':
                        raise CannotCreate()
                    self.title = u'View for: %s' % some_arg
                    self.set_page(SimplePage.factory(some_arg))

            self.ParameterisedView = ParameterisedView
            
        @scenario
        def cannot_create(self):
            """To indicate that a view does not exist for the given arguments, the .assemble() 
               method of the View should raise CannotCreate()."""
            self.argument = u'doesnotexist'
            self.url = u'/aregion/aview'
            self.should_exist = False

    @test(ParameterisedScenarios)
    def views_with_parameters(self, fixture):
        """Views can have arguments that originate from code, or are parsed from the URL."""

        class UIWithParameterisedViews(UserInterface):
            def assemble(self):
                self.define_view(u'/aview', view_class=fixture.ParameterisedView, some_arg=fixture.argument) 

        class MainUI(UserInterface):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/aregion',  UIWithParameterisedViews,  {u'main': u'main'}, name=u'myregion')

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        if fixture.should_exist:
            browser.open(fixture.url)
            vassert( browser.title == u'View for: %s' % fixture.expected_value )
            vassert( browser.is_element_present(XPath.paragraph_containing(u'content for %s' % fixture.expected_value)) )
        else:
            browser.open(fixture.url, status=404)

    @test(WebFixture)
    def views_from_regex(self, fixture):
        """Parameterised Views can also be added based on a regex over the url."""

        class ParameterisedView(UrlBoundView):
            def assemble(self, some_key=None):
                self.title = u'View for: %s' % some_key
            
        class UIWithParameterisedViews(UserInterface):
            def assemble(self):
                self.define_regex_view(u'/someurl_(?P<some_key>.*)', u'/someurl_${some_key}', view_class=ParameterisedView,
                                       some_key=Field(required=True))

        class MainUI(UserInterface):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/aregion',  UIWithParameterisedViews,  {}, name=u'myregion')

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        # Parameterisedally constructing a View from an URL
        browser.open('/aregion/someurl_test1')
        vassert( browser.title == u'View for: test1' )

    @test(WebFixture)
    def regions_from_regex(self, fixture):
        """Sub Regions can be created on the fly on a UserInterface, based on the URL visited. To indicate that a
           UserInterface does not exist, the creation method should return None."""

        class RegexRegion(UserInterface):
            def assemble(self, region_key=None):
                if region_key == u'doesnotexist':
                    raise CannotCreate()

                self.name = u'region-%s' % region_key
                root = self.define_view(u'/', title=u'Simple region %s' % self.name)
                root.set_slot(u'region-slot', P.factory(text=u'in region slot'))

        class UIWithParameterisedRegions(UserInterface):
            def assemble(self):
                self.define_regex_region(u'/apath/(?P<region_key>[^/]*)',
                                         u'/apath/${region_key}',
                                         RegexRegion,
                                         {u'region-slot': u'main'},
                                         region_key=Field())

        class MainUI(UserInterface):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/aregion',  UIWithParameterisedRegions,  IdentityDictionary(), name=u'myregion')

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        # A sub-region is dynamically created from an URL
        browser.open('/aregion/apath/test1/')
        vassert( browser.title == u'Simple region region-test1' )

        # The slots of the sub-region is correctly plugged into the main window
        [p] = browser.lxml_html.xpath('//p')
        vassert( p.text == u'in region slot' )

        # Another sub-region is dynamically created from an URL
        browser.open('/aregion/apath/another/')
        vassert( browser.title == u'Simple region region-another' )

        # When the URL cannot be mapped
        browser.open('/aregion/apath/doesnotexist/', status=404)


    class ParameterisedRegionScenarios(WebFixture):
        @scenario
        def normal_arguments(self):
            """Arguments can be sent from where the UserInterface is defined."""
            self.argument = u'some arg'
            self.expected_value = u'some arg'
            self.url = u'/aregion/parameterisedregion/aview'
            self.should_exist = True
        
        @scenario
        def url_arguments(self):
            """Arguments can be parsed from an URL, iff they are specified to the definition as Fields."""
            self.argument = Field()
            self.expected_value = u'test1'
            self.url = u'/aregion/parameterisedregion/test1/aview'
            self.should_exist = True
            
        @scenario
        def cannot_create(self):
            """To indicate that a UserInterface does not exist for the given arguments, the .assemble() 
               method of the UserInterface should raise CannotCreate()."""
            self.argument = u'doesnotexist'
            self.url = u'/aregion/parameterisedregion/aview'
            self.should_exist = False

    @test(ParameterisedRegionScenarios)
    def parameterised_regions(self, fixture):
        """Sub Regions can also be parameterised by defining arguments in .define_region, and receiving them in .assemble()."""

        class ParameterisedRegion(UserInterface):
            def assemble(self, region_arg=None):
                if region_arg == u'doesnotexist':
                    raise CannotCreate()

                self.name = u'region-%s' % region_arg
                root = self.define_view(u'/aview', title=u'Simple region %s' % self.name)
                root.set_slot(u'region-slot', P.factory(text=u'in region slot'))


        class UIWithParameterisedRegions(UserInterface):
            def assemble(self):
                self.define_region(u'/parameterisedregion', ParameterisedRegion, {u'region-slot': u'main'}, 
                                   region_arg=fixture.argument,
                                   name=u'paramregion')

        class MainUI(UserInterface):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/aregion',  UIWithParameterisedRegions,  IdentityDictionary(), name=u'myregion')

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        if fixture.should_exist:
            browser.open(fixture.url)
            
            # The correct argument was passed
            vassert( browser.title == u'Simple region region-%s' % fixture.expected_value )

            # The slots of the sub-region is correctly plugged into the main window
            [p] = browser.lxml_html.xpath('//p')
            vassert( p.text == u'in region slot' )
        else:
            # When the URL cannot be mapped
            browser.open(fixture.url, status=404)




