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

from sqlalchemy import Column, Integer, String

from reahl.tofu import Fixture, test, vassert

from reahl.sqlalchemysupport import SqlAlchemyControl, QueryAsSequence, Session, Base, metadata
from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyTestMixin

from reahl.domain_dev.fixtures import BasicModelZooMixin
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


class QueryFixture(Fixture, BasicModelZooMixin):
    def new_MyObject(self):
        class MyObject(Base):
            __tablename__ = 'my_object'
            name = Column(String, primary_key=True)
            def __init__(self, name):
                self.name = name
        return MyObject
        
    def new_objects(self):
        objects = [self.MyObject(name='B'), self.MyObject(name='A'), self.MyObject(name='C')]
        for o in objects:
            Session.add(o)
        return objects
        
    def new_query_as_sequence(self):
        return QueryAsSequence(Session.query(self.MyObject))


@test(QueryFixture)
def query_as_sequence(fixture):
    """A QueryAsSequence adapts a sqlalchemy.Query to look like a list."""
    
    with fixture.persistent_test_classes(fixture.MyObject):
        [object1, object2, object3] = fixture.objects

        #can len() items
        vassert( len(fixture.query_as_sequence) == 3 )

        #can find in list
        items = [item for item in Session.query(fixture.MyObject)]
        for i, item in enumerate(items):
            vassert( fixture.query_as_sequence[i] is item )

        #can sort
        fixture.query_as_sequence.sort(key=fixture.MyObject.name)
        sorted_items = [item for item in fixture.query_as_sequence]
        vassert( sorted_items == [object2, object1, object3] )

        #can sort descending
        fixture.query_as_sequence.sort(key=fixture.MyObject.name, reverse=True)
        sorted_items_in_reverse = [item for item in fixture.query_as_sequence]
        vassert( sorted_items_in_reverse == [object3, object1, object2] )


@test(QueryFixture)
def query_as_sequence_last_sort_wins(fixture):
    """Only the last .sort() on a QueryAsSequence has any effect."""

    with fixture.persistent_test_classes(fixture.MyObject):
        [object1, object2, object3] = fixture.objects

        fixture.query_as_sequence.sort(key=fixture.MyObject.name)
        fixture.query_as_sequence.sort(key=fixture.MyObject.name, reverse=True)
        sorted_items = [item for item in fixture.query_as_sequence]
        vassert( sorted_items == [object3, object1, object2] )






