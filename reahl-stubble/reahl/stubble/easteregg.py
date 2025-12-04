# Copyright 2013-2023 Reahl Software Services (Pty) Ltd. All rights reserved.
#
#    This file is part of Reahl.
#
#    Reahl is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation; version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import contextlib
import sys
import os

# Import modern API (always required)
if sys.version_info < (3, 8):
    try:
        import importlib_metadata
    except ImportError:
        raise ImportError('You are on an older version of python. Please install importlib-metadata')
else:
    import importlib.metadata as importlib_metadata

# Import old API if available (optional, for backwards compatibility)
try:
    import pkg_resources
    _HAS_PKG_RESOURCES = True
except ImportError:
    _HAS_PKG_RESOURCES = False
    pkg_resources = None


def can_use_modern_entry_points_api():
    """Check if modern importlib.metadata.entry_points() API is available"""
    try:
        importlib_metadata.entry_points(group='test')
        return True
    except (AttributeError, TypeError):
        return False


# Global registry for all EasterEggs
_active_eastereggs = []
_patches_installed = False


def _register_easteregg(egg):
    if egg not in _active_eastereggs:
        _active_eastereggs.append(egg)


def _unregister_easteregg(egg):
    if egg in _active_eastereggs:
        _active_eastereggs.remove(egg)


def _get_active_eastereggs():
    return list(reversed(_active_eastereggs))


# Modern API classes (always available)
class ImportlibEntryPoint:
    """Entry point for importlib.metadata API"""
    def __init__(self, name, value, group, dist):
        self.name = name
        self.value = value  # e.g., "module.name:ClassName"
        self.group = group
        self.dist = dist

    def load(self):
        """Load the entry point target"""
        module_name, _, attrs = self.value.partition(':')
        module = __import__(module_name, fromlist=['__name__'])
        if attrs:
            obj = module
            for attr in attrs.split('.'):
                obj = getattr(obj, attr)
            return obj
        return module

    @property
    def module(self):
        return self.value.split(':')[0]
    
    def matches(self, **params):
        group = params.get('group')
        name = params.get('name')
        if group is not None and group != self.group:
            return False
        if name is not None and name != self.name:
            return False
        return True

    def __repr__(self):
        return f"{self.name} = {self.value}"


