# Copyright 2009, 2011, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from __future__ import unicode_literals
from __future__ import print_function
from reahl.component.context import ExecutionContext
from reahl.tofu import TestSuite, Fixture, test
from reahl.stubble import stubclass

@stubclass(TestSuite)
class TestSuiteStub(TestSuite):
    @test(Fixture)
    def a_method(self, fixture):
        self.__class__.saved_set_up = fixture.run_fixture.is_set_up
        self.__class__.saved_torn_down = fixture.run_fixture.is_torn_down
        self.__class__.saved_fixture = fixture
        self.__class__.saved_context = ExecutionContext.get_context()

class TestSuiteStubB(TestSuiteStub):
    pass

TestSuite = None # In order to fool the Harness into NOT wanting to load and run it as well...
