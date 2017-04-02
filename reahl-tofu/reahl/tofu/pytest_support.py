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

class with_fixtures(object):
    def __init__(self, *fixture_classes):
        self.fixture_classes = fixture_classes

    def __call__(self, f):
        @wrapt.decorator
        def the_test(wrapped, instance, args, kwargs):
            fixture_instances = [i for i in list(args) + list(kwargs.values())
                                     if i.__class__ in self.fixture_classes]
            fixtures = self.instances_in_fixture_order(self.fixture_classes, fixture_instances)

            if six.PY2:
                with contextlib.nested(fixtures):
                    return wrapped(*args, **kwargs)
            else:
                with contextlib.ExitStack() as stack:
                    for fixture in fixtures:
                        stack.enter_context(fixture)
                    return wrapped(*args, **kwargs)

        ff = the_test(f)
        return pytest.mark.parametrize(self.fixture_arg_names(ff), self.fixture_permutations())(ff)

    @classmethod
    def instances_in_fixture_order(self, fixture_classes, instances):
        fixture_instances = {i.__class__: i for i in instances if i.__class__ in fixture_classes}
        return [fixture_instances[c] for c in fixture_classes]
        
    def fixture_arg_names(self, f):
        signature = inspect.signature(f)
        return ','.join(list(signature.parameters.keys())[:len(self.fixture_classes)])

    def fixture_permutations(self):
        return FixturePermutationIterator(self.fixture_classes)

    
class FixturePermutationIterator(object):
    def __init__(self, fixture_classes):
        self.fixture_classes = fixture_classes
        self.dependency_ordered_classes = self.topological_sort(fixture_classes)
        self.permutations = itertools.product(*([c.get_scenarios() for c in self.dependency_ordered_classes]))

    def __iter__(self):
        return self
    
    def __next__(self):
        current_scenarios = self.permutations.__next__()
        instances = [f.for_scenario(current_scenarios[self.dependency_ordered_classes.index(f)]) for f in self.dependency_ordered_classes]
        for instance in instances:
            instance.setup_dependencies(instances)
        return with_fixtures.instances_in_fixture_order(self.fixture_classes, instances)

    def topological_sort(self, fixture_classes):
        def add_class(fixture_class, graph):
            graph[fixture_class] = fixture_class._options.dependencies.values()
            for dep in fixture_class._options.dependencies.values():
                if dep not in graph:
                    add_class(dep, graph)

        graph = {}
        for fixture_class in fixture_classes:
            add_class(fixture_class, graph)

        graph[None] = fixture_classes
        return list(DependencyGraph(graph).topological_sort())[1:]