class ImportlibEasterEgg:
    """Stubbed Distribution for importlib.metadata API

       Once an ImportlibEasterEgg has been constructed, it needs to be added to the
       importlib.metadata mock by calling add_to_working_set().

       :keyword name: A unique name for this Distribution.
       :keyword location: The location on disk where the contents of this Distribution reside.
    """

    def __init__(self, name='test', location=None):
        self.location = location or os.getcwd()
        self.project_name = name
        self.version = '1.0'
        self.entry_points = {}
        self.stubbed_metadata = {}
        self._dep_map = {}
        self.added_paths = set()

    @property
    def name(self):
        """Distribution name (lowercase as per modern API convention)"""
        return self.project_name.lower()

    @property
    def metadata(self):
        """Return dict with metadata"""
        return {
            'Name': self.project_name,
            'Version': self.version
        }

    @property
    def files(self):
        """List of files in distribution (return None for stub)"""
        return None

    def read_text(self, filename):
        """Read a metadata file"""
        if filename in self.stubbed_metadata:
            return self.stubbed_metadata[filename]
        raise FileNotFoundError(filename)

    def add_entry_point_from_line(self, group_name, line):
        """Add an entry point from a setuptools-style line"""
        name, _, value = line.partition('=')
        name = name.strip()
        value = value.strip()
        entry = ImportlibEntryPoint(name, value, group_name, self)
        self.entry_points[(group_name, entry.name)] = entry
        return entry

    def add_entry_point(self, group_name, name, the_class):
        """Add an entry point for a class"""
        value = f"{the_class.__module__}:{the_class.__name__}"
        entry = ImportlibEntryPoint(name, value, group_name, self)
        self.entry_points[(group_name, entry.name)] = entry
        return entry

    def add_dependency(self, spec):
        """Add a dependency requirement"""
        self._dep_map[None] = self._dep_map.get(None, [])
        self._dep_map[None].append(spec)
        return spec

    @property
    def requires(self):
        """List dependency requirement strings (modern distribution compatibility)"""
        return list(self._dep_map.get(None, []))

    def as_requirement_string(self):
        """Return requirement string"""
        return f"{self.project_name}=={self.version}"

    def as_requirement(self):
        """Return as a requirement"""
        return self.as_requirement_string()

    def add_to_working_set(self):
        """Register this EasterEgg with the modern API mock"""
        _register_easteregg(self)
        global _patches_installed
        if not _patches_installed:
            _install_patches()
            _patches_installed = True
        return self

    def remove_from_working_set(self):
        _unregister_easteregg(self)
    
    def clear(self):
        """Clear entry points and dependencies"""
        self.entry_points = {}
        self._dep_map.clear()

    def get_entry_map(self, group=None):
        """Return the entry point map (for compatibility)"""
        epmap = {}
        for (listed_group, listed_name), entry in self.entry_points.items():
            names_in_group = epmap.get(listed_group, {})
            names_in_group[listed_name] = entry
            epmap[listed_group] = names_in_group

        if group is not None:
            return epmap.get(group, {})
        return epmap

    @contextlib.contextmanager
    def installed(self):
        self.add_to_working_set()
        self.activate()
        try:
            yield
        finally:
            self.deactivate()
            self.remove_from_working_set()
            
    @contextlib.contextmanager
    def active(self):
        """Context manager to activate this EasterEgg"""
        self.activate()
        try:
            yield
        finally:
            self.deactivate()

    def activate(self, **kwargs):
        """Add location to sys.path"""
        saved_path = sys.path[:]
        if self.location not in sys.path:
            sys.path.insert(0, self.location)
        self.added_paths = set(sys.path) - set(saved_path)

    def deactivate(self):
        """Remove from sys.path and unregister"""
        for i in self.added_paths:
            if i in sys.path:
                sys.path.remove(i)
        for name, module in list(sys.modules.items()):
            if self.contains(module):
                del sys.modules[name]

    def contains(self, module):
        """Check if a module is part of this distribution"""
        return hasattr(module, '__file__') and module.__file__ and \
               module.__file__.startswith(self.location)


# Patching infrastructure for modern API (always available)
_original_entry_points = importlib_metadata.entry_points
_original_distribution = importlib_metadata.distribution


def _patched_entry_points(**kwargs):
    """Patched entry_points that includes active EasterEggs"""
    group = kwargs.get('group', None)

    # Get real entry points
    real_eps = _original_entry_points(**kwargs)

    # Add EasterEgg entry points
    easteregg_eps = []
    for egg in _get_active_eastereggs():
        for (ep_group, ep_name), entry_point in egg.entry_points.items():
            if group is None or ep_group == group:
                easteregg_eps.append(entry_point)

    entry_points_type = getattr(importlib_metadata, 'EntryPoints', None)
    selectable_groups_type = getattr(importlib_metadata, 'SelectableGroups', None)

    if entry_points_type and isinstance(real_eps, entry_points_type):
        return entry_points_type([*real_eps, *easteregg_eps])

    if selectable_groups_type and isinstance(real_eps, selectable_groups_type):
        combined = {group: list(entries) for group, entries in real_eps.items()}
        for entry_point in easteregg_eps:
            combined.setdefault(entry_point.group, []).append(entry_point)
        return selectable_groups_type(combined)

    if isinstance(real_eps, dict):  # Legacy API returning mapping
        combined = {group: list(entries) for group, entries in real_eps.items()}
        for entry_point in easteregg_eps:
            combined.setdefault(entry_point.group, []).append(entry_point)
        return combined

    return list(real_eps) + easteregg_eps


