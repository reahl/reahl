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

"""Classes that aid in dealing with Eggs and setting them up."""

import os
import os.path
import logging
import itertools

from pkg_resources import Requirement, get_distribution, iter_entry_points, require, resource_isdir, \
                          resource_listdir, working_set, parse_version

from reahl.component.decorators import memoized
from reahl.component.exceptions import DomainException, ProgrammerError


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

class InvalidDependencySpecification(DomainException):
    def __init__(self, versions, duplicates):
        self.versions = versions
        self.duplicates = duplicates
        detail = ','.join(['%s -> [%s]' % (version, '; '.join([str(i) for i in version.get_dependencies()])) for version in versions if version.get_dependencies()])
        super().__init__(message='Dependencies result in installing more than one version of: %s. Dependencies: %s' % (','.join(duplicates), detail))


class DependencyGraph:
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
        self.clear_state()

    def clear_state(self):
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
        while i in self.parents and i != from_vertex:
            i = self.parents[i]
            path.append(i)
        if i != from_vertex:
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
        self.clear_state()
        for i in self.graph.keys():
            if i not in self.discovered:
                self.search(i)
        return reversed(self.topological_order)

    def find_components(self):
        components = {}
        all_dependencies = set(itertools.chain(*self.graph.values()))
        for vertex in self.graph.keys():
            if vertex not in all_dependencies:
                new_component_contents = self.get_all_reachable_from(vertex)
                found = False
                done = False
                component_iterator = iter(components.items())
                while not found and not done:
                    try:
                        existing_component, existing_contents = next(component_iterator)
                    except StopIteration:
                        done = True
                    else:
                        new_component_contents_set = set(new_component_contents)
                        existing_component_contents_set = set(existing_contents)
                        if new_component_contents_set & existing_component_contents_set:
                            existing_contents.extend(new_component_contents_set - existing_component_contents_set)
                            found = True
                if not found:
                    components[vertex] = new_component_contents
        return list(components.items())

    def get_all_reachable_from(self, vertex):
        self.clear_state()
        self.search(vertex)
        return self.topological_order

    def render(self, filename, render_format='svg'):
        try:
            from graphviz import Digraph
        except ImportError:
            raise DomainException(message='To use this, you have to install graphviz (pip install graphviz)')
        else:
            graph = Digraph()
            for node in self.graph.keys():
                graph.node(str(node))
            for node, deps in self.graph.items():
                for dep in deps:
                    graph.edge(str(node), str(dep))
            graph.render(filename, cleanup=True, format=render_format)


class DependencyCluster:
    def __init__(self, cluster_root, versions):
        duplicates = []
        for i in range(len(versions)):
            current_version = versions[i]
            if any([current_version.name == other_version.name for other_version in versions[i+1:]]):
                 duplicates.append(current_version.name)
        if duplicates:
            raise InvalidDependencySpecification(versions, duplicates)

        self.root = cluster_root
        self.versions = versions
        self.visited = False

    def is_dependent_on(self, other):
        deps = []
        for e in self.versions:
            for other_e in other.versions:
                if other_e.is_previous_version_of(e):
                    deps.append((e, other_e))
        return bool(deps)

    def get_dependencies(self, all_clusters):
        return [other for other in all_clusters if self.is_dependent_on(other)]

    def get_versions_biggest_first(self):
        def version_dependencies(version):
            return [v for v in self.versions
                    if any([d.name == v.name for d in v.get_dependencies()])]
        version_graph = DependencyGraph.from_vertices(self.versions, version_dependencies)
        versions_biggest_first = version_graph.topological_sort()
        return versions_biggest_first

    def __str__(self):
        return str(self.root)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self)


class Dependency(object):
    """
        entry point : name = module.attrs [extras]
    """
    def __init__(self, for_version, entry_point_spec):
        self.for_version = for_version
        self.name = entry_point_spec.name
        self.type = entry_point_spec.module_name
        self.min_version = None
        if self.type == 'egg':
            min_version = '.'.join(entry_point_spec.attrs) if entry_point_spec.attrs else None
            if min_version != '_':
                self.min_version = min_version
        self.max_version = entry_point_spec.extras[0] if entry_point_spec.extras and len(entry_point_spec.extras) > 0 else None

    def get_best_version(self):
        all_versions = self.get_versions()
        matching_versions = sorted([v for v in all_versions
                                    if v.matches_versions(self.min_version, self.max_version)],
                                   key=lambda x: x.version_number)
        return matching_versions[-1]

    def get_versions(self):
        dep_egg = ReahlEgg(self.distribution)
        return dep_egg.get_versions()

    def __repr__(self):
        version_spec = ''
        if self.min_version:
            version_spec += '>= %s' % self.min_version
        if self.max_version:
            if version_spec:
                version_spec += ','
            version_spec += '< %s' % self.max_version

        return '<%s %s %s>' % (self.__class__.__name__, self.name, version_spec)

    @property
    def distribution(self):
        try:
            return get_distribution(self.name)
        except:
            return None


