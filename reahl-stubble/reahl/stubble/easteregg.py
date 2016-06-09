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
import six
import sys
import warnings
from contextlib import contextmanager
import pkg_resources
import os


class FileSystemResourceProvider(pkg_resources.NullProvider):
    def __init__(self, distribution):
        self.distribution = distribution

    @property
    def module_path(self):
        return self.distribution.location

    def _has(self, path):
        return os.path.exists(path)

    def _isdir(self, path):
        return os.path.isdir(path)

    def _listdir(self, path):
        return os.listdir(path)

    def _fn(self, base, resource_name):
        return os.path.join(base, *resource_name.split('/'))

    def _get(self, path):
        return open(path, 'rb').read()


class EasterEgg(pkg_resources.Distribution):
    """A stubbed-out Distribution that can be used to fake a Distribution for testing.

       Once an EasterEgg has been constructed, it needs to be added to the global 
       pkg_resources.working_set. If the location is changed after being added, it is 
       necessary to .activate() the EasterEgg before it will be active on sys.path.

       :keyword name: A unique name for this Distribution.
       :keyword location: The location on disk where the contents of this Distribution reside. 
       
       .. versionchanged: 3.2
          Added the location keyword argument and deprecated set_module_path().
    """
    def __init__(self, name='test', location=None):
        self.metadata_provider = FileSystemResourceProvider(self)
        super(EasterEgg, self).__init__(location=location or os.getcwd(),
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
        """Adds this EasterEgg to the global pkg_resources.working_set object."""

        pkg_resources.working_set.add(self, replace=True)

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
        """Change the location of the egg.
           .. deprecated:: 3.2
              Please use .location = instead, or pass location= upon construction.
        """
        warnings.warn('DEPRECATED: EasterEgg.set_module_path(). Please use .location = instead, or pass location= upon construction.', DeprecationWarning, stacklevel=1)
        self.location = path

    def activate(self):
        saved_path = sys.path[:]
        super(EasterEgg, self).activate()
        self.added_paths = set(sys.path) - set(saved_path)

    def contains(self, module):
        return hasattr(module, '__file__') and module.__file__.startswith(self.location)

    def deactivate(self):
        for i in self.added_paths:
            sys.path.remove(i)
        for name, module in list(sys.modules.items()):
            if self.contains(module):
                del sys.modules[name]



        
