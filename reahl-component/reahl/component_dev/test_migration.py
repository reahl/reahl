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

import os
from contextlib import contextmanager
import warnings
import re

from reahl.tofu import Fixture, expected, temp_dir, uses, scenario
from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import CallMonitor, EmptyStub, stubclass

from reahl.component.dbutils import ORMControl
from reahl.component.eggs import ReahlEgg, Version, Dependency, CircularDependencyDetected, InvalidDependencySpecification
from reahl.component.migration import Migration, MigrationPlan, MigrationSchedule, ExceptionDuringMigration
from reahl.component.exceptions import ProgrammerError


@stubclass(Dependency)
class StubDependency:
    type = 'egg'
    distribution = EmptyStub()
    def __init__(self, version, egg_type='egg', is_component=True):
        self.version = version
        self.name = self.version.name
        self.type = egg_type
        self._is_component = is_component

    def get_best_version(self):
        return self.version

    def __str__(self):
        return str(self.version)

    @property
    def is_component(self):
        return self._is_component


@stubclass(ReahlEgg)
class ReahlEggStub(ReahlEgg):
    def __init__(self, name, version_info):
        super().__init__(None)
        self._name = name
        self.version_info = version_info
        self.dependencies = {}

    def create_metadata(self, distribution):
        return {'metadata_version': str(ReahlEgg.metadata_version)}
        
    @property
    def name(self):
        return self._name

    def get_versions(self):
        unsorted_versions = [Version(self, version_number_string) for version_number_string in self.version_info]
        return list(sorted(unsorted_versions, key=lambda x: x.version_number))

    @property
    def installed_version(self):
        return self.get_versions()[-1]

    def get_migration_classes_for_version(self, version):
        return self.version_info[str(version.version_number)]

    def get_dependencies(self, version):
        return self.dependencies.get(version, [])




@stubclass(ORMControl)
class ORMControlStub(ORMControl):
    created_schema_for = None
    pruned_schemas_to = []

    def __init__(self):
        self.versions = {}

    @contextmanager
    def managed_transaction(self):
        yield

    def set_schema_version_for(self, version):
        self.versions[version.egg.name] = str(version.version_number)

    def schema_version_for(self, egg, default=None):
        return self.versions.get(egg.name, '0.0')

    def initialise_schema_version_for(self, egg=None, egg_name=None, egg_version=None):
        self.versions[egg.name] = str(egg.version.version_number)

    def prune_schemas_to_only(self, live_versions):
        self.pruned_schemas_to = live_versions



class MigrateFixture(Fixture):
    def new_orm_control(self):
        return ORMControlStub()

    def new_some_object(self):
        class SomeObject:
            calls_made = []

            def do_something(self, arg):
                self.calls_made.append(arg)

        return SomeObject()

    def check_order(self, operations):
        keys = list(set([i.split('-')[-1] for i in operations]))
        for key in keys:
            try:
                drop_pk_index = operations.index('drop_pk-%s' % key)
            except ValueError:
                drop_pk_index = -1
            try:
                create_pk_index = operations.index('create_pk-%s' % key)
            except ValueError:
                create_pk_index = -1

            create_fk_indexes = [i for i in range(len(operations)) if operations[i] == 'create_fk-%s' % key]
            drop_fk_indexes = [i for i in range(len(operations)) if operations[i] == 'drop_fk-%s' % key]

            assert all([i > create_pk_index for i in create_fk_indexes])   # creating a pk happens before creating a fk to it
            assert drop_pk_index < 0 or drop_pk_index > create_pk_index    # dropping a pk happens after creating it

            for i in range(len(create_fk_indexes)):                        # dropping an fk happens after creating it (multiple times)
                if len(drop_fk_indexes) > i:
                    assert create_fk_indexes[i] < drop_fk_indexes[i]

        
