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



from sqlalchemy import Column, String

from reahl.tofu import Fixture, uses
from reahl.tofu.pytestsupport import with_fixtures
from reahl.sqlalchemysupport import SqlAlchemyControl, QueryAsSequence, Session, Base

from reahl.dev.fixtures import ReahlSystemFixture
from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture

from reahl.component_dev.test_migration import ReahlEggStub


@with_fixtures(ReahlSystemFixture)
def test_egg_schema_version_changes(reahl_system_fixture):
    orm_control = SqlAlchemyControl()

    old_version_egg = ReahlEggStub('anegg', {'0.0': []})

    orm_control.initialise_schema_version_for(old_version_egg)
    current_version = orm_control.schema_version_for(old_version_egg)
    assert current_version == str(old_version_egg.installed_version.version_number)

    new_version_egg = ReahlEggStub('anegg', {'0.1': []})
    orm_control.set_schema_version_for(new_version_egg.installed_version)
    current_version = orm_control.schema_version_for(new_version_egg)
    assert current_version == str(new_version_egg.installed_version.version_number)
    assert not current_version == str(old_version_egg.installed_version.version_number)
    current_version = orm_control.schema_version_for(old_version_egg)
    assert current_version == str(new_version_egg.installed_version.version_number)


@with_fixtures(ReahlSystemFixture)
def test_egg_schema_version_init(reahl_system_fixture):
    orm_control = SqlAlchemyControl()

    egg = ReahlEggStub('initegg', {'0.0': []})
    orm_control.create_db_tables(None, [egg])
    current_version = orm_control.schema_version_for(egg)
    assert current_version == str(egg.installed_version.version_number)


@uses(sql_alchemy_fixture=SqlAlchemyFixture)
class QueryFixture(Fixture):

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


@with_fixtures(SqlAlchemyFixture, QueryFixture)
def test_query_as_sequence(sql_alchemy_fixture, query_fixture):
    """A QueryAsSequence adapts a sqlalchemy.Query to look like a list."""

    fixture = query_fixture
    with sql_alchemy_fixture.persistent_test_classes(fixture.MyObject):
        [object1, object2, object3] = fixture.objects

        # can len() items
        assert len(fixture.query_as_sequence) == 3

        # can find in list
        items = [item for item in Session.query(fixture.MyObject)]
        for i, item in enumerate(items):
            assert fixture.query_as_sequence[i] is item

        # can sort
        fixture.query_as_sequence.sort(key=fixture.MyObject.name)
        sorted_items = [item for item in fixture.query_as_sequence]
        assert sorted_items == [object2, object1, object3]

        # can sort descending
        fixture.query_as_sequence.sort(key=fixture.MyObject.name, reverse=True)
        sorted_items_in_reverse = [item for item in fixture.query_as_sequence]
        assert sorted_items_in_reverse == [object3, object1, object2]

        # can slice
        natural_ordered_items = [item for item in fixture.query_as_sequence]
        [object1, object2, object3] = fixture.query_as_sequence[:]
        assert[object1, object2, object3] == natural_ordered_items

        # can slice some more
        [sliced_item] = fixture.query_as_sequence[1:2]
        assert sliced_item == natural_ordered_items[1]


@with_fixtures(SqlAlchemyFixture, QueryFixture)
def test_query_as_sequence_last_sort_wins(sql_alchemy_fixture, query_fixture):
    """Only the last .sort() on a QueryAsSequence has any effect."""

    fixture = query_fixture
    with sql_alchemy_fixture.persistent_test_classes(fixture.MyObject):
        [object1, object2, object3] = fixture.objects

        fixture.query_as_sequence.sort(key=fixture.MyObject.name)
        fixture.query_as_sequence.sort(key=fixture.MyObject.name, reverse=True)
        sorted_items = [item for item in fixture.query_as_sequence]
        assert sorted_items == [object3, object1, object2]


@with_fixtures(SqlAlchemyFixture, QueryFixture)
def test_query_as_sequence_chained_sorts(sql_alchemy_fixture, query_fixture):
    """A QueryAsSequence constructed with a query that already has an order_by clause,
       should be able to chain additional sort(order_by) requirements"""

    fixture = query_fixture
    with sql_alchemy_fixture.persistent_test_classes(fixture.MyObject):
        [object1, object2, object3] = fixture.objects

        native_query_with_sort = Session.query(fixture.MyObject).order_by(fixture.MyObject.name)
        query_as_sequence = QueryAsSequence(native_query_with_sort)

        # another sort(order_by) requirement
        query_as_sequence.sort(key=fixture.MyObject.name, reverse=True)
        sorted_items = [item for item in query_as_sequence]
        assert sorted_items == [object3, object1, object2]

