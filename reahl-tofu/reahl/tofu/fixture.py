# Copyright 2013-2021 Reahl Software Services (Pty) Ltd. All rights reserved.
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


import sys
import inspect
import types
import atexit
import contextlib
from collections import OrderedDict 


from reahl.component.exceptions import ProgrammerError



#--------------------------------------------------[ MarkingDecorator ]
class MarkingDecorator:
    """A MarkingDecorator is a decorator used to tag methods on a Fixture.

    """
    def __init__(self, function):
        self.function = function
        self.fixture_class = None

    def bind_class(self, fixture_class):
        self.fixture_class = fixture_class
        
    def __get__(self, instance, owner):
        self.bind_class(owner)
        if instance is None:
            return self
        else:
            return types.MethodType(self.function, instance)

    @property
    def name(self):
        return self.function.__name__

    def method_for(self, fixture):
        return getattr(fixture, self.name)


#--------------------------------------------------[ Scenario ]
class Scenario(MarkingDecorator):
    """A Scenario is a variation on a :class:`Fixture`.

       A Scenario is defined as a Fixture method which is decorated
       with @scenario.  The Scenario method is run after setup of the
       Fixture, to provide some extra setup pertaining to that
       scenario only.

       When a Fixture that contains more than one scenario is used
       with :py:func:`with_fixtures`, the test will be run once for
       every Scenario defined on the Fixture. Before each run of the
       Fixture, a new Fixture instance is set up, and only the current
       scenario method is called to provide the needed variation on
       the Fixture.

    """
    def get_scenarios(self):
        return [self]

    def for_scenario(self, scenario, *args):
        instance = self.fixture_class(*args)
        instance.set_scenario(scenario)
        return instance

    @property
    def _options(self):
        return self.fixture_class._options

    
class DefaultScenario(Scenario):
    def __init__(self):
        super().__init__(None)
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




class FixtureOptions:
    def __init__(self):
        self.dependencies = {}
        self.scope = 'function'

    
