# Copyright 2013-2020 Reahl Software Services (Pty) Ltd. All rights reserved.
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




from reahl.tofu import set_up, tear_down, scenario, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.component.context import ExecutionContext
from reahl.dev.fixtures import ContextAwareFixture





class ContextAwareFixtureStub(ContextAwareFixture):
    def new_context(self):
        return ExecutionContext()

    def check_context(self):
        assert ExecutionContext.get_context() is self.context

    @set_up
    def setup_marked_method(self):
        self.check_context()

    @tear_down
    def tear_down_marked_method(self):
        self.check_context()

    def set_up(self):
        self.check_context()

    def tear_down(self):
        self.check_context()

    @scenario
    def only_one(self):
        self.check_context()

    def new_thing(self):
        self.check_context()
        yield None
        self.check_context()
    

@with_fixtures(ContextAwareFixtureStub)
def test_context_aware_setup_and_tear_down(fixture):
    """The setup, tear_down actions and scenarios of a ContextAwareFixture are run within its .context."""
    fixture.thing


@with_fixtures(ContextAwareFixtureStub)
def test_context_aware_tests_in_context(fixture):
    """Tests using a ContextAwareFixture are run within its .context."""
    assert ExecutionContext.get_context() is fixture.context


@uses(other=ContextAwareFixtureStub)
class ContextAwareDeepFixture(ContextAwareFixture):
    def new_context(self):
        return ExecutionContext()
    
@with_fixtures(ContextAwareDeepFixture, ContextAwareFixtureStub)
def test_context_aware_tests_in_multiple_contexts(most_dependent_fixture, least_dependent_fixture):
    """When using multiple ContextAwareFixtures in a test, the context of most-dependent Fixture wins."""
    assert ExecutionContext.get_context() is not least_dependent_fixture.context
    assert ExecutionContext.get_context() is most_dependent_fixture.context
    
