# Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from __future__ import print_function, unicode_literals, absolute_import, division

pytest_plugins = '_pytest.pytester'

def test_use_with_pytest(testdir):
    """Fixtures can be used as pytest fixture functions."""

    p = testdir.makepyfile('''
    from reahl.tofu import Fixture
    class FixtureStub(Fixture):
        set_up_done = False
        tear_down_done = False
        def set_up(self):
            assert not self.set_up_done
            self.set_up_done = True
        def tear_down(self):
            assert self.test_ran
            FixtureStub.tear_down_done = True


    pyfix = FixtureStub.as_pytest_fixture()
    def test_func(pyfix):
        assert pyfix.set_up_done
        assert not pyfix.tear_down_done
        pyfix.test_ran = True

    def test_torndown():
        assert FixtureStub.tear_down_done
    ''')

    result = testdir.runpytest(p)
    result.reprec.assertoutcome(passed=2)



def test_scenarios(testdir):
    """When a Fixture contains multiple scenarios, the test is run once for each scenario."""

    p = testdir.makepyfile('''
    from reahl.tofu import Fixture, scenario
    class Scenarios(Fixture):
        @scenario
        def one(self):
            self.n = 1
        @scenario
        def two(self):
            self.n = 2

    scenario_fixture = Scenarios.as_pytest_fixture()

    Scenarios.runs = []

    def test_something(scenario_fixture):
        Scenarios.runs.append(scenario_fixture)

    def test_all_scenarios_run_with_correct_setups():
        fixture_1, fixture_2 = Scenarios.runs

        assert fixture_1.n == 1
        assert fixture_2.n == 2
    ''')

    result = testdir.runpytest(p)
    result.reprec.assertoutcome(passed=3)


def test_single_scenario(testdir):
    """A single scenario can be used as the fixture for a test."""

    p = testdir.makepyfile('''
    from reahl.tofu import Fixture, scenario
    class Scenarios(Fixture):
        @scenario
        def one(self):
            self.n = 1
        @scenario
        def two(self):
            self.n = 2

    a = []
    one = Scenarios.one.as_pytest_fixture()

    def test_something(one):
        a.append(one)

    def test_result():
        assert len(a) == 1
        [fixture] = a
        assert fixture.n == 1
    ''')
    result = testdir.runpytest(p)
    result.reprec.assertoutcome(passed=2)


def test_contextual_runs(testdir):
    """Tests can be run in the context of their fixtures (if any)."""

    p = testdir.makepyfile('''
    from reahl.tofu import Fixture, scenario
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
    context_fixture = ContextualFixture.as_pytest_fixture()

    a = []
    def test_something(context_fixture):
        a.append(context_fixture)
        assert context_fixture.context.entered
        assert not context_fixture.context.exited

    def test_result():
        [fixture] = a
        assert fixture.context.exited
    ''')
    result = testdir.runpytest(p)
    result.reprec.assertoutcome(passed=2)
