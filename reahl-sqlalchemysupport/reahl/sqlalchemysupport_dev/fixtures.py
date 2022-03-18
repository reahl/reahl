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


from contextlib import contextmanager

from reahl.tofu import set_up, tear_down, Fixture, uses
from reahl.sqlalchemysupport import metadata, Session

from reahl.dev.fixtures import ReahlSystemFixture


@uses(reahl_system_fixture=ReahlSystemFixture)
class SqlAlchemyFixture(Fixture):
    """SqlAlchemyFixture ensures that a transaction is started before each test run, and
    rolled back after each test so as to leave the database unchanged
    between tests. It also contains a handy method
    :meth:`~reahl.sqlalchemysupport_dev.fixtures.SqlAlchemyFixture.persistent_test_classes`
    that can be used to add persistent classes to your database schema
    just for purposes of the current test.

    """
    commit = False

    @set_up
    def start_transaction(self):
        if not self.commit:
            # The tests run in a nested transaction inside a real transaction, and both are rolled back
            # This is done because finalise_session (real code) is run as part of the test, and it
            # checks for the nested transaction and behaves differently to make testing possible.
            # Session.begin() - this happens implicitly
            Session.begin_nested()

    @tear_down
    def finalise_transaction(self):
        if not self.commit:
            self.reahl_system_fixture.system_control.rollback()  # The nested one
            self.reahl_system_fixture.system_control.rollback()  # The real transaction
            self.reahl_system_fixture.system_control.finalise_session()  # To nuke the session, and commit (possibly nothing)
        else:
            self.reahl_system_fixture.system_control.commit()  # The nested one
            self.reahl_system_fixture.system_control.commit()  # The real transaction

    @contextmanager
    def persistent_test_classes(self, *entities):
        """A context manager that creates the tables needed for the entities passed to it, and which sets
        the necessary SqlAlchemy wiring up for thos entities to work. The tables are destroyed again
        after the context is exited.

        This is useful for having persistent classes that may even need their own tables in the database
        but which should stay part of test code only, and are thus not listed in the <persisted> section
        of any egg.
        """
        try:
            self.create_test_tables()
            yield
        finally:
            self.destroy_test_tables(*entities)

    def create_test_tables(self):
        metadata.create_all(bind=Session.connection())

    def destroy_test_tables(self, *entities):
        # Session.flush()
        Session.expunge_all()
        for entity in entities:
            if hasattr(entity, '__table__'):
                entity.__table__.metadata.remove(entity.__table__)
                if hasattr(entity, 'registry'):
                    if entity.__name__ in entity.registry._class_registry:
                        del entity.registry._class_registry[entity.__name__]
                else:
                    #for older versions of SqlAlchemy like 1.2,1.3
                    if entity.__name__ in entity._decl_class_registry:
                        del entity._decl_class_registry[entity.__name__]


