# Copyright 2013, 2014, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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
import sys
import inspect
import logging
import copy
import atexit
from collections import OrderedDict 

import six




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
        if instance is None:
            return self
        else:
            return six.create_bound_method(self.function, instance)

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

    def for_scenario(self, scenario, *args):
        instance = self.fixture_class(*args)
        instance.set_scenario(scenario)
        return instance

    @property
    def _options(self):
        return self.fixture_class._options

    
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




class FixtureOptions(object):
    def __init__(self):
        self.dependencies = {}
        self.scope = 'function'

    
def uses(**kwargs):
    def catcher(f):
        f._options = copy.copy(f._options)
        f._options.dependencies = kwargs
        return f
    return catcher

def scope(scope):
    def catcher(f):
        f._options = copy.copy(f._options)
        f._options.scope = scope
        return f
    return catcher


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

       If a corresponding `del_` method exists for a given `new_`
       method, it will be called when the Fixture is torn down. This
       mechanism exists so you can dispose of the singleton created by
       the `new_` method. These `del_` methods are called only for singleton
       instances that were actually created, and in reverse order of creation
       of each instance. Singleton instances are also torn down before any other
       tear down logic happens (because, presumably the instances are all
       created after all other setup occurs).
       

       A Fixture instance can be used as a context manager. It is set up before 
       entering the block of code it manages, and torn down upon exiting it.

       A Fixture instance also has a context manager available as its
       '.context' attribute. Setup, test run and tear down code is run
       within the context of '.context' as well. The default context
       manager does not do anything, but you can supply your own by
       creating a method named `new_context` on a subclass. If no custom
       context is given and the fixture has a run_fixture, the run_fixture.context
       is used.

       .. versionchanged:: 3.2
          Added support for `del_` methods.
       
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
        for name, instance in reversed(list(self.attributes_set.items())):
            self.get_tear_down_method_for(name)(instance)

    def clear(self):
        """Clears all existing singleton objects"""
        self.tear_down_attributes()
        for name in self.attributes_set.keys():
            delattr(self, name)
        self.attributes_set = OrderedDict()

    def __getattr__(self, name):
        if name.startswith(self.factory_method_prefix):
            raise AttributeError(name)

        factory = self.get_factory_method_for(name)
        
        try:
            instance = factory()
        except AttributeError as ex:
            six.reraise(AttributeErrorInFactoryMethod, AttributeErrorInFactoryMethod(ex), sys.exc_info()[2])
        setattr(self, name, instance)
        self.attributes_set[name] = instance
        return instance

    def create_default_context(self):
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

    def do_nothing(self):  # Used when no scenarios are defined
        pass
        
    def set_up(self): pass
    def tear_down(self): pass    

    def get_factory_method_for(self, name):
        try:
            return self.get_prefixed_method_for(name, 'new')
        except AttributeError:
            if name == 'context':
                return self.create_default_context
            raise

    def get_tear_down_method_for(self, name):
        try:
            return self.get_prefixed_method_for(name, 'del')
        except AttributeError:
            return lambda i: None

    def get_prefixed_method_for(self, name, prefix):
        method_name = '%s_%s' % (prefix, name)
        return getattr(self, method_name)

    def __repr__(self):
        return '%s[%s]' % (self.__class__.__name__, self.scenario.name)

    # def __enter__(self):
    #     if self._options.scope == 'function':
    #         return super(Fuxture, self).__enter__()
    #     elif self._options.scope == 'session' and not self.__class__._session_setup_done.get(self.scenario, False):
    #         atexit.register(self.session_cleanup)
    #         try:
    #             return super(Fuxture, self).__enter__()
    #         finally:
    #             self.__class__._session_setup_done[self.scenario] = True

    def __enter__(self):
        if self._setup_done:
            return

        self._setup_done = True
        
        if self._options.scope == 'session':
            atexit.register(self.session_cleanup)

        with self.context:
            try:
                self.set_up()
                self.run_marked_methods(SetUp, order=reversed)
                self.scenario.method_for(self)()
            except:
                self.__exit__(*sys.exc_info())
                raise
            return self

    def session_cleanup(self):
        return self.__exit__(*sys.exc_info(), exit_session=True)

    def __exit__(self, exception_type, value, traceback, exit_session=False):
        if self._options.scope == 'function' or exit_session:
            with self.context:
                self.tear_down_attributes()
                self.run_marked_methods(TearDown)
                self.tear_down()



class NoContext(object):
    def __enter__(self):
        return self

    def __exit__(self, exception_type, value, traceback):
        pass
