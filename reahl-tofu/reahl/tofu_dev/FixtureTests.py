# Copyright 2006, 2009, 2011, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.tofu import Fixture, set_up, tear_down

from reahl.tofu.fixture import NoContext

#--------------------------------------------------[ FixtureTests ]
@istest
class FixtureTests(object):
    @istest
    def test_construction(self):
        run_fixture = Fixture(None)
        assert run_fixture.run_fixture == None
        assert isinstance(run_fixture.context, NoContext)
        
        test_fixture = Fixture(run_fixture)
        assert test_fixture.run_fixture is run_fixture
        assert test_fixture.context is run_fixture.context
        
    @istest
    def test_automaticsingletons(self):
        class Stub(object): pass
        
        class TestFixture(Fixture):
            def new_thing(self, a=None):
                return a or Stub()

        fixture = TestFixture(None)

        assert fixture.thing is not None
        assert fixture.thing is fixture.thing # It is a singleton

        thing = fixture.thing
        fixture.clear()

        assert thing is not fixture.thing # After .clear() new instances are made

        fixture.thing = 2
        assert fixture.thing == 2
        
        try:
            fixture.non_existing_thing
            assert None, 'AttributeError not raised'
        except AttributeError:
            pass

        assert fixture.new_thing(a=123) == 123

    @istest
    def test_overriding_automatic_context(self):
        class TestFixture(Fixture):
            def new_context(self):
                return 123

        fixture = TestFixture(None)

        assert fixture.context is 123

    @istest
    def test_automaticsingletons_inherited(self):
        class Parent(Fixture):
            def new_thing(self, a=1):
                return a

        class TestFixture(Parent):
            pass
        
        fixture = TestFixture(None)

        assert fixture.thing == 1

    @istest
    def test_automaticsingletons_overridden(self):
        class Parent(Fixture):
            def new_thing(self, a=1):
                return a

        class TestFixture(Parent):
            def new_thing(self, a=2):
                return a
        
        fixture = TestFixture(None)

        assert fixture.thing == 2

    @istest
    def test_automaticsingletons_from_mixin(self):
        class Mixin(object):
            def new_thing(self, a=1):
                return a

        class TestFixture(Fixture, Mixin):
            pass
        
        fixture = TestFixture(None)

        assert fixture.thing == 1

    @istest
    def test_context_from_mixin(self):
        class ContextStub(object):
            def __enter__(self): pass
            def __exit__(self): pass
            
        class Mixin(object):
            def new_context(self, a=1):
                return ContextStub()

        class TestFixture(Fixture, Mixin):
            pass
        
        fixture = TestFixture(None)

        assert isinstance(fixture.context, ContextStub)

    @istest
    def fixture_as_context_manager(self):
        """The Fixture is set_up and torn_down when used in a with statement."""
        class MyFixture(Fixture):
            is_set_up = False
            is_torn_down = False
            def set_up(self):
                self.is_set_up = True
            def tear_down(self):
                self.is_torn_down = True
         
        with MyFixture(None) as fixture:
            assert fixture.is_set_up
            assert not fixture.is_torn_down
        
        assert fixture.is_torn_down
         
    @istest
    def default_set_up_and_tear_down(self):
        """The default set_up and tear_down run marked methods."""
        class MyFixture(Fixture):
            is_set_up = False
            is_torn_down = False
            @set_up
            def my_set_up(self):
                self.is_set_up = True
            @tear_down
            def my_tear_down(self):
                self.is_torn_down = True
         
        with MyFixture(None) as fixture:
            assert fixture.is_set_up
            assert not fixture.is_torn_down
        
        assert fixture.is_torn_down

    @istest
    def overriding_marked_methods(self):
        """Marked methods can be overridden."""
        class MyFixture(Fixture):
            is_set_up = False
            @set_up
            def my_set_up(self):
                self.is_set_up = True

        class MyDerivedFixture(MyFixture):
            derived_is_set_up = False
            @set_up
            def my_set_up(self):
                self.derived_is_set_up = True

        with MyDerivedFixture(None) as fixture:
            assert not fixture.is_set_up
            assert fixture.derived_is_set_up
        

        
