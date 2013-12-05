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



from reahl.tofu import Fixture, test, vassert

from reahl.sqlalchemysupport import SqlAlchemyControl
from reahl.component_dev.migrationtests import ReahlEggStub



@test(Fixture)
def egg_schema_version_changes(fixture):
    orm_control = SqlAlchemyControl()

    old_version_egg = ReahlEggStub('anegg', '0.0', [])
    
    orm_control.initialise_schema_version_for(old_version_egg)
    current_version = orm_control.schema_version_for(old_version_egg)
    vassert( current_version == old_version_egg.version )
    
    new_version_egg = ReahlEggStub('anegg', '0.1', [])
    orm_control.update_schema_version_for(new_version_egg)
    current_version = orm_control.schema_version_for(new_version_egg)
    vassert( current_version == new_version_egg.version )
    vassert( not current_version == old_version_egg.version )
    current_version = orm_control.schema_version_for(old_version_egg)
    vassert( current_version == new_version_egg.version )


@test(Fixture)
def egg_schema_version_init(fixture):
    orm_control = SqlAlchemyControl()

    egg = ReahlEggStub('initegg', '0.0', [])
    orm_control.create_db_tables(None, [egg])
    current_version = orm_control.schema_version_for(egg)
    vassert( current_version == egg.version )

