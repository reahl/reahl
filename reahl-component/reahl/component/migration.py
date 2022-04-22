# Copyright 2013-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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

import logging
import warnings
import inspect
import traceback

from reahl.component.exceptions import ProgrammerError
from reahl.component.eggs import DependencyGraph, DependencyCluster


class MigrationPlan:
    def __init__(self, root_egg, orm_control):
        self.root_egg = root_egg
        self.orm_control = orm_control
        self.version_graph = None
        self.cluster_graph = None
        self.schedules = None

    def do_planning(self):
        self.version_graph = self.create_version_graph_for(self.root_egg, self.orm_control)
        self.version_graph.topological_sort() # to detect circular dependencies

        self.cluster_graph = self.create_cluster_graph(self.version_graph)
        self.all_clusters_in_smallest_first_topological_order = list(reversed(list(self.cluster_graph.topological_sort())))
        self.schedules = self.create_schedules_for_clusters(self.all_clusters_in_smallest_first_topological_order)

    @classmethod
    def create_version_graph_for(cls, egg, orm_control):
        graph = {}
        versions = egg.get_versions()
        for version in versions:
            cls.discover_version_graph_for(version, graph, orm_control)
        return DependencyGraph(graph)

    @classmethod
    def discover_version_graph_for(cls, version, graph, orm_control):
        if not version:
            return
        if version not in graph and not version.is_up_to_date(orm_control):
            cls.discover_version_graph_for(version.get_previous_version(), graph, orm_control)
            all_versions = [dependency.get_best_version() for dependency in version.get_dependencies()
                            if dependency.distribution and dependency.is_component]
            children = graph[version] = [v for v in all_versions if not v.is_up_to_date(orm_control)]
            for v in children:
                cls.discover_version_graph_for(v, graph, orm_control)
                cls.discover_version_graph_for(v.get_previous_version(), graph, orm_control)

    @classmethod
    def create_cluster_graph(cls, version_graph):
        clusters = [DependencyCluster(root, contents) for root, contents in version_graph.find_components()]
        return DependencyGraph.from_vertices(clusters, lambda c: c.get_dependencies(clusters))

    def execute(self):
        for schedule in self.schedules:
            schedule.execute_all()
        if self.schedules:
            self.orm_control.prune_schemas_to_only(self.schedules[-1].cluster.versions)

    def explain(self):
        if self.version_graph:
            print('Rendering version graph to: versions.svg')
            self.version_graph.render('versions')
        else: 
            print('Could not compute version graph')
        if self.cluster_graph:
            print('Rendering cluster graph to: clusters.svg')
            self.cluster_graph.render('clusters')
        else: 
            print('Could not compute cluster graph')
        if self.schedules is not None:
            def find_schedules(schedules):
                all_schedules = schedules[:]
                for schedule in schedules:
                    all_schedules.extend(find_schedules(schedule.nested_schedules))
                return all_schedules
            schedule_graph = DependencyGraph.from_vertices(find_schedules(self.schedules), lambda r: r.nested_schedules)
            print('Rendering schedule graph to: schedules.svg')
            schedule_graph.render('schedules')
        else: 
            print('Could not compute schedule graph')
        
    def create_schedules_for_clusters(self, clusters_in_smallest_first_topological_order):
        schedules = []
        for cluster in clusters_in_smallest_first_topological_order:
            if not cluster.visited:
                cluster_children = cluster.get_dependencies(clusters_in_smallest_first_topological_order)
                next_cluster = self.find_highest_parent_of(cluster_children, clusters_in_smallest_first_topological_order) if cluster_children else cluster
                next_cluster.visited = True 
                schedules.append(self.create_migration_schedule_for(next_cluster, clusters_in_smallest_first_topological_order))
        return schedules

    def find_highest_parent_of(self, clusters, clusters_in_smallest_first_topological_order):
        immediate_ancestors = [a for a in clusters_in_smallest_first_topological_order
                                if any([c in a.get_dependencies(clusters_in_smallest_first_topological_order) for c in clusters])]
        return immediate_ancestors[-1]

    def create_migration_schedule_for(self, cluster, clusters_in_smallest_first_topological_order):
        logging.getLogger(__name__).debug('Creating MigrationSchedule for cluster %s' % cluster)
        schedule = MigrationSchedule(self.orm_control, cluster, self.all_clusters_in_smallest_first_topological_order) 
        schedule.schedule_migrations()
        unhandled_decendants_in_smallest_first_topological_order = [c for c in clusters_in_smallest_first_topological_order
                                                                    if (clusters_in_smallest_first_topological_order.index(c) < clusters_in_smallest_first_topological_order.index(cluster))
                                                                        and not c.visited]
        if unhandled_decendants_in_smallest_first_topological_order:
            logging.getLogger(__name__).debug('Adding nested MigrationSchedules for clusters: %s' % unhandled_decendants_in_smallest_first_topological_order)
        for nested_schedule in self.create_schedules_for_clusters(unhandled_decendants_in_smallest_first_topological_order):
            schedule.add_nested(nested_schedule)
        if unhandled_decendants_in_smallest_first_topological_order:
            logging.getLogger(__name__).debug('Done adding nested MigrationSchedules for clusters: %s' % unhandled_decendants_in_smallest_first_topological_order)
        return schedule


