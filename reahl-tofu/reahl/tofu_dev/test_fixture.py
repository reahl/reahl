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




from reahl.tofu import Fixture, set_up, tear_down


#--------------------------------------------------[ FixtureTests ]

class FixtureTests:
    __test__ = True

    def test_automaticsingletons(self):
        class Stub: pass
        
        class TestFixture(Fixture):
            def new_thing(self, a=None):
                return a or Stub()

        fixture = TestFixture()

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


    def test_automaticsingletons_tear_down(self):
        """If a new_ method for a singleton yields a value (instead of returning one) the singleton can be torn down
           after the yield statement in the new_ method. Tairing down such singletons happens in reverse order
           of singletons being created (ie, last created is first to be torn down)."""
        class Stub: pass

        torn_down_things = []

        class TestFixture(Fixture):
            def new_thing_last_accessed(self):
                thing = Stub()
                yield thing
                thing.torn_down = True
                torn_down_things.append(thing)

            def new_thing_first_accessed(self):
                thing = Stub()
                yield thing
                thing.torn_down = True
                torn_down_things.append(thing)

        with TestFixture() as fixture:
            fixture.thing_first_accessed.torn_down = False
            fixture.thing_last_accessed.torn_down = False

        assert fixture.thing_first_accessed.torn_down
        assert fixture.thing_last_accessed.torn_down
        assert torn_down_things == [fixture.thing_last_accessed, fixture.thing_first_accessed]


    def test_automaticsingletons_inherited(self):
        class Parent(Fixture):
            def new_thing(self, a=1):
                return a

        class TestFixture(Parent):
            pass
        
        fixture = TestFixture()

        assert fixture.thing == 1


    def test_automaticsingletons_overridden(self):
        class Parent(Fixture):
            def new_thing(self, a=1):
                return a

        class TestFixture(Parent):
            def new_thing(self, a=2):
                return a
        
        fixture = TestFixture()

        assert fixture.thing == 2


    def test_automaticsingletons_from_mixin(self):
        class Mixin:
            def new_thing(self, a=1):
                return a

        class TestFixture(Fixture, Mixin):
            pass
        
        fixture = TestFixture()

        assert fixture.thing == 1


    def test_fixture_as_context_manager(self):
        """The Fixture is set_up and torn_down when used in a with statement."""
        class MyFixture(Fixture):
            is_set_up = False
            is_torn_down = False
            def set_up(self):
                self.is_set_up = True
            def tear_down(self):
                self.is_torn_down = True
         
        with MyFixture() as fixture:
            assert fixture.is_set_up
            assert not fixture.is_torn_down
        
        assert fixture.is_torn_down
         

    def test_setup_breakages_as_context_manager(self):
        """Breakage in the setup triggers tear down to be run when a fixture is used in a with statement."""
        class MyFixture(Fixture):
            is_torn_down = False
            def set_up(self):
                raise Exception()
            def tear_down(self):
                self.is_torn_down = True

        fixture = MyFixture()
        try:
            with fixture as fixture:
                pass
        except:
            pass
        else:
            assert None, 'No exception raised'
        
        assert fixture.is_torn_down

         

    def test_default_set_up_and_tear_down(self):
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
         
        with MyFixture() as fixture:
            assert fixture.is_set_up
            assert not fixture.is_torn_down
        
        assert fixture.is_torn_down


    def test_overriding_marked_methods(self):
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

        with MyDerivedFixture() as fixture:
            assert not fixture.is_set_up
            assert fixture.derived_is_set_up
        

        