class Fixture:
    """A test Fixture is a collection of objects defined and set up to be
       used together in a test. 

       A Fixture can be used by many tests and also by other Fixtures.


       To create your own Fixture, create a subclasses of Fixture.
       On such a subclass, a new member of the Fixture is defined by a specially
       named method that is able to create the object.
       
       The name of such a 'factory method' is `new_` with the name of the object
       appended.

       .. code-block:: python

          class MyFixture(Fixture):
              def new_name(self):
                  return 'myname'

       A Fixture is used inside a with statement or as using a plugin for a test
       framework.

       A member of the Fixture can be accessed by referencing it by
       name on the fixture as if it were an attribute.

       The first time a program references a member on the Fixture
       instance, the corresponding `new_` method will be called behind
       the scenes (without arguments) to create the object. Subsequent
       accesses of the same member will always bring back the same
       instance which was created on the first access.

       .. code-block:: python

          with MyFixture() as fixture:
               assert fixture.name is fixture.name

       If the created singleton object also needs to be torn down, the new\_ method
       should yield it (not return), and perform necessary tear down after the yield
       statement.

       Singletons are torn down using this mechanism in reverse order
       of how they were created. (The last one created is torn down
       first.) Singleton instances are also torn down before any other
       tear down logic happens (because, presumably the instances are
       all created after all other setup occurs).

       A Fixture instance can be used as a context manager. It is set up before 
       entering the block of code it manages, and torn down upon exiting it.

       .. versionchanged:: 3.2
          Added support for `del_` methods.

       .. versionchanged:: 4.0 
          Changed to work with pytest instead of nosetests
          (:py:class:`with_fixtures`, :py:func:`scope`,
          :py:func:`uses`).

       .. versionchanged:: 4.0 
          Removed `.run_fixture` and `.context`.

       .. versionchanged:: 4.0 
          Removed `_del` methods in favour of allowing `new_` methods to yield, then tear down.

    """
    factory_method_prefix = 'new'
    _options = FixtureOptions()
    _setup_done = False

    @classmethod
    def get_scenarios(cls):
        scenarios = [getattr(cls, i) for i in dir(cls) if isinstance(getattr(cls, i), Scenario)]
        return scenarios or [DefaultScenario()]

    @classmethod
    def create_with_scenario(cls, scenario, *args):
        instance = cls(*args)
        instance.set_scenario(scenario)
        return instance

    @classmethod
    def for_scenario(cls, scenario, *args):
        assert cls._options.scope in ['function', 'session']
        if cls._options.scope == 'function':
            return cls.create_with_scenario(scenario, *args)

        if not hasattr(cls, '_session_instances'):
            cls._session_instances = {}
            cls._session_setup_done = {}
        try:
            instance = cls._session_instances[scenario.name]
        except KeyError:
            instance = cls._session_instances[scenario.name] = cls.create_with_scenario(scenario, *args)

        return instance


    def __init__(self):
        self.attributes_set = OrderedDict()
        self.scenario = DefaultScenario()
        self.attribute_generators = []

    def set_scenario(self, scenario):
        self.scenario = scenario

    def setup_dependencies(self, all_fixtures):
        self.dependencies = []
        dependencies_by_class = {v: k for k, v in self._options.dependencies.items()}
        for fixture in all_fixtures:
            if fixture.__class__ in dependencies_by_class:
                setattr(self, dependencies_by_class[fixture.__class__], fixture)
                self.dependencies.append(fixture)
        
    def tear_down_attributes(self):
        for generator in reversed(self.attribute_generators):
            try:
                next(generator)
            except StopIteration:
                pass
            else:
                name = generator.__qualname__ 
                raise ProgrammerError('%s is yielding more than one element. \'new_\' methods should only yield a single element' % name)

    def clear(self):
        """Clears all existing singleton objects"""
        self.tear_down_attributes()
        for name in self.attributes_set.keys():
            delattr(self, name)
        self.attributes_set = OrderedDict()
        self.attribute_generators = []

    @contextlib.contextmanager
    def wrapped_attribute_error(self):
        try:
            yield
        except AttributeError as ex:
            raise AttributeErrorInFactoryMethod(ex).with_traceback(sys.exc_info()[2])
        
    def __getattr__(self, name):
        try:
            getattr(self.__class__, '%s_%s' % (self.factory_method_prefix, name))
        except AttributeError:
            raise AttributeError(name)

        factory = self.get_factory_method_for(name)
        if inspect.isgeneratorfunction(factory):
            with self.wrapped_attribute_error():
                generator = factory()
                instance = next(generator)
            self.attribute_generators.append(generator)
        else:
            with self.wrapped_attribute_error():
                instance = factory()
            
        setattr(self, name, instance)
        self.attributes_set[name] = instance
        return instance

    def get_marked_methods(self, cls, marker):
        return [value for name, value in cls.__dict__.items() if isinstance(value, marker)]

    def run_marked_methods(self, marker_type, order=lambda x: x ):
        done = {None}
        for cls in order(self.__class__.mro()):
            for marked in self.get_marked_methods(cls, marker_type):
                if marked.name not in done:
                    marked.method_for(self)()
                    done.add(marked.name)

    def do_nothing(self):  # Used when no scenarios are defined
        pass
        
    def set_up(self): pass
    def tear_down(self): pass    

    def get_factory_method_for(self, name):
        return self.get_prefixed_method_for(name, 'new')

    def get_prefixed_method_for(self, name, prefix):
        method_name = '%s_%s' % (prefix, name)
        return getattr(self, method_name)

    def __repr__(self):
        return '%s[%s]' % (self.__class__.__name__, self.scenario.name)

    def __enter__(self):
        if self._setup_done:
            return
        self._setup_done = True

        if self._options.scope == 'session':
            atexit.register(self.run_tear_down_actions)

        try:
            self.set_up()
            self.run_marked_methods(SetUp, order=reversed)
            self.scenario.method_for(self)()
        except:
            self.__exit__(*sys.exc_info())
            raise
        return self

    def __exit__(self, exception_type, value, traceback):
        if self._options.scope == 'function':
            return self.run_tear_down_actions()

    def run_tear_down_actions(self):
        self.tear_down_attributes()
        self.run_marked_methods(TearDown)
        self.tear_down()
