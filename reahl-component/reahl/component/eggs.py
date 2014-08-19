# Copyright 2007-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from __future__ import unicode_literals
from __future__ import print_function
import os
import os.path
import logging

from pkg_resources import Requirement
from pkg_resources import iter_entry_points
from pkg_resources import require
from pkg_resources import resource_isdir
from pkg_resources import resource_listdir
from pkg_resources import working_set

from reahl.component.decorators import memoized

class Attachment(object):
    def __init__(self, filename, label):
        self.filename = filename
        self.label = label

class ReahlEgg(object):
    interface_cache = {}

    def __init__(self, distribution):
        self.distribution = distribution

    @property
    def name(self):
        return self.distribution.key

    @property
    def version(self):
        return self.distribution.version

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

    def get_persisted_classes_in_order(self, orm_control):
        return self.get_ordered_classes_exported_on('reahl.persistlist')
        
    def find_attachments(self, label):
        return [Attachment(i, label) for i in self.get_ordered_names_exported_on('reahl.attachments.%s' % label)]

    @property
    def migrations_in_order(self):
        return self.get_ordered_classes_exported_on('reahl.migratelist')

    def compute_migrations(self, current_schema_version):
        return [cls for cls in self.migrations_in_order
                if cls.is_applicable(current_schema_version, self.version)]

    def get_ordered_names_exported_on(self, entry_point):
        entry_point_dict = self.distribution.get_entry_map().get(entry_point, {})
        ordered_names = [(int(name.split(':')[0]), ':'.join(name.split(':')[1:])) for name in entry_point_dict.keys()]
        return [name for order, name in sorted(ordered_names)]

    def get_ordered_classes_exported_on(self, entry_point):
        entry_point_dict = self.distribution.get_entry_map().get(entry_point, {})
        return [entry.load() for order, entry in sorted([(int(order), e) for order, e in entry_point_dict.items()])]

    def get_classes_exported_on(self, entry_point):
        entry_point_dict = self.distribution.get_entry_map().get(entry_point, {})
        return [entry.load() for name, entry in entry_point_dict.items()]

    @property
    def translation_pot_filename(self):
        entry_point_dict = self.distribution.get_entry_map().get('reahl.translations')
        translations_package_name = entry_point_dict[self.name].module_name
        translations_file_path = translations_package_name.replace('.', '/')
        return self.distribution.get_resource_filename(self.distribution, '%s/%s' % (translations_file_path, self.name))

    @property
    def scheduled_jobs(self):
        return self.get_classes_exported_on('reahl.scheduled_jobs')
    
    def do_daily_maintenance(self):
        for job in self.scheduled_jobs:
            job()

    def get_roles_to_add(self):
        "returns a list of role classes"
        return []

    @property
    def locale_dirname(self):
        return self.distribution.get_resource_filename(working_set, 'i18n')

    @classmethod
    def get_egg_internal_path_for(cls, translations_entry_point):
        module = translations_entry_point.load()
        dir_or_egg_name = translations_entry_point.dist.location.split(os.sep)[-1]
        paths = [p for p in module.__path__ if p.find('%s%s' % (dir_or_egg_name, os.path.sep)) > 0]
        unique_paths = {p.split('%s/' % dir_or_egg_name)[-1] for p in paths}
        assert len(unique_paths) <=1, \
            'Only one translations package per component is allowed, found %s for %s' % (paths, translations_entry_point.dist)
        assert len(unique_paths) >0, \
            'No translations found for %s, did you specify a translations package and forget to add locales in there?' % translations_entry_point.dist
        return unique_paths.pop()

    @classmethod
    @memoized
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
                             if resource_isdir(requirement, '%s/%s' % (egg_internal_path, d))]
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
    # Algorithm from: http://www.logarithmic.net/pfh-files/blog/01208083168/sort.py
    # See also: http://en.wikipedia.org/wiki/Topological_sorting
        
        graph = {}
        for dist in distributions:
            dependencies = [working_set.find(i) for i in dist.requires()]
            my_requirements =  dist.requires()
            #we want the subset of stuff in the basket we actually depend on, not just the basket itself
            basket_requirements = [i for i in my_requirements
                                   if i.extras]
            for basket in basket_requirements:
                dependencies.extend([working_set.find(Requirement.parse(i)) for i in basket.extras])
                
            graph[dist] = dependencies
        
        count = { }
        for node in graph:
            count[node] = 0
        for node in graph:
            for successor in graph[node]:
                count[successor] += 1

        ready = [ node for node in graph if count[node] == 0 ]
        
        result = []
        while ready:
            node = ready.pop(-1)
            result.append(node)
            
            for successor in graph[node]:
                count[successor] -= 1
                if count[successor] == 0:
                    ready.append(successor)
        
        assert set(distributions) == set(result)
        return result

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
            entry_map = i.get_entry_map('reahl.eggs')
            if entry_map:
                classes = entry_map.values()
                assert len(classes) == 1, 'Only one eggdeb class per egg allowed'
                interfaces.append(classes[0].load()(i))


        return interfaces

