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


from contextlib import contextmanager

from reahl.tofu import Fixture, test, vassert

from reahl.component.dbutils import ORMControl
from reahl.component.eggs import ReahlEgg
from reahl.component.migration import Migration

# current schema version is saved when tables are creates
# when you run upgrade, only the relevant migrations are run, in order - 2 phases, then new schema version is notes



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


class MigrateFixture(Fixture):
    def new_orm_control(self):
        return ORMControlStub()



@test(MigrateFixture)
def upgrading(fixture):

    fixture.ran = []
    class TestMigration(Migration):
        def upgrade(self):
            fixture.ran.append((self.__class__, u'upgrade'))
        def upgrade_cleanup(self):
            fixture.ran.append((self.__class__, u'cleanup'))
    
    class MigrateOneA(TestMigration):
        version = u'0.1'
    class MigrateOneB(TestMigration):
        version = u'0.1'
    class MigrateTwoA(TestMigration):
        version = u'0.1'
    class MigrateTwoB(TestMigration):
        version = u'0.1'
    
    eggs = [ReahlEggStub(u'one', u'0.0', [MigrateOneA, MigrateOneB]), 
            ReahlEggStub(u'two', u'0.0', [MigrateTwoA, MigrateTwoB])]
    for egg in eggs:
        fixture.orm_control.initialise_schema_version_for(egg)
    for egg in eggs:
        egg._version = u'0.1'
    fixture.orm_control.migrate_db(eggs)

    expected_migrations = [(MigrateTwoA, u'upgrade'), (MigrateTwoB, u'upgrade'), 
                           (MigrateOneA, u'upgrade'), (MigrateOneB, u'upgrade'), 
                           (MigrateOneA, u'cleanup'), (MigrateOneB, u'cleanup'), 
                           (MigrateTwoA, u'cleanup'), (MigrateTwoB, u'cleanup')]
    vassert ( fixture.ran == expected_migrations )

    #case: running it again does not trigger running the upgrade again if the version did not change
    fixture.ran = []
    fixture.orm_control.migrate_db(eggs)
    vassert( fixture.ran == [] )




