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

from pkg_resources import parse_version
import logging
import warnings
import inspect
import traceback

from reahl.component.exceptions import ProgrammerError


class NoRunFound(Exception):
    def __init__(self, run, cluster):
        super().__init__('Could not find a nested run for %s in %s' % (cluster, run))

class MigrationRun:
    @classmethod
    def migrate(cls, root_egg):
        version_tree = VersionTree.from_root_egg(root_egg)
        clusters = version_tree.create_clusters()
        cluster_graph = DependencyGraph.from_vertices(clusters, lambda c: c.dependencies(clusters))
        sorted_clusters = cluster_graph.topological_sort()
        runs = cls.create_runs_for_clusters(sorted_clusters)
        for run in runs:
            run.execute_all()

    def create_runs_for_clusters(cls, clusters_in_tolological_order):
        passxxx

    def for_cluster(cls, cluster):
        return MigrationRun(cluster)

    def __init__(self, orm_control, cluster):
        self.cluster = cluster
        self.orm_control = orm_control
        self.phases_in_order = ['drop_pk', 'pre_alter', 'alter', 
                                'create_pk', 'indexes', 'data', 'create_fk', 'cleanup']
        self.phases = dict([(i, []) for i in self.phases_in_order])
        self.before_nesting_phase = []
        self.last_phase = []
        self.nested_runs = []
        self.eggs_in_order = eggs_in_order

    def schedule_migrations(self):
        pass

    def execute_migrations(self):
        self.execute_all()
        self.update_schema_versions()
        
    def update_schema_versions(self):
        for egg in self.eggs_in_order:
            if self.orm_control.schema_version_for(egg, default='0.0') != egg.version:
                logging.getLogger(__name__).info('Migrating %s - updating schema version to %s' % (egg.name, egg.version))
                self.orm_control.update_schema_version_for(egg)

    def add_nested(self, run):
        try:
            previously_added_run = self.nested_run_for(run.cluster)
            raise ProgrammerError('Trying to add %s, but there is already a nested run for %s: %s' % (run, run.cluster, previously_added_run))
        except NoRunFound:
            self.nested_runs.append(run)
        
    def nested_run_for(self, cluster):
        matching_runs = [run for run in self.nested_runs if run.cluster is cluster]
        if not matching_runs:
            raise NoRunFound()
        return matching_runs[0]

    def schedule(self, phase, scheduling_context, to_call, *args, **kwargs):
        if phase == 'drop_fk':
            if scheduling_egg.previous_version.cluster.visited:
                self.before_nesting_phase.append((to_call, scheduling_context, args, kwargs))
            else:
                self.nested_run_for(scheduling_egg.previous_version.cluster).last_phase.append((to_call, scheduling_context, args, kwargs))
        else:
            try:
                self.phases[phase].append((to_call, scheduling_context, args, kwargs))
            except KeyError as e:
                raise ProgrammerError('A phase with name<%s> does not exist.' % phase)

    def execute(self, scheduled_changes):
        for to_call, scheduling_context, args, kwargs in scheduled_changes:
            logging.getLogger(__name__).debug(' change: %s(%s, %s)' % (to_call.__name__, args, kwargs))
            try:
                to_call(*args, **kwargs)
            except Exception as e:
                class ExceptionDuringMigration(Exception):
                    def __init__(self, scheduling_context):
                        super(ExceptionDuringMigration, self).__init__()
                        self.scheduling_context = scheduling_context
                    def __str__(self):
                        message = super(ExceptionDuringMigration, self).__str__()
                        formatted_context = traceback.format_list([(frame_info.filename, frame_info.lineno, frame_info.function, frame_info.code_context[frame_info.index])
                                                                   for frame_info in self.scheduling_context])
                        return '%s\n\n%s\n\n%s' % (message, 'The above Exception happened for the migration that was scheduled here:', ''.join(formatted_context))
                raise ExceptionDuringMigration(scheduling_context)

    def execute_nested_runs(self):
        for run in self.nested_runs:
            run.execute_all()

    def execute_all(self):
        self.execute(self.before_nesting_phase)
        self.execute_nested_runs()
        for phase in self.phases_in_order:
            self.execute(self.phases[phase])
        self.execute(self.last_phase)

# TO TEST:
#  - migrations can schedule changes on a MigrationRun
#  - you can nest MigrationRuns on a MigrationRun
#  - Scheduling drop_fk is handled differently, depending...(see pic)

class Migration:
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

    def __init__(self, migration_run):
        self.migration_run = migration_run

    def schedule(self, phase, to_call, *args, **kwargs):
        """Call this method to schedule a method call for execution later during the specified migration phase.

           Scheduled migrations are first collected from all components, then the calls scheduled for each defined
           phase are executed. Calls in one phase are executed in the order they were scheduled. Phases are executed
           in the following order:

           'drop_fk', 'drop_pk', 'pre_alter', 'alter', 'create_pk', 'indexes', 'data', 'create_fk', 'cleanup'

           :param phase: The name of the phase to schedule this call.
           :param to_call: The method or function to call.
           :param args: The positional arguments to be passed in the call.
           :keyword kwargs: The keyword arguments to be passed in the call.
        """
        def get_scheduling_context():
            relevant_frames = []
            found_framework_code = False
            frames = iter(inspect.stack()[2:]) #remove this function from the stack
            while not found_framework_code:
                frame = next(frames)
                found_framework_code = frame.filename.endswith(__file__)
                if not found_framework_code:
                    relevant_frames.append(frame)

            return reversed(relevant_frames)
        self.migration_run.schedule(phase, get_scheduling_context(), to_call, *args, **kwargs)

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