class NoMigrationScheduleFound(Exception):
    def __init__(self, cluster):
        super().__init__('Could not find nested schedules for %s' % cluster)


class ExceptionDuringMigration(Exception):
    def __init__(self, scheduling_context):
        super(ExceptionDuringMigration, self).__init__()
        self.scheduling_context = scheduling_context
    def __str__(self):
        message = super(ExceptionDuringMigration, self).__str__()
        formatted_context = traceback.format_list([(frame_info.filename, frame_info.lineno, frame_info.function, frame_info.code_context[frame_info.index])
                                                    for frame_info in self.scheduling_context])
        return '%s\n\n%s\n\n%s' % (message, 'The above Exception happened for the migration that was scheduled here:', ''.join(formatted_context))


class MigrationSchedule:
    """A schedule stating in which order migration operations should be performed to bring the database up to date with the given DependencyCluster"""
    def __init__(self, orm_control, cluster, all_clusters):
        self.cluster = cluster
        self.orm_control = orm_control
        self.phases_in_order = ['drop_pk', 'pre_alter', 'alter', 'create_pk', 'indexes', 'data', 'create_fk', 'cleanup']
        self.phases = dict([(i, []) for i in self.phases_in_order])
        self.before_nesting_phase = []
        self.last_phase = []
        self.after_nested_schedule_phases = {}
        self.nested_schedules = []
        self.all_clusters = all_clusters
        self.current_drop_fk_phase = self.before_nesting_phase

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.cluster)

    def get_previous_cluster_for_version(self, version):
        clusters_containing_previous_version = [c for c in self.all_clusters
                                                if any([v.is_previous_version_of(version) for v in c.versions])]
        previous_cluster = None
        if clusters_containing_previous_version:
            assert len(clusters_containing_previous_version) == 1
            [previous_cluster] = clusters_containing_previous_version

        return previous_cluster

    def schedule_migrations(self):
        for version in self.cluster.get_versions_biggest_first():
            previous_cluster = self.get_previous_cluster_for_version(version)

            if previous_cluster and not previous_cluster.visited:
                self.current_drop_fk_phase = self.after_nested_phase_for(previous_cluster)
            else:
                self.current_drop_fk_phase = self.before_nesting_phase

            for migration_class in version.get_migration_classes():
                migration = migration_class(self)
                logging.getLogger(__name__).debug('Scheduling Migrations for migration %s in cluster %s' % (migration_class, self.cluster))
                migration.schedule_upgrades()
            UpdateSchemaVersion(self, version).schedule_upgrades()

    def add_nested(self, schedule):
        if any([s.cluster is schedule.cluster for s in self.nested_schedules]):
            raise ProgrammerError('Trying to add %s, but there is already a nested schedule for %s' % (schedule, schedule.cluster))
        self.nested_schedules.append(schedule)
        
    def after_nested_phase_for(self, cluster):
        return self.after_nested_schedule_phases.setdefault(cluster, [])

    def schedule(self, phase, scheduling_migration, scheduling_context, to_call, *args, **kwargs):
        if phase == 'drop_fk':
            self.current_drop_fk_phase.append((to_call, scheduling_migration, scheduling_context, args, kwargs))
        else:
            try:
                self.phases[phase].append((to_call, scheduling_migration, scheduling_context, args, kwargs))
            except KeyError as e:
                raise ProgrammerError('A phase with name<%s> does not exist.' % phase)

    def execute(self, scheduled_changes):
        for to_call, scheduling_migration, scheduling_context, args, kwargs in scheduled_changes:
            logging.getLogger(__name__).info('Executing for %s in %s: %s(%s, %s)' % (scheduling_migration, self.cluster, to_call.__name__, args, kwargs))
            try:
                to_call(*args, **kwargs)
            except Exception as e:
                raise ExceptionDuringMigration(scheduling_context)

    def execute_nested_schedules(self):
        for schedule in self.nested_schedules:
            schedule.execute_all()
            self.execute(self.after_nested_schedule_phases[schedule.cluster])

    def execute_all(self):
        self.execute(self.before_nesting_phase)
        self.execute_nested_schedules()
        for phase in self.phases_in_order:
            self.execute(self.phases[phase])


