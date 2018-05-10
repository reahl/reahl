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


from __future__ import print_function, unicode_literals, absolute_import, division

import six
from contextlib import contextmanager
import warnings
import re


from reahl.tofu import Fixture, expected
from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import CallMonitor, EmptyStub


from reahl.component.dbutils import ORMControl
from reahl.component.eggs import ReahlEgg
from reahl.component.migration import Migration, MigrationSchedule, MigrationRun
from reahl.component.exceptions import ProgrammerError


class FakeStubClass(object):
    # noinspection PyUnusedLocal
    def __init__(self, cls):
        pass

    def __call__(self, cls):
        warnings.warn('This needs to become stubble.stubclass, but stubble does not deal with this scenario - it needs to be fixed')
        return cls

stubclass = FakeStubClass


@stubclass(ReahlEgg)
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


@stubclass(ORMControl)
class ORMControlStub(ORMControl):
    created_schema_for = None

    def __init__(self):
        self.versions = {}

    @contextmanager
    def managed_transaction(self):
        yield

    def update_schema_version_for(self, egg):
        self.versions[egg.name] = egg.version

    # noinspection PyUnusedLocal
    def schema_version_for(self, egg, default=None):
        return self.versions[egg.name]

    def initialise_schema_version_for(self, egg):
        self.versions[egg.name] = egg.version

    def set_currently_installed_version_for(self, egg, version_number):
        self.versions[egg.name] = version_number


class MigrateFixture(Fixture):
    def new_orm_control(self):
        return ORMControlStub()


@with_fixtures(MigrateFixture)
def test_how_migration_works(migrate_fixture):
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
    migrate_fixture.orm_control.set_currently_installed_version_for(egg, '1.0')

    migrate_fixture.orm_control.migrate_db([egg])

    expected_order = ['drop_fk_1', 'drop_fk_2', 'drop_fk_3', 'data_1']
    assert some_object.calls_made == expected_order


def test_schedule_executes_in_order():
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

    # schedule calls not in registered order
    with CallMonitor(some_object.do_something) as monitor:
        migration_schedule.schedule('c', some_object.do_something, 'c1')
        migration_schedule.schedule('a', some_object.do_something, 'a1')
        migration_schedule.schedule('b', some_object.do_something, 'b')
        migration_schedule.schedule('a', some_object.do_something, 'a2')
        migration_schedule.schedule('c', some_object.do_something, 'c2')

    migration_schedule.execute_all()

    actual_order = [call.args[0] for call in monitor.calls]
    expected_order = ['a1', 'a2', 'b', 'c1', 'c2']
    assert actual_order == expected_order


def test_schedule_executes_phases_with_parameters():
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

    assert monitor.calls[0].args == ('myarg',)
    assert monitor.calls[0].kwargs == dict(kwarg='mykwarg')


def test_invalid_schedule_name_raises():
    """A useful error is raised when an attempt is made to schedule a call in a phase that is not defined."""
    
    valid_schedule_names = ['a', 'b']
    migration_schedule = MigrationSchedule(*valid_schedule_names)

    with expected(ProgrammerError, test='A phase with name<wrong_name> does not exist\.'):
        migration_schedule.schedule('wrong_name', None)


@with_fixtures(MigrateFixture)
def test_version_dictates_execution_of_migration_(migrate_fixture):
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
    migrate_fixture.orm_control.set_currently_installed_version_for(egg, '2.0')

    migration_run = MigrationRun(migrate_fixture.orm_control, [egg])
    migrations_to_run = migration_run.migrations_to_run_for(egg)
    classes_to_run = [m.__class__ for m in migrations_to_run]
    assert classes_to_run == [NewerVersionMigration, EvenNewerVersionMigration]


@with_fixtures(MigrateFixture)
def test_version_of_migration_not_set_error(migrate_fixture):
    """If the version to which a Migration is applicable is not set, an error is raised."""
    class TestMigration(Migration):
        pass

    egg = ReahlEggStub('my_egg', '1.0', [TestMigration])
    migrate_fixture.orm_control.set_currently_installed_version_for(egg, '0.0')

    with expected(ProgrammerError, test='Migration <class \'reahl\.component_dev\.test_migration\..*TestMigration\'> does not have a version set'):
        migrate_fixture.orm_control.migrate_db([egg])


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
    assert six.text_type(warning.message) == expected_message


@with_fixtures(MigrateFixture)
def test_available_migration_phases(migrate_fixture):
    """These are the phases, and order of the phases in a MigrationRun."""

    migration_run = MigrationRun(migrate_fixture.orm_control, [])
    
    expected_order = ('drop_fk', 'drop_pk', 'pre_alter', 'alter', 'create_pk', 'indexes', 'data', 'create_fk', 'cleanup')
    assert migration_run.changes.phases_in_order == expected_order


@with_fixtures(MigrateFixture)
def test_schema_version_housekeeping(migrate_fixture):
    """The database keeps track of the schema for each installed component. After a migration run
       the currently installed versions are updated.
    """
    
    egg = ReahlEggStub('my_egg', '2.0', [])
    migrate_fixture.orm_control.set_currently_installed_version_for(egg, '1.0')
    migration_run = MigrationRun(migrate_fixture.orm_control, [egg])
    migration_run.execute_migrations()
    assert migrate_fixture.orm_control.schema_version_for(egg) == '2.0'
