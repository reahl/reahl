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

from reahl.component.modelinterface import Field, RequiredConstraint
from reahl.component.exceptions import ProgrammerError
from reahl.web.fw import ReahlWSGIApplication, Region, UrlBoundView
from reahl.web.ui import TwoColumnPage, P, A
from reahl.webdev.tools import Browser, WidgetTester
from reahl.web_dev.fixtures import WebFixture

@istest
class ParameterisedViewErrors(object):
    @test(WebFixture)
    def missing_variable_in_regex(self, fixture):
        """If a variable is missing from the regex, an appropriate error is raised."""

        class ParameterisedView(UrlBoundView):
            def assemble(self, some_key=None):
                self.title = u'View for: %s' % some_key

        class RegionWithParameterisedViews(Region):
            def assemble(self):
                self.define_regex_view(u'/(?P<incorrect_name_for_key>.*)', u'/${key}', view_class=ParameterisedView, some_key=Field(required=True))

        class MainApp(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/aregion',  RegionWithParameterisedViews,  {}, name=u'testregion')

        wsgi_app = fixture.new_wsgi_app(site_root=MainApp)
        browser = Browser(wsgi_app)

        def check_message(ex):
            return unicode(ex).startswith('The arguments contained in URL')
        with expected(ProgrammerError, test=check_message):
            browser.open('/aregion/test1/')



class ParameterisedRegionErrors(WebFixture):
    def new_wsgi_app(self):
        fixture = self
        class RegexRegion(Region):
            def assemble(self, region_key=None):
                self.name = u'region-%s' % region_key

        class RegionWithParameterisedRegions(Region):
            def assemble(self):
                self.define_regex_region(u'/(?P<xxx>[^/]*)', u'N/A', RegexRegion,
                                         {u'region-slot': u'main'},
                                         region_key=Field(required=True))

        class MainApp(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/aregion',  RegionWithParameterisedRegions,  {}, name=u'testregion')

        return super(ParameterisedRegionErrors, self).new_wsgi_app(site_root=MainApp)
       

@istest
class ParameterisedErrorsTests(object):
    @test(ParameterisedRegionErrors)
    def missing_variable_in_regex(self, fixture):

        browser = Browser(fixture.wsgi_app)

        with expected(RequiredConstraint):
            browser.open('/aregion/test1/')
