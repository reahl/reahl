import inspect
import itertools
import contextlib

import wrapt
try:
    import pytest
except ImportError:
    pass
import six

from reahl.tofu.fixture import Scenario


class NoDependencyPathFound(Exception):
    def __init__(self, from_vertex, to_vertex):
        self.from_vertex = from_vertex
        self.to_vertex = to_vertex

    def str(self):
        return 'No dependency path found from %s to %s' % (self.from_vertex, self.to_vertex)


class CircularDependencyDetected(Exception):
    def __init__(self, cycle):
        self.cycle = cycle

    def __str__(self):
        return ' -> '.join([str(i) for i in self.cycle])



class DependencyGraph(object):
    @classmethod
    def from_vertices(cls, vertices, find_dependencies):
        graph = {}
        def add_to_graph(v, graph):
            dependencies = graph[v] = find_dependencies(v)
            for dep in dependencies:
                if dep not in graph:
                    add_to_graph(dep, graph)

        for v in vertices:
            add_to_graph(v, graph)

        return cls(graph)

    def __init__(self, graph):
        self.graph = graph
        self.discovered = {}
        self.entered = {}
        self.exited = {}
        self.count = 0
        self.topological_order = []
        self.parents = {}

    def path(self, from_vertex, to_vertex):
        path = []
        i = to_vertex
        path.append(i)
        while i in self.parents and i is not from_vertex:
            i = self.parents[i]
            path.append(i)
        if i is not from_vertex:
            raise NoDependencyPathFound(from_vertex, to_vertex)
        path.reverse()
        return path

    def search(self, from_vertex):
        self.discovered[from_vertex] = True
        self.entered[from_vertex] = self.count
        self.count += 1
        for i in self.graph[from_vertex]:
            if i not in self.discovered:
                self.parents[i] = from_vertex
                self.search(i)
            elif self.entered[i] < self.entered[from_vertex] and i not in self.exited:
                raise CircularDependencyDetected(self.path(i, from_vertex)+[i])
            elif i not in self.parents:
                self.parents[i] = from_vertex

        self.exited[from_vertex] = self.count
        self.count += 1
        self.topological_order.append(from_vertex)

    def topological_sort(self):
        for i in self.graph.keys():
            if i not in self.discovered:
                self.search(i)
        return reversed(self.topological_order)



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
                with contextlib.nested(*list(dependency_ordered_fixtures)):
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
        if six.PY2:
            arg_spec = inspect.getargspec(f)
            return arg_spec.args[:len(self.requested_fixtures)]
        else:
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
        if six.PY2:
            current_scenarios = self.permutations.next()
        else:
            current_scenarios = self.permutations.__next__()

        instances = [f.for_scenario(current_scenarios[self.dependency_ordered_classes.index(f)]) for f in self.dependency_ordered_classes]
        for instance in instances:
            instance.setup_dependencies(instances)
        if self.number_args > 1:
            return with_fixtures.instances_in_fixture_order(self.fixture_classes, instances)
        else:
            return with_fixtures.instances_in_fixture_order(self.fixture_classes, instances)[0]
        
    next = __next__
            
    def topological_sort(self, fixture_classes):
        def find_dependencies(fixture_class):
            return fixture_class._options.dependencies.values()
        dependency_graph = DependencyGraph.from_vertices(fixture_classes, find_dependencies)
        return list(dependency_graph.topological_sort())

