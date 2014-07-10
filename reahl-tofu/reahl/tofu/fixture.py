# Copyright 2006, 2009-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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
import six
import sys
import new

#--------------------------------------------------[ MarkingDecorator ]
class MarkingDecorator(object):
    """A MarkingDecorator is a decorator used to tag methods on a Fixture.

    """
    def __init__(self, function):
        self.function = function
        self.fixture_class = None

    def bind_class(self, fixture_class):
        self.fixture_class = fixture_class
        
    def __get__(self, instance, owner):
        self.bind_class(owner)
        if not instance:
            return self
#        return functools.wraps(self.function)(new.instancemethod(self.function, instance, owner))
        return new.instancemethod(self.function, instance, owner)

    @property
    def name(self):
        return self.function.__name__

    def method_for(self, fixture):
        return getattr(fixture, self.name)


#--------------------------------------------------[ Scenario ]
class Scenario(MarkingDecorator):
    """A Scenario is a variation on a :class:`Fixture`.

       A Scenario is defined as a Fixture method which is decorated with @scenario.
       The Scenario method is run after setup of the Fixture, to provide some extra
       setup pertaining to that scenario only.

       When a Fixture that contains more than one scenario is used with nosetests, 
       the test will be run once for every Scenario defined on the Fixture. Before
       each run of the Fixture, a new Fixture instance is set up, and only the current
       scenario method is called to provide the needed variation on the Fixture.
    """
    def get_scenarios(self):
        return [self]

    def for_scenario(self, run_fixture, scenario):
        return self.fixture_class(run_fixture, scenario)

    
class DefaultScenario(Scenario):
    def __init__(self):
        super(DefaultScenario, self).__init__(None)
    @property
    def name(self):
        return 'default_scenario'
    def method_for(self, fixture):
        return fixture.do_nothing

    
#--------------------------------------------------[ SetUp ]
class SetUp(MarkingDecorator):
    """Methods on a Fixture marked as @set_up are run when the Fixture is set up."""


#--------------------------------------------------[ TearDown ]
class TearDown(MarkingDecorator):
    """Methods on a Fixture marked as @tear_down are run when the Fixture is torn down."""


#--------------------------------------------------[ Fixture ]
class AttributeErrorInFactoryMethod(Exception):
    pass


class Fixture(object):
    """A test Fixture is a collection of objects defined and set up to be
       used together in a test.

       Programmers should extend this class by creating subclasses of Fixture.
       On such a subclass, a new member of the Fixture is defined by a specially
       named method that is able to create the object.
       
       The name of such a 'factory method' is `new_` with the name of the object
       appended.

       When an object is referenced by name on the fixture, the corresponding 
       `new_` method is called, and the resulting object cached as a singleton for
       future accesses.

       A Fixture instance can be used as a context manager. It is set up before 
       entering the block of code it manages, and torn down upon exiting it.

       A Fixture has a default :class:`reahl.component.context.ExecutionContext` 
       instance available as its `.context` attribute, which can be overridden
       by creating a method named `new_context` on a subclass.
    """
    factory_method_prefix = 'new'

    @classmethod
    def get_scenarios(cls):
        scenarios = [getattr(cls, i) for i in dir(cls) if isinstance(getattr(cls, i), Scenario)]
        return scenarios or [DefaultScenario()]

    @classmethod
    def for_scenario(cls, run_fixture, scenario):
        return cls(run_fixture, scenario)
    
    def __init__(self, fixture, scenario=DefaultScenario()):
        self.attributes_set = []
        self.run_fixture = fixture
        self.scenario = scenario

    def clear(self):
        """Clears all existing singleton objects."""
        for name in self.attributes_set:
            delattr(self, name)
        self.attributes_set = []

    def __getattr__(self, name):
        if name.startswith(self.factory_method_prefix):
            raise AttributeError(name)

        factory = self.get_factory_method_for(name)
        
        try:
            instance = factory()
        except AttributeError as ex:
            six.reraise(AttributeErrorInFactoryMethod, AttributeErrorInFactoryMethod(ex), sys.exc_info()[2])
        setattr(self, name, instance)
        self.attributes_set.append(name)
        return instance

    def create_default_context(self):
        if self.run_fixture:
            return self.run_fixture.context
        else:
            return NoContext()
    
    def get_marked_methods(self, cls, marker):
        return [value for name, value in cls.__dict__.items() if isinstance(value, marker)]

    def run_marked_methods(self, marker_type, order=lambda x: x ):
        done = {None}
        for cls in order(self.__class__.mro()):
            for marked in self.get_marked_methods(cls, marker_type):
                if marked.name not in done:
                    marked.method_for(self)()
                    done.add(marked.name)

    def do_nothing(self):  # Used when no scenarions are defined
        pass
        
    def set_up(self): pass
    def tear_down(self): pass    

    def get_factory_method_for(self, name):
        try:
            factory_method_name = '%s_%s' % (self.factory_method_prefix, name)
            return getattr(self, factory_method_name)
        except AttributeError:
            if name == 'context':
                return self.create_default_context
            raise

    def __repr__(self):
        return '%s[%s]' % (self.__class__.__name__, self.scenario.name)

    def __enter__(self):
        with self.context:
            self.set_up()
            self.run_marked_methods(SetUp, order=reversed)
            self.scenario.method_for(self)()
        return self

    def __exit__(self, exception_type, value, traceback):
        with self.context:
            self.run_marked_methods(TearDown)
            self.tear_down()

class NoContext(object):
    def __enter__(self):
        return self

    def __exit__(self, exception_type, value, traceback):
        pass
