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

from reahl.web.fw import ReahlWSGIApplication, Region
from reahl.web.ui import TwoColumnPage, P, A
from reahl.webdev.tools import Browser, WidgetTester
from reahl.web_dev.fixtures import WebFixture
from reahl.component.exceptions import ProgrammerError

class RegionErrorScenarios(WebFixture):
    def new_wsgi_app(self):
        fixture = self
        class SimpleRegion(Region):
            def assemble(self):
                root = self.define_view(u'/', title=u'View')
                root.set_slot(u'name', P.factory())

        class MainApp(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/aregion',  SimpleRegion,  {}, name=u'testregion')

        return super(RegionErrorScenarios, self).new_wsgi_app(site_root=MainApp)

    @scenario
    def plug_in_to_nonexistant_name(self):
        self.slot_map = {u'name': u'nonexistent'}

    @scenario
    def view_name_not_mapped(self):
        self.slot_map = {}

        
@istest
class RegionErrorTests(object):
    @test(RegionErrorScenarios)
    def region_slots_map_error(self, fixture):
        browser = Browser(fixture.wsgi_app)

        with expected(ProgrammerError):
            browser.open('/aregion/')