@with_fixtures(MigrateFixture)
def test_how_migration_works(fixture):
    """A logical change to the database is coded in a Migration. In a Migration, override
       schedule_upgrades in which changes are scheduled to be run during the appropriate phase.
    """

    some_object = fixture.some_object
    
    class Migration1(Migration):

        def schedule_upgrades(self):
            self.schedule('drop_fk', some_object.do_something, 'drop_fk-1')
            self.schedule('data', some_object.do_something, 'data-1')
            self.schedule('drop_fk', some_object.do_something, 'drop_fk-2')

    class Migration2(Migration):

        def schedule_upgrades(self):
            self.schedule('drop_fk', some_object.do_something, 'drop_fk-3')

    egg = ReahlEggStub('my_egg', {'1.0': [], '1.1': [Migration1, Migration2]})
    fixture.orm_control.set_schema_version_for(egg.get_versions()[0])

    fixture.orm_control.migrate_db(egg)

    expected_order = ['drop_fk-1', 'drop_fk-2', 'drop_fk-3', 'data-1']
    assert some_object.calls_made == expected_order


@with_fixtures(MigrateFixture)
def test_migrating_dependencies(fixture):
    """Only the necessary Migrations are run to bring the database schema up to date from a previous running installation.
    """

    some_object = fixture.some_object
    
    class MainMigration1(Migration):
        def schedule_upgrades(self):
            self.schedule('create_fk', some_object.do_something, 'create_fk-1')

    class MainMigration2(Migration):
        def schedule_upgrades(self):
            self.schedule('drop_fk', some_object.do_something, 'drop_fk-1')
            self.schedule('create_fk', some_object.do_something, 'create_fk-2')


    orm_control = fixture.orm_control
    main_egg = ReahlEggStub('main_egg', {'1.0': [MainMigration1], '1.1': [MainMigration2]})


    class DependencyMigration1(Migration):
        def schedule_upgrades(self):
            self.schedule('create_pk', some_object.do_something, 'create_pk-1')

    class DependencyMigration2(Migration):
        def schedule_upgrades(self):
            self.schedule('drop_pk', some_object.do_something, 'drop_pk-1')
            self.schedule('create_pk', some_object.do_something, 'create_pk-2')

    dependency_egg = ReahlEggStub('dependency_egg', {'5.0': [DependencyMigration1], '5.1': [DependencyMigration2]})

    [mv1, mv2] = main_egg.get_versions()
    [dv1, dv2] = dependency_egg.get_versions()

    main_egg.dependencies = {str(mv1.version_number): [StubDependency(dv1)],
                             str(mv2.version_number): [StubDependency(dv2)]}

    fixture.orm_control.migrate_db(main_egg)

    expected_order = ['create_pk-1', 'create_fk-1', 'drop_fk-1', 'drop_pk-1', 'create_pk-2', 'create_fk-2']
    assert some_object.calls_made == expected_order


@uses(migrate_fixture=MigrateFixture)
class DependencyScenarios(Fixture):

    @property
    def orm_control(self):
        return self.migrate_fixture.orm_control

    @scenario
    def egg_dependency(self):
        self.egg_type = 'egg'
        self.is_component = True

    @scenario
    def thirdparty_component_dependency(self):
        self.egg_type = 'thirdparty'
        self.is_component = True

    @scenario
    def thirdparty_dependency(self):
        self.egg_type = 'thirdparty'
        self.is_component = False


@with_fixtures(DependencyScenarios)
def test_dependency_types_detected(dependency_scenarios):
    """Components may depend on other components. These dependencies may be referred to as egg or thirdparty dependencies.
    If these dependencies are components, they should be included in the version dependency graph.
    """

    main_egg = ReahlEggStub('main_egg', {'1.0': []})

    dependency_egg = ReahlEggStub('dependency_egg', {'5.0': []})

    [mv1] = main_egg.get_versions()
    [dv1] = dependency_egg.get_versions()

    main_egg.dependencies = {str(mv1.version_number): 
                             [StubDependency(dv1, egg_type=dependency_scenarios.egg_type,
                                                  is_component=dependency_scenarios.is_component)]}

    plan = MigrationPlan(main_egg, dependency_scenarios.orm_control)
    plan.do_planning()

    if dependency_scenarios.is_component:
        assert dv1 in plan.version_graph.graph
    else:
        assert dv1 not in plan.version_graph.graph