class Version(object):
    def __init__(self, egg, version_number_string):
        self.egg = egg
        self.version_number_string = version_number_string
        as_major_minor = '.'.join(version_number_string.split('.')[:2])
        if not self.version_number.is_prerelease and str(self.version_number) != as_major_minor:
            raise ProgrammerError('Patch version %s specified for %s. You can only register versions of the form major.minor (unless the patch version includes an alpha indicator)' % (self.version_number, egg.project_name))

    @property
    def name(self):
        return self.egg.name

    @property
    def version_number(self):
        return parse_version(self.version_number_string)

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        return '%s[%s]' % (self.egg.name, self.version_number)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self)

    def matches_versions(self, min_version, max_version):
        if not min_version:
            return True
        candidate_version = parse_version(self.version_number_string)
        [major, minor] = min_version.split('.')[:2]
        min_version = parse_version(min_version)
        max_version = parse_version(max_version or '%s.%s.%s' % (major, minor, '9999'))
        return min_version <= candidate_version < max_version

    def get_migration_classes(self):
        return self.egg.get_migration_classes_for_version(self)

    def get_dependencies(self):
        return self.egg.get_dependencies(self.version_number_string)

    def get_previous_version(self):
        # TODO: cater for is_replacement_of in VersionEntry
        previous_versions = [i for i in sorted(self.egg.get_versions(), key=lambda x: x.version_number) if i.version_number < self.version_number]
        return previous_versions[-1] if len(previous_versions) else None

    def is_previous_version_of(self, other):
        if self.egg.name == other.egg.name:
            return other.get_previous_version() == self
        return False

    def is_up_to_date(self, orm_control):
        installed_version_number = parse_version(orm_control.schema_version_for(self.egg, default='0.0'))
        return installed_version_number >= self.version_number


