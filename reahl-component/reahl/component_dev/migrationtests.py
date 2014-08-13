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
from contextlib import contextmanager
import warnings

from reahl.tofu import Fixture, test, vassert

from reahl.component.dbutils import ORMControl
from reahl.component.eggs import ReahlEgg
from reahl.component.migration import Migration

warnings.warn('TODO: these tests need neatening, some facts to test are in comments below this warning')
#
# current schema version is saved when tables are created
# when you run upgrade, only the relevant migrations are run, in order - 2 phases, then new schema version is noted
# when a new egg appears in the dependency tree that was not installed before, its tables are created & version is noted
# when an old egg disappears from the dependency tree???


class stubclass(object):
    def __init__(self, cls):
        pass
    def __call__(self, cls):
        warnings.warn('This needs to become stubble.stubclass, but stubble does not deal with this scenario - it needs to be fixed')
        return cls

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
    def has_schema_version(self, egg):
        return egg.name in self.versions
    def create_schema_for(self, transaction, new_eggs):
        pass

class MigrateFixture(Fixture):
    def new_orm_control(self):
        return ORMControlStub()



@test(MigrateFixture)
def upgrading(fixture):

    fixture.ran = []
    class TestMigration(Migration):
        def upgrade(self):
            fixture.ran.append((self.__class__, 'upgrade'))
        def upgrade_cleanup(self):
            fixture.ran.append((self.__class__, 'cleanup'))
    
    class MigrateOneA(TestMigration):
        version = '0.1'
    class MigrateOneB(TestMigration):
        version = '0.1'
    class MigrateTwoA(TestMigration):
        version = '0.1'
    class MigrateTwoB(TestMigration):
        version = '0.1'
    
    eggs = [ReahlEggStub('one', '0.0', [MigrateOneA, MigrateOneB]), 
            ReahlEggStub('two', '0.0', [MigrateTwoA, MigrateTwoB])]
    for egg in eggs:
        fixture.orm_control.initialise_schema_version_for(egg)
    for egg in eggs:
        egg._version = '0.1'
    fixture.orm_control.migrate_db(eggs)

    expected_migrations = [(MigrateTwoA, 'upgrade'), (MigrateTwoB, 'upgrade'), 
                           (MigrateOneA, 'upgrade'), (MigrateOneB, 'upgrade'), 
                           (MigrateOneA, 'cleanup'), (MigrateOneB, 'cleanup'), 
                           (MigrateTwoA, 'cleanup'), (MigrateTwoB, 'cleanup')]
    vassert ( fixture.ran == expected_migrations )

    #case: running it again does not trigger running the upgrade again if the version did not change
    fixture.ran = []
    fixture.orm_control.migrate_db(eggs)
    vassert( fixture.ran == [] )




