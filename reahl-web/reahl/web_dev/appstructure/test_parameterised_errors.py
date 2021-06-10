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

from reahl.browsertools.browsertools import Browser

from reahl.component.modelinterface import Field, RequiredConstraint
from reahl.component.exceptions import ProgrammerError
from reahl.web.fw import UrlBoundView, UserInterface
from reahl.web.ui import HTML5Page

from reahl.web_dev.fixtures import WebFixture


@with_fixtures(WebFixture)
def test_missing_variable_in_regex(web_fixture):
    """If a variable is missing from the regex, an appropriate error is raised."""

    class ParameterisedView(UrlBoundView):
        def assemble(self, some_key=None):
            self.title = 'View for: %s' % some_key

    class UIWithParameterisedViews(UserInterface):
        def assemble(self):
            self.define_regex_view('/(?P<incorrect_name_for_key>.*)', '/${key}', view_class=ParameterisedView, some_key=Field(required=True))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page)
            self.define_user_interface('/a_ui',  UIWithParameterisedViews,  {}, name='test_ui')

    fixture = web_fixture

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    with expected(ProgrammerError, test='The arguments contained in URL.*'):
        browser.open('/a_ui/test1/')


@with_fixtures(WebFixture)
def test_missing_variable_in_ui_regex(web_fixture):

    class RegexUserInterface(UserInterface):
        def assemble(self, ui_key=None):
            self.name = 'user_interface-%s' % ui_key

    class UIWithParameterisedUserInterfaces(UserInterface):
        def assemble(self):
            self.define_regex_user_interface('/(?P<xxx>[^/]*)', 'N/A', RegexUserInterface,
                                             {},
                                             ui_key=Field(required=True))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page)
            self.define_user_interface('/a_ui',  UIWithParameterisedUserInterfaces,  {}, name='test_ui')


    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)

    browser = Browser(wsgi_app)

    with expected(RequiredConstraint):
        browser.open('/a_ui/test1/')