class ReahlEgg:
    interface_cache = {}

    def __init__(self, distribution):
        self.distribution = distribution

    @property
    def name(self):
        return self.distribution.key

    @property
    def installed_version(self):
        latest_declared_version = self.get_versions()[-1]
        installed_version_string = self.distribution.version
        if str(latest_declared_version.version_number) != '.'.join(installed_version_string.split('.')[:2]):
            raise ProgrammerError('Installed version %s of %s, does not match the latest declared version %s'
                                  % (installed_version_string, self.name, latest_declared_version))
        return latest_declared_version

    @property
    def configuration_spec(self):
        entry_point_dict = self.distribution.get_entry_map().get('reahl.configspec', {})
        entry_point = entry_point_dict.get('config', None)
        return entry_point.load() if entry_point else None

    def read_config(self, config):
        if self.configuration_spec:
            config.read(self.configuration_spec)

    def validate_config(self, config):
        if self.configuration_spec:
            config.validate_required(self.configuration_spec)

    def list_config(self, config):
        if self.configuration_spec:
            return config.list_required(self.configuration_spec)
        return []

    def get_versions(self):
        entry_point_dict = self.distribution.get_entry_map().get('reahl.versions', {})
        all_versions = [Version(self, version_string) for version_string in entry_point_dict.keys()]

        return list(sorted([v for v in all_versions], key=lambda x: x.version_number))

    def get_dependencies(self, version):
        entry_point_dict = self.distribution.get_entry_map().get('reahl.versiondeps.%s' % version, {})
        unparsed_dependency_entry_points = entry_point_dict.values()
        return [Dependency(self, ep) for ep in unparsed_dependency_entry_points]

    def get_persisted_classes_in_order(self):
        return self.get_ordered_classes_exported_on('reahl.persistlist')

    def get_migration_classes_for_version(self, version):
        return self.get_ordered_classes_exported_on('reahl.migratelist.%s' % version.version_number)

    def get_ordered_classes_exported_on(self, entry_point):
        entry_point_dict = self.distribution.get_entry_map().get(entry_point, {})
        found_eps = set()
        for ep in entry_point_dict.values():
            if ep in found_eps:
                raise AssertionError('%s is listed twice' % ep)
            found_eps.add(ep)
        return [entry.load() for order, entry in sorted([(int(order), e) for order, e in entry_point_dict.items()])]

    def get_classes_exported_on(self, entry_point):
        entry_point_dict = self.distribution.get_entry_map().get(entry_point, {})
        return [entry.load() for name, entry in entry_point_dict.items()]

    @property
    def translation_package(self):
        entry_point_dict = self.distribution.get_entry_map().get('reahl.translations')
        if entry_point_dict:
            return entry_point_dict[self.name].load()
        else:
            return None

    @property
    def translation_pot_filename(self):
        translations_package_name = self.translation_package.__name__
        translations_file_path = translations_package_name.replace('.', '/')
        return self.distribution.get_resource_filename(self.distribution, '%s/%s' % (translations_file_path, self.name))

    @property
    def scheduled_jobs(self):
        return self.get_classes_exported_on('reahl.scheduled_jobs')
    
    def do_daily_maintenance(self):
        for job in self.scheduled_jobs:
            job()

    @classmethod
    def get_egg_internal_path_for(cls, translations_entry_point):
        module = translations_entry_point.load()
        dir_or_egg_name = translations_entry_point.dist.location.split(os.sep)[-1]
        paths = [p for p in module.__path__ if p.find('%s%s' % (dir_or_egg_name, os.path.sep)) > 0]
        paths = [p for p in paths if not p.startswith(os.path.join(translations_entry_point.dist.location, '.'))]
        unique_paths = [p.split('%s/' % dir_or_egg_name)[-1] for p in paths]
        unique_paths = set([p for p in unique_paths if '.egg' not in p])
        assert len(unique_paths) <= 1, \
            'Only one translations package per component is allowed, found %s for %s' % (paths, translations_entry_point.dist)
        assert len(unique_paths) > 0, \
            'No translations found for %s, did you specify a translations package and forget to add locales in there?' % translations_entry_point.dist
        return unique_paths.pop()

    @memoized
    @classmethod
    def get_languages_supported_by_all(cls, root_egg):
        egg_interfaces = cls.get_all_relevant_interfaces(root_egg)
        default_languages = ['en_gb']
        if not egg_interfaces:
            return default_languages

        domains_in_use = [e.name for e in egg_interfaces]

        languages_for_eggs = {}
        for translation_entry_point in iter_entry_points('reahl.translations'):
            requirement = translation_entry_point.dist.as_requirement()
            egg_internal_path = cls.get_egg_internal_path_for(translation_entry_point)
            if resource_isdir(requirement, egg_internal_path):
                languages = [d for d in resource_listdir(requirement, egg_internal_path)
                             if (resource_isdir(requirement, '%s/%s' % (egg_internal_path, d)) and not d.startswith('__'))]
            else:
                logging.error('Translations of %s not found in %s' % (requirement, egg_internal_path))
                languages = []

            for language in languages:
                language_path = '%s/%s/LC_MESSAGES' % (egg_internal_path, language)
                domains = [d[:-3] for d in resource_listdir(requirement, language_path) if d.endswith('.mo')]
                for domain in domains:
                    if domain in domains_in_use:
                        languages = languages_for_eggs.setdefault(domain, set())
                        languages.add(language)

        if not languages_for_eggs.values():
            return default_languages
        languages = (list(languages_for_eggs.values()))[0].intersection(*languages_for_eggs.values())
        languages.update(default_languages)
        return list(languages)

    @classmethod
    def do_daily_maintenance_for_egg(cls, root_egg):
        eggs_in_order = ReahlEgg.get_all_relevant_interfaces(root_egg)
        for egg in eggs_in_order:
            if isinstance(egg, ReahlEgg):
                egg.do_daily_maintenance()

    @classmethod
    def clear_cache(cls):
        cls.interface_cache.clear()

    @classmethod
    def get_all_relevant_interfaces(cls, main_egg):
        # (We cache the result of this computation, since it is
        #  quite expensive and is called often in the tests.)
        interfaces = cls.interface_cache.get(main_egg, None)
        if interfaces:
            return interfaces
        interfaces = cls.compute_all_relevant_interfaces(main_egg)
        cls.interface_cache[main_egg] = interfaces
        return interfaces

    @classmethod
    def topological_sort(cls, distributions):
        def find_dependencies(dist):
            dependencies = [working_set.find(i) for i in dist.requires()]
            my_requirements =  dist.requires()
            #we want the subset of stuff in the basket we actually depend on, not just the basket itself
            basket_requirements = [i for i in my_requirements
                                   if i.extras]
            for basket in basket_requirements:
                dependencies.extend([working_set.find(Requirement.parse(i)) for i in basket.extras])
            return dependencies
            
        return DependencyGraph.from_vertices(distributions, find_dependencies).topological_sort()


    @classmethod 
    def get_eggs_for(cls, main_egg):
        distributions = require(main_egg)
        return list(set(distributions)) # To get rid of duplicates

    @classmethod
    def compute_ordered_dependent_distributions(cls, main_egg):
        return cls.topological_sort(cls.get_eggs_for(main_egg))
    
    @classmethod
    def compute_all_relevant_interfaces(cls, main_egg):
        interfaces = []

        for i in cls.compute_ordered_dependent_distributions(main_egg):
            interface = cls.interface_for(i)
            if interface:
                interfaces.append(interface)

        return interfaces

    @classmethod
    def interface_for(cls, distribution):
        entry_map = distribution.get_entry_map('reahl.eggs')
        if entry_map:
            classes = list(entry_map.values())
            assert len(classes) == 1, 'Only one eggdeb class per egg allowed'
            return classes[0].load()(distribution)
        else:
            return None

