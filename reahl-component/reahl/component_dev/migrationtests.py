# Copyright 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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
from contextlib import contextmanager

from reahl.tofu import Fixture, test, vassert, expected, NoException
from reahl.stubble import CallMonitor, EmptyStub


from reahl.component.dbutils import ORMControl
from reahl.component.eggs import ReahlEgg
from reahl.component.migration import Migration, MigrationSchedule, MigrationRun
from reahl.component.exceptions import ProgrammerError

# Migrations schedule changes to be run in several phases on a single object of some kind
# the relevant migrations are computed to be run, then allowed to schedule their changes
# phases are run, in order, tasks in a phase are run in the order they were scheduled

# All the migrations are scheduled, then run for all the migrations to bring things up to each intermediate version.


class ReahlEggStub(ReahlEgg):
    def __init__(self, name, version, migrations):
        super(ReahlEggStub, self).__init__(None)
        self._name = name
        self._version = version
        self.migrations = migrations
    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    @property
    def migrations_in_order(self):
        return self.migrations


class ORMControlStub(ORMControl):
    created_schema_for = None
    def __init__(self):
        self.versions = {}
    @contextmanager
    def managed_transaction(self):
        yield
    def update_schema_version_for(self, egg):
        self.versions[egg.name] = egg.version
    def schema_version_for(self, egg):
        return self.versions[egg.name]
    def initialise_schema_version_for(self, egg):
        self.versions[egg.name] = egg.version
    def set_currently_installed_version_for(self, egg, version_number):
        self.versions[egg.name] = version_number
    def create_db_tables(self, transaction, new_eggs):
        self.created_schema_for = new_eggs


class MigrateFixture(Fixture):
    def new_orm_control(self):
        return ORMControlStub()


@test(MigrateFixture)
def how_migration_works(fixture):
    """Calls that will modify the database are scheduled in the schedule_upgrades() method of all
       the applicable Migrations for a single migration run. `shedule_upgrades()` is called on each
       migration in order of their versions. Once all calls are scheduled,
       they are executed as scheduled.
    """

    class SomeObject(object):
        calls_made = []
        def do_something(self, arg):
            self.calls_made.append(arg)
    some_object = SomeObject()
    
    class Migration1(Migration):
        version = '2.0'
        def schedule_upgrades(self):
            self.schedule('drop_fk', some_object.do_something, 'drop_fk_1')
            self.schedule('data', some_object.do_something, 'data_1')
            self.schedule('drop_fk', some_object.do_something, 'drop_fk_2')

    class Migration2(Migration):
        version = '3.0'
        def schedule_upgrades(self):
            self.schedule('drop_fk', some_object.do_something, 'drop_fk_3')

    egg = ReahlEggStub('my_egg', '4.0', [Migration1, Migration2])
    fixture.orm_control.set_currently_installed_version_for(egg, '1.0')

    fixture.orm_control.migrate_db([egg])

    expected_order = ['drop_fk_1', 'drop_fk_2', 'drop_fk_3', 'data_1']
    vassert( some_object.calls_made == expected_order )


@test(MigrateFixture)
def schedule_executes_in_order(fixture):
    """A MigrationSchedule is used internally to schedule calls in different phases. The calls 
       scheduled in each phase are executed in the order the phases have been set up on the MigrationSchedule.
       Within a phase, the calls are executed in the order they were registered in that phase.
    """
    
    schedule_names = ['a', 'b', 'c']
    migration_schedule = MigrationSchedule(*schedule_names)

    class SomeObject(object):
        def do_something(self, arg):
            pass
    some_object = SomeObject()

    #schedule calls not in registered order
    with CallMonitor(some_object.do_something) as monitor:
        migration_schedule.schedule('c', some_object.do_something, 'c1')
        migration_schedule.schedule('a', some_object.do_something, 'a1')
        migration_schedule.schedule('b', some_object.do_something, 'b')
        migration_schedule.schedule('a', some_object.do_something, 'a2')
        migration_schedule.schedule('c', some_object.do_something, 'c2')

    migration_schedule.execute_all()

    actual_order = [call.args[0] for call in monitor.calls]
    expected_order = ['a1', 'a2', 'b', 'c1', 'c2']
    vassert( actual_order == expected_order )


