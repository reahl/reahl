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



from reahl.stubble import EmptyStub
from reahl.tofu import Fixture, scenario, with_fixtures, set_up, tear_down
from reahl.component.context import ExecutionContext

class ContextImplementationFixture(Fixture):

    @set_up
    def record_original_implementation_setting(self):
        self.original_use_context_var = ExecutionContext.use_context_var

    @tear_down
    def restore_original_implementation_setting(self):
        ExecutionContext.use_context_var = self.original_use_context_var

    @scenario
    def use_frames(self):
        ExecutionContext.use_context_var = False

    @scenario
    def use_contextvars(self):
        ExecutionContext.use_context_var = True


@with_fixtures(ContextImplementationFixture)
def test_execution_context_basics(context_implementation_fixture):
    """An ExecutionContext is like a global variable for a particular call stack. To create an
       ExecutionContext for a call stack, use it in a with statement."""

    def do_something():
        return ExecutionContext.get_context()
    def do_high_level_something():
        return do_something()

    with ExecutionContext() as some_context:

        found_context = do_high_level_something()

        assert found_context is some_context


@with_fixtures(ContextImplementationFixture)
def test_execution_context_stacking(context_implementation_fixture):
    """When an ExecutionContext overrides a deeper one on the call stack, it will retain the same id."""
    with ExecutionContext() as some_context:

        def deeper_code():
            with ExecutionContext() as deeper_context:
                assert ExecutionContext.get_context_id() == some_context.id
                return deeper_context

        deeper_context = deeper_code()
        assert some_context is not deeper_context
        assert some_context.id == deeper_context.id


@with_fixtures(ContextImplementationFixture)
def test_contents(context_implementation_fixture):
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



