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
from reahl.web.fw import ReahlWSGIApplication, UserInterface, UrlBoundView
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

        class UIWithParameterisedViews(UserInterface):
            def assemble(self):
                self.define_regex_view(u'/(?P<incorrect_name_for_key>.*)', u'/${key}', view_class=ParameterisedView, some_key=Field(required=True))

        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                self.define_user_interface(u'/a_ui',  UIWithParameterisedViews,  {}, name=u'test_ui')

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        def check_message(ex):
            return unicode(ex).startswith('The arguments contained in URL')
        with expected(ProgrammerError, test=check_message):
            browser.open('/a_ui/test1/')



class ParameterisedUserInterfaceErrors(WebFixture):
    def new_wsgi_app(self):
        fixture = self
        class RegexUserInterface(UserInterface):
            def assemble(self, ui_key=None):
                self.name = u'user_interface-%s' % ui_key

        class UIWithParameterisedUserInterfaces(UserInterface):
            def assemble(self):
                self.define_regex_user_interface(u'/(?P<xxx>[^/]*)', u'N/A', RegexUserInterface,
                                         {u'user_interface-slot': u'main'},
                                         ui_key=Field(required=True))

        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                self.define_user_interface(u'/a_ui',  UIWithParameterisedUserInterfaces,  {}, name=u'test_ui')

        return super(ParameterisedUserInterfaceErrors, self).new_wsgi_app(site_root=MainUI)
       

@istest
class ParameterisedErrorsTests(object):
    @test(ParameterisedUserInterfaceErrors)
    def missing_variable_in_regex(self, fixture):

        browser = Browser(fixture.wsgi_app)

        with expected(RequiredConstraint):
            browser.open('/a_ui/test1/')