@with_fixtures(MigrateFixture)
def test_migrating_dependencies_with_intermediate_versions(fixture):
    """A dependency on a project can skip intermediate versions of the project, yet the necessary migrations are still run.
    """

    some_object = fixture.some_object
    
    class MainMigration1(Migration):
        def schedule_upgrades(self):
            self.schedule('create_fk', some_object.do_something, 'MainMigration1 create_fk-1')

    class MainMigration2(Migration):
        def schedule_upgrades(self):
            self.schedule('drop_fk', some_object.do_something, 'MainMigration2 drop_fk-1')
            self.schedule('create_fk', some_object.do_something, 'MainMigration2 create_fk-4')

    orm_control = fixture.orm_control
    main_egg = ReahlEggStub('main_egg', {'1.0': [MainMigration1], '1.1': [MainMigration2]})

    class DependencyMigration11(Migration):
        def schedule_upgrades(self):
            self.schedule('create_fk', some_object.do_something, 'DependencyMigration11 create_fk-1')

    class DependencyMigration12(Migration):
        def schedule_upgrades(self):
            self.schedule('drop_fk', some_object.do_something, 'DependencyMigration12 drop_fk-1')
            self.schedule('create_fk', some_object.do_something, 'DependencyMigration12 create_fk-2')

    class DependencyMigration13(Migration):
        def schedule_upgrades(self):
            self.schedule('drop_fk', some_object.do_something, 'DependencyMigration13 drop_fk-2')
            self.schedule('create_fk', some_object.do_something, 'DependencyMigration13 create_fk-4')

    dependency_egg1 = ReahlEggStub('dependency_egg1', {'1.1': [DependencyMigration11], '1.2': [DependencyMigration12], '1.3': [DependencyMigration13]})

    class DependencyMigration21(Migration):
        def schedule_upgrades(self):
            self.schedule('create_pk', some_object.do_something, 'DependencyMigration21 create_pk-1')

    class DependencyMigration22(Migration):
        def schedule_upgrades(self):
            self.schedule('drop_pk', some_object.do_something, 'DependencyMigration22 drop_pk-1')
            self.schedule('create_pk', some_object.do_something, 'DependencyMigration22 create_pk-2')

    class DependencyMigration23(Migration):
        def schedule_upgrades(self):
            self.schedule('drop_pk', some_object.do_something, 'DependencyMigration23 drop_pk-2')
            self.schedule('create_pk', some_object.do_something, 'DependencyMigration23 create_pk-3')

    class DependencyMigration24(Migration):
        def schedule_upgrades(self):
            self.schedule('drop_pk', some_object.do_something, 'DependencyMigration24 drop_pk-3')
            self.schedule('create_pk', some_object.do_something, 'DependencyMigration24 create_pk-4')

    dependency_egg2 = ReahlEggStub('dependency_egg2', {'2.1': [DependencyMigration21], '2.2': [DependencyMigration22], '2.3': [DependencyMigration23], '2.4': [DependencyMigration24]})

    [v1, v2] = main_egg.get_versions()
    [dv11, dv12, dv13] = dependency_egg1.get_versions()
    [dv21, dv22, dv23, dv24] = dependency_egg2.get_versions()

    main_egg.dependencies = {str(v1.version_number): [StubDependency(dv11), StubDependency(dv21)],
                             str(v2.version_number): [StubDependency(dv13), StubDependency(dv24)]}  # Jump over dv12

    dependency_egg1.dependencies = {str(dv11.version_number): [StubDependency(dv21)],
                                    str(dv12.version_number): [StubDependency(dv22)],
                                    str(dv13.version_number): [StubDependency(dv24)]}  # Jump over dv23

    fixture.orm_control.migrate_db(main_egg)

    expected_order = [
         'create_pk-1',
         'create_fk-1', 
         'create_fk-1',
         'drop_fk-1', 
         'drop_fk-1',
         
         'drop_pk-1',
         
         'create_pk-2',
         
         'create_fk-2',
         
         'drop_fk-2',
         
         'drop_pk-2',
         
         'create_pk-3',
         'drop_pk-3',
         'create_pk-4',
         'create_fk-4',
         'create_fk-4']

    assert [i.split()[1] for i in some_object.calls_made] == expected_order


