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



from reahl.tofu import scenario, expected, Fixture
from reahl.tofu.pytestsupport import with_fixtures

from reahl.browsertools.browsertools import Browser

from reahl.component.exceptions import ProgrammerError
from reahl.web.fw import UserInterface
from reahl.web.ui import P, HTML5Page

from reahl.web_dev.fixtures import WebFixture


class UserInterfaceErrorScenarios(Fixture):
    @scenario
    def plug_in_to_nonexistant_name(self):
        self.slot_map = {'name': 'nonexistent'}

    @scenario
    def view_name_not_mapped(self):
        self.slot_map = {}


@with_fixtures(WebFixture, UserInterfaceErrorScenarios)
def test_ui_slots_map_error(web_fixture, user_interface_error_scenarios):

    class SimpleUserInterface(UserInterface):
        def assemble(self):
            root = self.define_view('/', title='View')
            root.set_slot('name', P.factory())

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page)
            self.define_user_interface('/a_ui',  SimpleUserInterface,  user_interface_error_scenarios.slot_map, name='test_ui')

    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    with expected(ProgrammerError):
        browser.open('/a_ui/')