def _patched_distribution(name):
    """Patched distribution that includes EasterEggs"""
    for egg in _get_active_eastereggs():
        if egg.name == name.lower() or egg.project_name.lower() == name.lower():
            return egg
    return _original_distribution(name)


def _install_patches():
    """Install patches for importlib.metadata"""
    importlib_metadata.entry_points = _patched_entry_points
    importlib_metadata.distribution = _patched_distribution


def _uninstall_patches():
    """Restore original functions"""
    importlib_metadata.entry_points = _original_entry_points
    importlib_metadata.distribution = _original_distribution


if _HAS_PKG_RESOURCES:
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


    class PkgResourcesEasterEgg(pkg_resources.Distribution):
        """Stubbed Distribution for pkg_resources API

           Once a PkgResourcesEasterEgg has been constructed, it needs to be added to the global
           pkg_resources.working_set. If the location is changed after being added, it is
           necessary to .activate() the EasterEgg before it will be active on sys.path.

           :keyword name: A unique name for this Distribution.
           :keyword location: The location on disk where the contents of this Distribution reside.

           .. versionchanged:: 3.2
              Added the location keyword argument and deprecated set_module_path().

           .. versionchanged:: 4.0
              Removed set_module_path()
        """
        def __init__(self, name='test', location=None):
            self.metadata_provider = FileSystemResourceProvider(self)
            super().__init__(location=location or os.getcwd(),
                                            project_name=name,
                                            version='1.0',
                                            metadata=self.metadata_provider)
            self.entry_points = {}
            self.stubbed_metadata = {}
            self.added_paths = set()

        def has_metadata(self, name):
            if name in self.stubbed_metadata:
                return True
            try:
                super()._get_metadata(name)
            except KeyError:
                return False
            return True

        def get_metadata(self, name):
            if name in self.stubbed_metadata:
                return self.stubbed_metadata[name]
            else:
                return super()._get_metadata(name)

        def as_requirement_string(self):
            return str(self.as_requirement())

        def add_dependency(self, spec):
            requirement = pkg_resources.Requirement.parse(spec)
            self._dep_map[None] = [requirement]
            return requirement

        def add_to_working_set(self):
            """Adds this EasterEgg to the global pkg_resources.working_set object."""
            pkg_resources.working_set.add(self, replace=True)
            _register_easteregg(self)
            return self

        def add_entry_point_from_line(self, group_name, line):
            entry = pkg_resources.EntryPoint.parse(line, dist=self)
            self.entry_points[(group_name, entry.name)] = entry
            return entry

        def add_entry_point(self, group_name, name, the_class):
            entry = pkg_resources.EntryPoint(name, the_class.__module__,
                                             attrs=(the_class.__name__,),
                                             dist=self)
            self.entry_points[(group_name, entry.name)] = entry
            return entry

        def clear(self):
            self.entry_points = {}
            self._dep_map.clear()

        def get_entry_map(self, group=None):
            """Return the entry point map for `group`, or the full entry map"""

            epmap = {}

            for (listed_group, listed_name), entry in self.entry_points.items():
                names_in_group = epmap.get(listed_group, {})
                names_in_group[listed_name] = entry
                epmap[listed_group] = names_in_group

            if group is not None:
                return epmap.get(group, {})
            return epmap

        @contextlib.contextmanager
        def active(self):
            self.activate()
            try:
                yield
            finally:
                self.deactivate()

        def activate(self, **kwargs):
            saved_path = sys.path[:]
            super().activate(**kwargs)
            self.added_paths = set(sys.path) - set(saved_path)

        def contains(self, module):
            return hasattr(module, '__file__') and module.__file__ and module.__file__.startswith(self.location)

        def deactivate(self):
            for i in self.added_paths:
                sys.path.remove(i)
            for name, module in list(sys.modules.items()):
                if self.contains(module):
                    del sys.modules[name]
            _unregister_easteregg(self)