@with_fixtures(MigrateFixture)
def test_migrating_from_existing_schema(fixture):
    """The Migrations of all dependencies and all previous versions (and their dependencies) are
       scheduled.
    """

    some_object = fixture.some_object
    
    class MainMigration1(Migration):
        def schedule_upgrades(self):
            self.schedule('create_fk', some_object.do_something, 'create_fk_1')

    class MainMigration2(Migration):
        def schedule_upgrades(self):
            self.schedule('drop_fk', some_object.do_something, 'drop_fk_1')
            self.schedule('create_fk', some_object.do_something, 'create_fk_2')


    orm_control = fixture.orm_control
    main_egg = ReahlEggStub('main_egg', {'1.0': [MainMigration1], '1.1': [MainMigration2]})


    class DependencyMigration1(Migration):
        def schedule_upgrades(self):
            self.schedule('create_pk', some_object.do_something, 'create_pk_1')

    class DependencyMigration2(Migration):
        def schedule_upgrades(self):
            self.schedule('drop_pk', some_object.do_something, 'drop_pk_1')
            self.schedule('create_pk', some_object.do_something, 'create_pk_2')

    dependency_egg = ReahlEggStub('dependency_egg', {'5.0': [DependencyMigration1], '5.1': [DependencyMigration2]})

    [mv1, mv2] = main_egg.get_versions()
    [dv1, dv2] = dependency_egg.get_versions()

    main_egg.dependencies = {str(mv1.version_number): [StubDependency(dv1)],
                             str(mv2.version_number): [StubDependency(dv2)]}

    fixture.orm_control.set_schema_version_for(mv1)
    fixture.orm_control.set_schema_version_for(dv1)
    fixture.orm_control.migrate_db(main_egg)

    expected_order = ['drop_fk_1', 'drop_pk_1', 'create_pk_2', 'create_fk_2']
    assert some_object.calls_made == expected_order


@with_fixtures(MigrateFixture)
def test_migrating_changing_dependencies(fixture):
    """The dependencies of Versions can change during the evolution of the relateOnly the necessary Migrations are run
       to bring the database schema up to date from a previous running installation.
    """

    some_object = fixture.some_object
    
    orm_control = fixture.orm_control

    class MainMigration1(Migration):
        def schedule_upgrades(self):
            self.schedule('create_fk', some_object.do_something, '1 create_fk-21')
            self.schedule('create_fk', some_object.do_something, '1 create_fk-11')

    class MainMigration2(Migration):
        def schedule_upgrades(self):
            self.schedule('drop_fk', some_object.do_something, '2 drop_fk-21')
            self.schedule('drop_fk', some_object.do_something, '2 drop_fk-11')
            self.schedule('create_fk', some_object.do_something, '2 create_fk-12')

    main_egg = ReahlEggStub('main_egg', {'1.0': [MainMigration1], '1.1': [MainMigration2]})

    class DependencyMigration11(Migration):
        def schedule_upgrades(self):
            self.schedule('create_fk', some_object.do_something, '11 create_fk-21')
            self.schedule('create_pk', some_object.do_something, '11 create_pk-11')

    class DependencyMigration12(Migration):
        def schedule_upgrades(self):
            self.schedule('drop_fk', some_object.do_something, '12 drop_fk-21')
            self.schedule('drop_pk', some_object.do_something, '12 drop_pk-11')
            self.schedule('create_pk', some_object.do_something, '12 create_pk-12')

    dependency_egg1 = ReahlEggStub('dependency_egg1', {'5.0': [DependencyMigration11], '5.1': [DependencyMigration12]})

    class DependencyMigration21(Migration):
        def schedule_upgrades(self):
            self.schedule('create_pk', some_object.do_something, '21 create_pk-21')

    class DependencyMigration22(Migration):
        def schedule_upgrades(self):
            self.schedule('create_fk', some_object.do_something, '22 create_fk-12')

    dependency_egg2 = ReahlEggStub('dependency_egg2', {'3.2': [DependencyMigration21], '3.3': [DependencyMigration22]})

    [mv1, mv2] = main_egg.get_versions()
    [dv11, dv12] = dependency_egg1.get_versions()
    [dv21, dv22] = dependency_egg2.get_versions()

    main_egg.dependencies = {str(mv1.version_number): [StubDependency(dv11), StubDependency(dv21)],
                             str(mv2.version_number): [StubDependency(dv12)]} # and no dependency on dependency_egg2, thus no migrations expected

    dependency_egg1.dependencies = {str(dv11.version_number): [StubDependency(dv21)]}
    dependency_egg2.dependencies = {str(dv22.version_number): [StubDependency(dv12)]}  # Dependency gets swapped


    fixture.orm_control.migrate_db(main_egg)

    fixture.check_order([i.split()[1] for i in some_object.calls_made])

    assert '22 create_fk-12' not in some_object.calls_made # Migrations of previously used, but now-dead components are not run
    assert dv22 not in fixture.orm_control.pruned_schemas_to # dv22 is not live anymore, and its schema is cleaned up
    assert all([i in fixture.orm_control.pruned_schemas_to for i in [mv2, dv12]]) # These schemas are still live


