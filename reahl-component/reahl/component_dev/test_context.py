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


from reahl.tofu import set_up, tear_down, scenario, uses
from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import EmptyStub

from reahl.component.context import ExecutionContext
from reahl.component_dev.fixtures import ContextAwareFixture


def test_execution_context_basics():
    """An ExecutionContext is like a global variable for a particular call stack. To create an
       ExecutionContext for a call stack, use it in a with statement."""

    def do_something():
        return ExecutionContext.get_context()
    def do_high_level_something():
        return do_something()

    some_context = ExecutionContext().install()

    found_context = do_high_level_something()

    assert found_context is some_context


def test_execution_context_stacking():
    """When an ExecutionContext overrides a deeper one on the call stack, it will retain the same id."""
    some_context = ExecutionContext().install()

    def deeper_code():
        deeper_context = ExecutionContext().install()
        assert ExecutionContext.get_context_id() == some_context.id
        return deeper_context

    deeper_context = deeper_code()
    assert some_context is not deeper_context
    assert some_context.id == deeper_context.id


def test_contents():
    """A Session, Config or SystemControl may be set on the ExecutionContext."""
    some_context = ExecutionContext()

    session = EmptyStub()
    config = EmptyStub()
    system_control = EmptyStub()

    some_context.session = session
    some_context.config = config
    some_context.system_control = system_control

    assert some_context.session is session
    assert some_context.config is config
    assert some_context.system_control is system_control





class ContextAwareFixtureStub(ContextAwareFixture):
    def new_context(self):
        return ExecutionContext()

    def check_context(self):
        assert ExecutionContext.get_context() is self.context

    @set_up
    def setup_marked_method(self):
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

    def del_thing(self, thing):
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
    
