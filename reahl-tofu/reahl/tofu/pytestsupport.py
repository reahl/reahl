# Copyright 2017-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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

import inspect
import itertools
import contextlib
import copy

import wrapt
try:
    import pytest
except ImportError:
    pass

from reahl.tofu.fixture import Scenario
from reahl.component.eggs import DependencyGraph


def uses(**fixture_classes):
    """A decorator for making one :py:class:`Fixture` use others.

    The following will result in an instance of FixtureClass1 being instantiated
    every time a MyFixture is created. This instance will be available
    in MyFixture as its `.name1` attribute::

       @uses(name1=OtherFixture)
       class MyFixture(Fixture):
           def some_method(self):
               assert isinstance(self.name1, OtherFixture)

    .. versionadded:: 4.0 

    """
    def catcher(f):
        f._options = copy.copy(f._options)
        f._options.dependencies = fixture_classes
        return f
    return catcher

def scope(scope):
    """A decorator for setting the scope of a :py:class:`Fixture`.

    By default, all :py:class:`Fixture`\s are in 'function' scope,
    meaning they are created, set up, and torn down around each test
    function run. With `@scope` this default can be changed to
    'session' scope. A session scoped :py:class:`Fixture` is created
    and set up the first time it is entered as context manager, and
    torn down only once: when the test process exits.

    If the :py:class:`Fixture` contains multiple scenarios, a session
    scoped instance is created and set up for each scenario.

    .. code-block:: python

       @scope('session')
       class MyFixture(Fixture):
           pass

    .. versionadded:: 4.0 

    """
    def catcher(f):
        f._options = copy.copy(f._options)
        f._options.scope = scope
        return f
    return catcher


class WithFixtureDecorator:
    """A decorator for injecting :py:class:`Fixture`\s into pytest test method arguments.

    This decorator takes a list of :py:class:`Fixture` classes as
    arguments and ensures that the first declared positional arguments
    of the `test_` function it decorates will be populated with
    instances of the corresponding :py:class:`Fixture` classes when
    the test is run.

    The names of these positional arguments do not matter.

    If a :py:class:`Fixture` in this list has scenarios, the test
    function will be run repeatedly--once for each scenario. If more than
    one :py:class:`Fixture` in this list has scenarios, the `test_`
    function will be repeated once for each combination of scenarios.

    For example::

       class MyFixture(Fixture):
           def new_string(self):
               return 'this is a test'

       @with_fixture(MyFixture)
       def test_this(my_fix)
           assert my_fix.string == 'this is a test'

    The use of :py:class:`Fixture` classes can me mixed with
    pytest.fixture functions. In such a case, the :py:class:`Fixture`
    instances are passed to the first declared positional arguments of
    the test function, leaving the remainder of the arguments to be
    interpreted by pytest itself::

       class MyFixture(Fixture):
           def new_string(self):
               return 'this is a test'

       class MyOtherFixture(Fixture):
           def new_int(self):
               return 123

       @pytest.fixture
       def another_string():
           return 'another'

       @with_fixture(MyFixture, MyOtherFixture)
       def test_this(my_fix, other, another_string)
           assert my_fix.string == 'this is a test'
           assert other.int == 123
           assert another_string == 'another'

    .. versionadded:: 4.0 
    """
    def __init__(self, *fixture_classes):
        self.requested_fixtures = fixture_classes
        self.fixture_classes = [(i.fixture_class if isinstance(i, Scenario) else i) for i in fixture_classes]

    def __call__(self, f):
        @wrapt.decorator
        def test_with_fixtures(wrapped, instance, args, kwargs):
            fixture_instances = [i for i in list(args) + list(kwargs.values())
                                     if i.__class__ in self.fixture_classes or i.scenario in self.requested_fixtures]
            dependency_ordered_fixtures = self.topological_sort_instances(fixture_instances)

            with contextlib.ExitStack() as stack:
                for fixture in dependency_ordered_fixtures:
                    stack.enter_context(fixture)
                return wrapped(*args, **kwargs)

        ff = test_with_fixtures(f)
        arg_names = self.fixture_arg_names(ff)
        return pytest.mark.parametrize(','.join(arg_names), self.fixture_permutations())(ff)

    def instances_in_fixture_order(self, instances):
        fixture_instances = {i.__class__: i for i in instances if i.__class__ in self.fixture_classes}
        return [fixture_instances[c] for c in self.fixture_classes]
        
    def fixture_arg_names(self, f):
        signature = inspect.signature(f)
        return list(signature.parameters.keys())[:len(self.requested_fixtures)]

    def topological_sort_instances(self, fixture_instances):
        def find_dependencies(fixture_instance):
            return fixture_instance.dependencies
        dependency_graph = DependencyGraph.from_vertices(fixture_instances, find_dependencies)
        return reversed(list(dependency_graph.topological_sort()))

    def topological_sort_classes(self, fixture_classes):
        def find_dependencies(fixture_class):
            return fixture_class._options.dependencies.values()
        dependency_graph = DependencyGraph.from_vertices(fixture_classes, find_dependencies)
        return list(dependency_graph.topological_sort())

    def fixture_permutations(self):
        dependency_ordered_classes = self.topological_sort_classes(self.requested_fixtures)
        permutations = itertools.product(*([c.get_scenarios() for c in dependency_ordered_classes]))

        for current_scenarios in permutations:
            instances = [f.for_scenario(current_scenarios[dependency_ordered_classes.index(f)]) for f in dependency_ordered_classes]
            for instance in instances:
                instance.setup_dependencies(instances)
            ordered_instances = self.instances_in_fixture_order(instances)
            yield (ordered_instances if len(self.requested_fixtures) > 1 else ordered_instances[0])


with_fixtures = WithFixtureDecorator