@with_fixtures(MigrateFixture)
def test_intra_cluster_circular_dependency(fixture):
    """Circular dependencies within a cluster are not allowed.
    """

    some_object = fixture.some_object

    orm_control = fixture.orm_control
    main_egg = ReahlEggStub('main_egg', {'1.0': []})
    dependency_egg = ReahlEggStub('dependency_egg', {'5.0': []})

    [mv1] = main_egg.get_versions()
    [dv1] = dependency_egg.get_versions()

    main_egg.dependencies = {str(mv1.version_number): [StubDependency(dv1)]}
    dependency_egg.dependencies = {str(dv1.version_number): [StubDependency(mv1)]}
    
    with expected(CircularDependencyDetected, test=r'(dependency_egg\[5\.0\] -> main_egg\[1\.0\] -> dependency_egg\[5\.0\]|main_egg\[1\.0\] -> dependency_egg\[5\.0\] -> main_egg\[1\.0\])'):
        fixture.orm_control.migrate_db(main_egg)


@with_fixtures(MigrateFixture)
def test_dependencies_resulting_in_duplicates_in_cluster(fixture):
    """Dependencies resulting in installing more than one version of the same package are not allowed.
    """

    some_object = fixture.some_object

    orm_control = fixture.orm_control
    main_egg = ReahlEggStub('main_egg', {'1.0': [], '1.1': []})
    dependency_egg = ReahlEggStub('dependency_egg', {'5.0': [], '5.1': []})

    [mv1, mv2] = main_egg.get_versions()
    [dv1, dv2] = dependency_egg.get_versions()

    main_egg.dependencies = {str(mv1.version_number): [StubDependency(dv1)],
                             str(mv2.version_number): [StubDependency(dv2)]}
    dependency_egg.dependencies = {str(dv2.version_number): [StubDependency(mv1)]}

    with expected(InvalidDependencySpecification, test=r'Dependencies result in installing more than one version of: dependency_egg,main_egg\. Dependencies: main_egg\[1\.0\] -> \[dependency_egg\[5\.0\]\],dependency_egg\[5\.1\] -> \[main_egg\[1.0\]\],main_egg\[1\.1\] -> \[dependency_egg\[5\.1\]\]'):
        fixture.orm_control.migrate_db(main_egg)


