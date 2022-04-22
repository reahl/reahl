# Copyright 2013-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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



from reahl.tofu import test, Fixture
from unittest import TestSuite

#
# We declare the fixture classes here, so they could potentially be
#  re-used by several TestSuites or methods
#
class Fixture(Fixture):
    def set_up(self):
        print('setting up default fixture for this suite')
        self.stuff = 'this was set up in the fixture'
    def tear_down(self):
        print('tearing down default fixture for this suite')


class Other(Fixture):
    def set_up(self):
        print('other setup')
        self.something = 'this was set up in the Other fixture'
    def tear_down(self):
        print('other tear_down')

#
# Our main example TestSuite class
#
class SomeTests(TestSuite):
    @test(Fixture)
    def one(self, fixture):
        print('test one: %s' % fixture.stuff)

    @test(Fixture)
    def two(self, fixture):
        """docstrings work as with unittest"""
        assert None, 'something broke in test two'

    @test(Fixture)
    def three(self, fixture):
        assert None, 'something broke in test three'

    @test(Other)
    def four(self, fixture):
        print('test four - using the other fixture: %s' % fixture)

    def iamnotatest(self):
        print('i am not a test method, and should not run with the tests')



