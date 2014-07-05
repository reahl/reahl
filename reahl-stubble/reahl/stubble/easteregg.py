# Copyright 2006, 2008, 2009, 2011, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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
import pkg_resources
from reahl.stubble.stub import FileSystemResourceProvider


class EasterEgg(pkg_resources.Distribution):
    def __init__(self, name='test'):
        self.metadata_provider = FileSystemResourceProvider()
        super(EasterEgg, self).__init__(location=name,
                                        project_name=name,
                                        version = '1.0',
                                        metadata=self.metadata_provider)
        self.entry_points = {}

    def as_requirement_string(self):
        return six.text_type(self.as_requirement())

    def add_dependency(self, spec):
        requirement = pkg_resources.Requirement.parse(spec)
        self._dep_map[None] = [requirement]

    def add_to_working_set(self):
        pkg_resources.working_set.add(self)

    def add_entry_point_from_line(self, group_name, line):
        entry = pkg_resources.EntryPoint.parse(line, dist=self)
        self.entry_points[ (group_name, entry.name) ] = entry

    def add_entry_point(self, group_name, name, the_class):
        entry = pkg_resources.EntryPoint(name, the_class.__module__,
                                         attrs=(the_class.__name__,),
                                         dist=self)
        self.entry_points[ (group_name, entry.name) ] = entry

    def clear(self):
        self.entry_points = {}

    def get_entry_map(self, group=None):
        """Return the entry point map for `group`, or the full entry map"""

        epmap = {}

        for (listed_group, listed_name), entry in self.entry_points.items():
            names_in_group = epmap.get(listed_group, {})
            names_in_group[listed_name] = entry
            epmap[listed_group] = names_in_group

        if group is not None:
            return epmap.get(group,{})
        return epmap

    def set_module_path(self, path):
        self.metadata_provider.module_path = path