def test_schedule_executes_in_order():
    """A MigrationSchedule is used internally to schedule calls in different phases. The calls 
       scheduled in each phase are executed in the order the phases have been set up on the MigrationSchedule.
       Within a phase, the calls are executed in the order they were registered in that phase.
    """
    
    migration_schedule = MigrationSchedule(EmptyStub(), EmptyStub(), [])

    class SomeObject:
        def do_something(self, arg):
            pass
    some_object = SomeObject()

    # schedule calls not in registered order
    with CallMonitor(some_object.do_something) as monitor:
        migration_schedule.schedule('cleanup', EmptyStub(), EmptyStub(), some_object.do_something, '1')
        migration_schedule.schedule('create_fk', EmptyStub(), EmptyStub(), some_object.do_something, '2')
        migration_schedule.schedule('data', EmptyStub(), EmptyStub(), some_object.do_something, '3')
        migration_schedule.schedule('indexes', EmptyStub(), EmptyStub(), some_object.do_something, '4')
        migration_schedule.schedule('create_pk', EmptyStub(), EmptyStub(), some_object.do_something, '5')

        migration_schedule.schedule('alter', EmptyStub(), EmptyStub(), some_object.do_something, 'c1')
        migration_schedule.schedule('drop_pk', EmptyStub(), EmptyStub(),some_object.do_something, 'a1')
        migration_schedule.schedule('pre_alter', EmptyStub(), EmptyStub(),some_object.do_something, 'b')
        migration_schedule.schedule('drop_pk', EmptyStub(), EmptyStub(),some_object.do_something, 'a2')
        migration_schedule.schedule('alter', EmptyStub(), EmptyStub(),some_object.do_something, 'c2')

    migration_schedule.execute_all()

    actual_order = [call.args[0] for call in monitor.calls]
    expected_order = ['a1', 'a2', 'b', 'c1', 'c2', '5', '4', '3', '2', '1']
    assert actual_order == expected_order


def test_schedule_executes_phases_with_parameters():
    """When a MigrationSchedule executes the calls that were scheduled from a Migration, 
       the methods are actually called, and passed the correct arguments."""

    class SomeObject:
        def please_call_me(self, arg, kwarg=None):
            pass
    some_object = SomeObject()
    
    migration_schedule = MigrationSchedule(EmptyStub(), EmptyStub(), [])
    migration = Migration(migration_schedule)

    with CallMonitor(some_object.please_call_me) as monitor:
        migration.schedule('alter', some_object.please_call_me, 'myarg', kwarg='mykwarg')

    migration_schedule.execute_all()

    assert monitor.calls[0].args == ('myarg',)
    assert monitor.calls[0].kwargs == dict(kwarg='mykwarg')


def test_invalid_schedule_name_raises():
    """A useful error is raised when an attempt is made to schedule a call in a phase that is not defined."""
    
    migration_schedule = MigrationSchedule(EmptyStub(), EmptyStub(), [])

    with expected(ProgrammerError, test=r'A phase with name<wrong_name> does not exist\.'):
        migration_schedule.schedule('wrong_name', EmptyStub(), EmptyStub(), EmptyStub())


def test_missing_schedule_upgrades_warns():
    """If a programmer does not override schedule_upgrades, a warning is raised."""
    class TestMigration(Migration):
        pass

    with warnings.catch_warnings(record=True) as raised_warnings:
        warnings.simplefilter("always")
  
        TestMigration(EmptyStub()).schedule_upgrades()
 
    [warning] = raised_warnings
    expected_message = 'Ignoring TestMigration.schedule_upgrades(): it does not override schedule_upgrades() ' \
                       '(method name typo perhaps?)'
    assert str(warning.message) == expected_message


def test_error_reporting_on_breaking_migrations():
    """When there is an error during execution of a Migration, the code where it was scheduled is reported."""

    class SomeObject:
        def please_call_me(self):
            raise Exception('breaking intentionally')
    some_object = SomeObject()

    migration_schedule = MigrationSchedule(EmptyStub(), EmptyStub(), [])
    migration = Migration(migration_schedule)

    migration.schedule('alter', some_object.please_call_me)

    def is_please_call_me_on_stack(ex):
        return re.match(".*The above Exception happened for the migration that was scheduled here:.*    migration.schedule\('alter', some_object.please_call_me\)", str(ex), re.MULTILINE|re.S)
    with expected(ExceptionDuringMigration, test=is_please_call_me_on_stack):
        migration_schedule.execute_all()


@with_fixtures(MigrateFixture)
def test_planning(fixture):
    """A plan can be explained by generating graphs used by the migration algorithm.
    """

    egg = ReahlEggStub('my_egg', {'1.0': [], '1.1': []})

    plan = MigrationPlan(egg, fixture.orm_control)
    plan.do_planning()

    with temp_dir().as_cwd() as dir_name:
        plan.explain()
        assert os.path.isfile(os.path.join(dir_name, 'clusters.svg'))
        assert os.path.isfile(os.path.join(dir_name, 'versions.svg'))
        assert os.path.isfile(os.path.join(dir_name, 'schedules.svg'))



