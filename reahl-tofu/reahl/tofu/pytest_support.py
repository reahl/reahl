import inspect
import itertools
import contextlib

import wrapt
try:
    import pytest
except ImportError:
    pass
import six

from reahl.component.eggs import DependencyGraph
from reahl.tofu.fixture import Scenario

class WithFixtureDecorator(object):
    def __init__(self, *fixture_classes):
        self.requested_fixtures = fixture_classes
        self.fixture_classes = [(i.fixture_class if isinstance(i, Scenario) else i) for i in fixture_classes]

    def __call__(self, f):
        @wrapt.decorator
        def the_test(wrapped, instance, args, kwargs):
            fixture_instances = [i for i in list(args) + list(kwargs.values())
                                     if i.__class__ in self.fixture_classes or i.scenario in self.requested_fixtures]
            dependency_ordered_fixtures = self.topological_sort(fixture_instances)

            if six.PY2:
                with contextlib.nested(dependency_ordered_fixtures):
                    return wrapped(*args, **kwargs)
            else:
                with contextlib.ExitStack() as stack:
                    for fixture in dependency_ordered_fixtures:
                        stack.enter_context(fixture)
                    return wrapped(*args, **kwargs)

        ff = the_test(f)
        arg_names = self.fixture_arg_names(ff)
        return pytest.mark.parametrize(','.join(arg_names), self.fixture_permutations(len(arg_names)))(ff)

    @classmethod
    def instances_in_fixture_order(self, fixture_classes, instances):
        fixture_instances = {i.__class__: i for i in instances if i.__class__ in fixture_classes}
        return [fixture_instances[c] for c in fixture_classes]
        
    def fixture_arg_names(self, f):
        signature = inspect.signature(f)
        return list(signature.parameters.keys())[:len(self.requested_fixtures)]

    def fixture_permutations(self, number_args):
        return FixturePermutationIterator(self.requested_fixtures, self.fixture_classes, number_args)

    def topological_sort(self, fixture_instances):
        def find_dependencies(fixture_instance):
            return fixture_instance.dependencies
        dependency_graph = DependencyGraph.from_vertices(fixture_instances, find_dependencies)
        return reversed(list(dependency_graph.topological_sort()))

with_fixtures = WithFixtureDecorator
    
class FixturePermutationIterator(object):
    def __init__(self, requested_fixtures, fixture_classes, number_args):
        self.fixture_classes = fixture_classes
        self.dependency_ordered_classes = self.topological_sort(requested_fixtures)
        self.number_args = number_args
        self.permutations = itertools.product(*([c.get_scenarios() for c in self.dependency_ordered_classes]))

    def __iter__(self):
        return self
    
    def __next__(self):
        current_scenarios = self.permutations.__next__()
        instances = [f.for_scenario(current_scenarios[self.dependency_ordered_classes.index(f)]) for f in self.dependency_ordered_classes]
        for instance in instances:
            instance.setup_dependencies(instances)
        if self.number_args > 1:
            return with_fixtures.instances_in_fixture_order(self.fixture_classes, instances)
        else:
            return with_fixtures.instances_in_fixture_order(self.fixture_classes, instances)[0]
            
    def topological_sort(self, fixture_classes):
        def find_dependencies(fixture_class):
            return fixture_class._options.dependencies.values()
        dependency_graph = DependencyGraph.from_vertices(fixture_classes, find_dependencies)
        return list(dependency_graph.topological_sort())