@test(MigrateFixture)
def schedule_executes_phases_with_parameters(fixture):
    """When a MigrationSchedule executes the calls that were scheduled from a Migration, 
       the methods are actually called, and passed the correct arguments."""

    class SomeObject(object):
        def please_call_me(self, arg, kwarg=None):
            pass
    some_object = SomeObject()
    
    migration_schedule = MigrationSchedule('phase_name')
    migration = Migration(migration_schedule)

    with CallMonitor(some_object.please_call_me) as monitor:
        migration.schedule('phase_name', some_object.please_call_me, 'myarg', kwarg='mykwarg')

    migration_schedule.execute_all()

    vassert( monitor.calls[0].args == ('myarg',) )
    vassert( monitor.calls[0].kwargs == dict(kwarg='mykwarg') )


@test(MigrateFixture)
def invalid_schedule_name_raises(fixture):
    """A useful error is raised when an attempt is made to schedule a call in a phase that is not defined."""
    
    valid_schedule_names = ['a', 'b']
    migration_schedule = MigrationSchedule(*valid_schedule_names)

    def check_exception(ex):
        vassert( six.text_type(ex) == 'A phase with name<wrong_name> does not exist.' )

    with expected(ProgrammerError, test=check_exception):
        migration_schedule.schedule('wrong_name', None)


@test(MigrateFixture)
def version_dictates_execution_of_migration_(fixture):
    """Each Migration should have a class attribute `version` that states which version of the component
       it upgrades the database schema to. Only the Migrations with versions greater than the current 
       schema version are included in a MigrationRun for a given egg.
    """
    
    class PreviousVersionMigration(Migration):
        version = '1.0'
    class MatchingCurrentVersionMigration(Migration):
        version = '2.0'
    class NewerVersionMigration(Migration):
        version = '3.0'
    class EvenNewerVersionMigration(Migration):
        version = '4.0'

    egg = ReahlEggStub('my_egg', '4.0', [PreviousVersionMigration, MatchingCurrentVersionMigration, 
                                         NewerVersionMigration, EvenNewerVersionMigration])
    fixture.orm_control.set_currently_installed_version_for(egg, '2.0')

    migration_run = MigrationRun(fixture.orm_control, [egg])
    migrations_to_run = migration_run.migrations_to_run_for(egg)
    classes_to_run = [m.__class__ for m in migrations_to_run]
    vassert( classes_to_run == [NewerVersionMigration, EvenNewerVersionMigration] )


@test(MigrateFixture)
def version_of_migration_not_set_error(fixture):
    """If the version to which a Migration is applicable is not set, an error is raised."""
    class TestMigration(Migration):
        pass

    egg = ReahlEggStub('my_egg', '1.0', [TestMigration])
    fixture.orm_control.set_currently_installed_version_for(egg, '0.0')

    def check_exception(ex):
        vassert( six.text_type(ex) == 'Migration <class \'reahl.component_dev.migrationtests.TestMigration\'> does not have a version set' )

    with expected(ProgrammerError, test=check_exception):
        fixture.orm_control.migrate_db([egg])


@test(MigrateFixture)
def available_migration_phases(fixture):
    """These are the phases, and order of the phases in a MigrationRun."""

    migration_run = MigrationRun(fixture.orm_control, [])
    
    expected_order = ('drop_fk', 'drop_pk', 'pre_alter', 'alter', 'create_pk', 'indexes', 'data', 'create_fk', 'cleanup')
    vassert( migration_run.changes.phases_in_order == expected_order  )


@test(MigrateFixture)
def schema_version_housekeeping(fixture):
    """The database keeps track of the schema for each installed component. After a migration run
       the currently installed versions are updated.
    """
    
    egg = ReahlEggStub('my_egg', '2.0', [])
    fixture.orm_control.set_currently_installed_version_for(egg, '1.0')
    migration_run = MigrationRun(fixture.orm_control, [egg])
    migration_run.execute_migrations()
    vassert( fixture.orm_control.schema_version_for(egg) == '2.0' )



