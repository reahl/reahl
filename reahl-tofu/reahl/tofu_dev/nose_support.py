# Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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
from unittest import TestResult

from nose.tools import istest
from nose.loader import TestLoader

from reahl.tofu import test, Fixture, scenario

@istest
class NoseSupportTests(object):
    def run_tests(self, test_class):
        res = TestResult()
        loader = TestLoader()
        suite = loader.loadTestsFromTestClass(test_class)
        suite(res)
        return res
        
    @istest
    def separate_fixtures_supplied_to_nose(self):
        """Specifying Fixtures to nose tests."""

        class FixtureStub(Fixture):
            set_up_done = False
            tear_down_done = False
            def set_up(self):
                self.set_up_done = True
            def tear_down(self):
                self.tear_down_done = True

        a = []
        class TestClass(object):
            @test(FixtureStub)
            def some_test(self, fixture):
                a.append(fixture)
                assert fixture.set_up_done
                assert not fixture.tear_down_done

        res = self.run_tests(TestClass)
        fixture = a[0]

        assert res.wasSuccessful
        assert fixture.set_up_done
        assert fixture.tear_down_done


    @istest
    def scenarios(self):
        """When a Fixture contains multiple scenarios, the test is run once for each scenario."""

        class Scenarios(Fixture):
            @scenario
            def one(self):
                self.n = 1
            @scenario
            def two(self):
                self.n = 2

        a = []
        class TestClass(object):
            @test(Scenarios)
            def some_test(self, fixture):
                a.append(fixture)

        res = self.run_tests(TestClass)
        fixture_1, fixture_2 = a

        assert res.wasSuccessful
        assert fixture_1.n == 1
        assert fixture_2.n == 2

    @istest
    def single_scenario(self):
        """A single scenario can be used as the fixture for a test."""
        class Scenarios(Fixture):
            @scenario
            def one(self):
                self.n = 1
            @scenario
            def two(self):
                self.n = 2

        a = []
        class TestClass(object):
            @test(Scenarios.one)
            def some_test(self, fixture):
                a.append(fixture)
        
        res = self.run_tests(TestClass)

        assert len(a) == 1
        [fixture] = a
        assert fixture.n == 1
        assert res.testsRun == 1
        assert res.wasSuccessful

    @istest
    def contextual_runs(self):
        """Tests can be run in the context of their fixtures (if any)."""

        class ContextManager(object):
            entered = False
            exited = False
            def __enter__(self):
                self.entered = True
            def __exit__(self, exception, value, trace):
                self.exited = True

        class ContextualFixture(Fixture):
            def new_context(self):
                return ContextManager()

        a = []
        class TestClass(object):
            @test(ContextualFixture)
            def test_something(self, fixture):
                a.append(fixture)
                assert fixture.context.entered
                assert not fixture.context.exited

        res = self.run_tests(TestClass)
        assert res.wasSuccessful, res.errors
        [fixture] = a
        assert fixture.context.exited

