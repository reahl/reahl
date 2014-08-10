# Copyright 2011, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.tofu import set_up
from reahl.tofu import tear_down

from reahl.component.config import ReahlSystemConfig
from reahl.component.context import ExecutionContext

from reahl.sqlalchemysupport import metadata, Session, Base

    
class SqlAlchemyTestMixin(object):
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
            self.run_fixture.system_control.rollback()  # The nested one
            self.run_fixture.system_control.rollback()  # The real transaction
            self.run_fixture.system_control.finalise_session() # To nuke the session, and commit (nothing)

    @contextmanager
    def persistent_test_classes(self, *entities):
        try:
            self.create_test_tables(*entities)
            yield
        finally:
            self.destroy_test_tables(*entities)

    def elixir_classes_in(self, entities):
        return [e for e in entities if not issubclass(e, Base)]

    def declarative_classes_in(self, entities):
        return [e for e in entities if issubclass(e, Base)]
        
    def create_test_tables(self, *entities):
        try:
            from elixir import setup_entities
            self.instrument_elixir_classes(self.elixir_classes_in(entities))
        except ImportError:
            pass
        self.system_control.orm_control.instrument_declarative_classes(self.declarative_classes_in(entities))
        metadata.create_all(bind=Session.connection())

    def instrument_elixir_classes(self, entities):
        from elixir import setup_entities
        for entity in entities:
            for cls in entity.mro():
                if '_setup_done' in cls.__dict__:
                    delattr(cls, '_setup_done') 
        setup_entities(entities)

    def destroy_test_tables(self, *entities):
#        Session.flush()
        Session.expunge_all()
        for entity in self.elixir_classes_in(entities):
            entity.table.metadata.remove(entity.table)
        for entity in self.declarative_classes_in(entities):
            entity.__table__.metadata.remove(entity.__table__)
            for k, v in Base._decl_class_registry.items():
                if v is entity:
                    Base._decl_class_registry.pop(k)

    def new_reahlsystem(self, root_egg=None, connection_uri=None, orm_control=None):
        reahlsystem = ReahlSystemConfig()
        reahlsystem.root_egg = root_egg or self.run_fixture.reahlsystem.root_egg
        reahlsystem.connection_uri = connection_uri or self.run_fixture.reahlsystem.connection_uri
        reahlsystem.orm_control = orm_control or self.run_fixture.reahlsystem.orm_control
        reahlsystem.debug = True
        return reahlsystem

    def new_config(self, reahlsystem=None):
        config = self.run_fixture.config
        config.reahlsystem = reahlsystem or self.new_reahlsystem()
        return config

    def new_context(self, config=None, session=None):
        context = ExecutionContext()
        context.set_config( config or self.config )
        context.set_system_control( self.system_control )
        with context:
            context.set_session( session or self.session )
        return context

    @property
    def system_control(self):
        return self.run_fixture.system_control