class Migration:
    """Represents one logical change that can be made to an existing database schema.
    
       You should extend this class to build your own domain-specific database schema migrations.
       
       Never use code imported from your component in a Migration, since Migration code is kept around in
       future versions of a component and may be run to migrate a schema with different versions of the code in your component.
    """

    def __init__(self, migration_schedule):
        self.migration_schedule = migration_schedule

    @property
    def orm_control(self):
        return self.migration_schedule.orm_control

    def schedule(self, phase, to_call, *args, **kwargs):
        """Call this method to schedule a method call for execution later during the specified migration phase.

           Scheduled migrations are first collected from all components, then the calls scheduled for each defined
           phase are executed. All the calls scheduled in the same phase are executed in the order they were scheduled. 
           Phases are executed in the following order:

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
                try:
                    frame = next(frames)
                    found_framework_code = frame.filename.endswith(__file__)
                    if (not found_framework_code) or frame.function == 'schedule_upgrades':
                        relevant_frames.append(frame)
                except StopIteration:
                    found_framework_code = True

            return list(reversed(relevant_frames))
        self.migration_schedule.schedule(phase, self, get_scheduling_context(), to_call, *args, **kwargs)

    def schedule_upgrades(self):
        """Override this method in a subclass in order to supply custom logic for changing the database schema. This
           method will be called for each of the applicable Migrations listed for all components. The order in which
           Migrations are scheduled is carefully crafted based on dependencies between versions.

           **Added in 2.1.2**: Supply custom upgrade logic by calling `self.schedule()`.
        """
        warnings.warn('Ignoring %s.schedule_upgrades(): it does not override schedule_upgrades() (method name typo perhaps?)' % self.__class__.__name__ , 
                      UserWarning, stacklevel=-1)

    @property
    def name(self):
        return '%s.%s' % (inspect.getmodule(self).__name__, self.__class__.__name__)

    def __str__(self):
        return self.name


class UpdateSchemaVersion(Migration):
    def __init__(self, migration_schedule, version):
        super().__init__(migration_schedule)
        self.version = version

    def schedule_upgrades(self):
        self.schedule('cleanup', self.migration_schedule.orm_control.set_schema_version_for, self.version)
