# Copyright 2013-2018 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""Support for database schema migration."""

from __future__ import print_function, unicode_literals, absolute_import, division
from pkg_resources import parse_version
import logging
import warnings
import inspect

from reahl.component.exceptions import ProgrammerError


class MigrationRun(object):
    def __init__(self, orm_control, eggs_in_order):
        self.orm_control = orm_control
        self.changes = MigrationSchedule('drop_fk', 'drop_pk', 'pre_alter', 'alter', 
                                         'create_pk', 'indexes', 'data', 'create_fk', 'cleanup')
        self.eggs_in_order = eggs_in_order

    def migrations_to_run_for(self, egg):
        return [migration(self.changes) 
                for migration in egg.compute_migrations(self.orm_control.schema_version_for(egg, default='0.0'))]

    def schedule_migrations(self):
        migrations_per_egg = [(egg, self.migrations_to_run_for(egg))
                              for egg in self.eggs_in_order]

        self.schedule_migration_changes(reversed(migrations_per_egg), 'upgrade')
        self.schedule_migration_changes(migrations_per_egg, 'upgrade_cleanup')
        self.schedule_migration_changes(migrations_per_egg, 'schedule_upgrades')

    def schedule_migration_changes(self, migrations_per_egg, method_name):
        for egg, migration_list in migrations_per_egg:
            current_schema_version = self.orm_control.schema_version_for(egg, default='0.0')
            message = 'Scheduling %s %s migrations for %s - from version %s to %s' % \
                          (len(migration_list), method_name, egg.name, 
                           current_schema_version, egg.version)
            logging.getLogger(__name__).info(message)
            for migration in migration_list:
                if hasattr(migration, method_name):
                    logging.getLogger(__name__).info('Scheduling %s for %s' % (method_name, migration))
                    getattr(migration, method_name)()

    def execute_migrations(self):
        self.changes.execute_all()
        self.update_schema_versions()
        
    def update_schema_versions(self):
        for egg in self.eggs_in_order:
            if self.orm_control.schema_version_for(egg, default='0.0') != egg.version:
                logging.getLogger(__name__).info('Migrating %s - updating schema version to %s' % (egg.name, egg.version))
                self.orm_control.update_schema_version_for(egg)


class MigrationSchedule(object):
    def __init__(self, *phases):
        self.phases_in_order = phases
        self.phases = dict([(i, []) for i in phases])

    def schedule(self, phase, to_call, *args, **kwargs):
        try:
            self.phases[phase].append((to_call, args, kwargs))
        except KeyError as e:
            raise ProgrammerError('A phase with name<%s> does not exist.' % phase)

    def execute(self, phase):
        logging.getLogger(__name__).info('Executing schema change phase %s' % phase)
        for to_call, args, kwargs in self.phases[phase]:
            logging.getLogger(__name__).debug(' change: %s(%s, %s)' % (to_call.__name__, args, kwargs))
            to_call(*args, **kwargs)

    def execute_all(self):
        for phase in self.phases_in_order:
            self.execute(phase)


class Migration(object):
    """Represents one logical change that can be made to an existing database schema.
    
       You should extend this class to build your own domain-specific database schema migrations. Set the
       `version` class attribute to a string containing the version of your component for which this Migration
       should be run when upgrading from a previous version.
       
       Never use code imported from your component in a Migration, since Migration code is kept around in
       future versions of a component and may be run to migrate a schema with different versions of the code in your component.
    """

    version = None

    @classmethod
    def is_applicable(cls, current_schema_version, new_version):
        if not cls.version:
            raise ProgrammerError('Migration %s does not have a version set' % cls)
        return parse_version(cls.version) > parse_version(current_schema_version) and \
               parse_version(cls.version) <= parse_version(new_version)

    def __init__(self, changes):
        self.changes = changes

    def schedule(self, phase, to_call, *args, **kwargs):
        """Call this method to schedule a method call for execution later during the specified migration phase.

           Scheduled migrations are first collected from all components, then the calls scheduled for each defined
           phase are executed. Calls in one phase are executed in the order they were scheduled. Phases are executed
           in the following order:

           'drop_fk', 'drop_pk', 'pre_alter', 'alter', 'create_pk', 'indexes', 'data', 'create_fk', 'cleanup'

           :param phase: The name of the phase to schedule this call.
           :param to_call: The method or function to call.
           :param args: The positional arguments to be passed in the call.
           :param kwargs: The keyword arguments to be passed in the call.
        """
        self.changes.schedule(phase, to_call, *args, **kwargs)

    def schedule_upgrades(self):
        """Override this method in a subclass in order to supply custom logic for changing the database schema. This
           method will be called for each of the applicable Migrations listed for all components, in order of 
           dependency of components (the component deepest down in the dependency tree, first).

           **Added in 2.1.2**: Supply custom upgrade logic by calling `self.schedule()`.
        """
        warnings.warn('Ignoring %s.schedule_upgrades(): it does not override schedule_upgrades() (method name typo perhaps?)' % self.__class__.__name__ , 
                      UserWarning, stacklevel=-1)

    @property
    def name(self):
        return '%s.%s' % (inspect.getmodule(self).__name__, self.__class__.__name__)

    def __str__(self):
        return '%s %s' % (self.name, self.version)
