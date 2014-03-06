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

import os
from itertools import chain

from setuptools import setup
from pkg_resources import require, working_set, resource_filename, Requirement, Distribution, iter_entry_points, resource_listdir, resource_isdir

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
        entry_point_dict = self.distribution.get_entry_map().get(u'reahl.configspec', {})
        entry_point = entry_point_dict.get(u'config', None)
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
        return [cls() for cls in self.migrations_in_order
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
        entry_point_dict = self.distribution.get_entry_map().get(u'reahl.translations')
        translations_package_name = entry_point_dict[self.name].module_name
        translations_file_path = translations_package_name.replace(u'.', u'/')
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
        return self.distribution.get_resource_filename(working_set, u'i18n')

    @classmethod
    @memoized
    def get_languages_supported_by_all(self, root_egg):
        egg_interfaces = self.get_all_relevant_interfaces(root_egg)
        default_languages = [u'en_gb']
        if not egg_interfaces:
            return default_languages

        domains_in_use = [e.name for e in egg_interfaces]

        distributions = set([p.dist for p in iter_entry_points(u'reahl.translations')])
        requirements = [d.as_requirement() for d in distributions]

        languages_for_eggs = {}
        for requirement in requirements:
            languages = [d for d in resource_listdir(requirement, '/reahl/messages')
                         if resource_isdir(requirement, '/reahl/messages/%s' % d)]
            for language in languages:
                language_path = '/reahl/messages/%s/LC_MESSAGES' % language
                domains = [d[:-3] for d in resource_listdir(requirement, language_path) if d.endswith(u'.mo')]
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
    def do_daily_maintenance_for_egg(self, root_egg):
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
        distributions = require(str(main_egg))
        return list(set(distributions)) # To get rid of duplicates

    @classmethod
    def compute_ordered_dependent_distributions(cls, main_egg):
        return cls.topological_sort(cls.get_eggs_for(main_egg))
    
    @classmethod
    def compute_all_relevant_interfaces(cls, main_egg):
        interfaces = []

        for i in cls.compute_ordered_dependent_distributions(main_egg):
            entry_map = i.get_entry_map(u'reahl.eggs')
            if entry_map:
                classes = entry_map.values()
                assert len(classes) == 1, u'Only one eggdeb class per egg allowed'
                interfaces.append(classes[0].load()(i))


        return interfaces

