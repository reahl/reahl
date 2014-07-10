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


from __future__ import unicode_literals
from __future__ import print_function
from nose.tools import istest
from reahl.tofu import  test, Fixture
from reahl.tofu import vassert

from reahl.component.context import ExecutionContext
from reahl.stubble import EmptyStub

@istest
class ContextTests(object):
    @test(Fixture)
    def execution_context_basics(self, fixture):
        """An ExecutionContext is like a global variable for a particular call stack. To create an
           ExecutionContext for a call stack, use it in a with statement."""

        def do_something():
            fixture.found_context = ExecutionContext.get_context()
        def do_high_level_something():
            do_something()
            
        fixture.found_context = None
        some_context = ExecutionContext()
        with some_context:
            do_high_level_something()

        vassert( fixture.found_context is some_context )
        
    @test(Fixture)
    def execution_context_stacking(self, fixture):
        """When an ExecutionContext overrides a deeper one on the call stack, it will retain the same id."""
        some_context = ExecutionContext()

        vassert( some_context is not fixture.context )
        vassert( some_context.id == fixture.context.id )

        with some_context:
            vassert( ExecutionContext.get_context_id() == some_context.id )

    @test(Fixture)
    def contents(self, fixture):
        """A Session, Config or SystemControl may be set on the ExecutionContext."""
        some_context = ExecutionContext()

        session = EmptyStub()
        config = EmptyStub()
        system_control = EmptyStub()

        some_context.set_session( session )
        some_context.set_config( config )
        some_context.set_system_control( system_control )

        vassert( some_context.session is session )
        vassert( some_context.config is config )
        vassert( some_context.system_control is system_control )




