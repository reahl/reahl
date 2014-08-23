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

"""Various bits of support for SQLAlchemy (and declarative/Elixir)."""

from __future__ import unicode_literals
from __future__ import print_function
import six
import weakref
from contextlib import contextmanager
import logging
from collections import Sequence

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import instrument_declarative, declarative_base 
from sqlalchemy.exc import InvalidRequestError
from alembic.migration import MigrationContext
from alembic.operations import Operations

from reahl.component.i18n import Translator
from reahl.component.eggs import ReahlEgg
from reahl.component.dbutils import ORMControl
from reahl.component.context import ExecutionContext, NoContextFound
from reahl.component.modelinterface import Field, IntegerConstraint
from reahl.component.exceptions import ProgrammerError
from reahl.component.config import Configuration

_ = Translator('reahl-sqlalchemysupport')


class SqlAlchemyConfig(Configuration):
    filename = 'sqlalchemy.config.py'
    config_key = 'sqlalchemy'

    def do_injections(self, config):
        if not isinstance(config.reahlsystem.orm_control, SqlAlchemyControl):
            config.reahlsystem.orm_control = SqlAlchemyControl(echo=False)


def reahl_scope():
    try:
        return ExecutionContext.get_context_id()
    except NoContextFound:
        message = 'Database code can normally only be executed by code executed as part of handling a Request.'
        message += ' Such code is then executed within the context of, for example, a database transaction.'
        message += ' Looks like you attempted to execute database code from the wrong place, since no such context'
        message += ' could be found.'
        raise ProgrammerError(message)

Session = scoped_session(sessionmaker(autoflush=True, autocommit=False), scopefunc=reahl_scope) #: A shared SQLAlchemy session, scoped using the current :class:`reahl.component.context.ExecutionContext`
Base = declarative_base(class_registry=weakref.WeakValueDictionary())    #: A Base for using with declarative
metadata = Base.metadata  #: a metadata for use with Elixir, shared with declarative classes using Base 

class QueryAsSequence(Sequence):
    """Used to wrap a SqlAlchemy Query so that it looks like a normal Python :class:`Sequence`."""
    def __init__(self, query):
        self.original_query = query
        self.query = query
    def __len__(self):
        return self.query.count()
    def __getitem__(self, key):
        return self.query[key]
    def sort(self, key=None, reverse=False):
        if key:
            if not reverse:
                self.query = self.original_query.order_by(key)
            else:
                self.query = self.original_query.order_by(key.desc())
        else:
            self.query = self.original_query




class SqlAlchemyControl(ORMControl):
    """An ORMControl for dealing with SQLAlchemy."""
    def __init__(self, echo=False):
        self.echo = echo
        self.engine = None
        
    @contextmanager
    def nested_transaction(self):
        """A context manager for code that needs to run in a nested transaction."""
        Session.flush() # TODO, nuke this with alchemy 0.5.
                        #       see http://www.sqlalchemy.org/docs/05/session.html#using-savepoint
                        #       This does not seem to happen in sqlalchemy < 0.5
                        # Note: this first was necessary due to what seens to be a bug in sqlalchemy 0.4:
                        #       if you delete stuff before starting a savepoint, then rollback
                        #       the savepoint, the delete is flushed to the DB INSIDE the savepoint
                        #       and thus also rolled back.
        transaction = Session.begin_nested()
        try:
            yield transaction
        except Exception as ex:
            commit = getattr(ex, 'commit', False)
            if commit:
                self.commit()
            else:
                self.rollback()
            raise
        else:
            self.commit()

    @contextmanager
    def managed_transaction(self):
        transaction = self.get_or_initiate_transaction()
        try:
            yield transaction
        except:
            self.rollback()
            raise
        else:
            self.commit()
        
    def connect(self):
        """Creates the SQLAlchemy Engine, bind it to the metadata and instrument the persisted classes 
           for the current reahlsystem.root_egg."""
        assert not self.connected
        context = ExecutionContext.get_context()

        config = context.config
        db_api_connection_creator = context.system_control.db_control.get_dbapi_connection_creator()

        create_args = {}
        if db_api_connection_creator:
            create_args['creator']=db_api_connection_creator

        self.engine = create_engine(config.reahlsystem.connection_uri, **create_args)
        self.engine.echo = self.echo
        self.engine.connect()
        metadata.bind = self.engine
        Session.configure(bind=self.engine)

        self.instrument_classes_for(config.reahlsystem.root_egg)

    def instrument_classes_for(self, root_egg):
        all_classes = []
        for i in ReahlEgg.get_all_relevant_interfaces(root_egg):
            all_classes.extend(i.get_persisted_classes_in_order(self)) # So that they get imported  
        
        try:
            from elixir import setup_all
            setup_all()
        except ImportError:
            logging.info('skipping setup of elixir classes, elixir could not be imported')

        declarative_classes = [i for i in all_classes if not getattr(i, 'mapper', None)]
        self.instrument_declarative_classes(declarative_classes)

    def instrument_declarative_classes(self, all_classes):
        registry = {}
        for cls in all_classes:
            try:
#                if not hasattr(cls, 'metadata'):
#                if '_decl_class_registry' not in cls.__dict__:
#                if not hasattr(cls, '__table__'):
#                if getattr(cls, '__table__', None) not in metadata.sorted_tables:
                if not hasattr(cls, '__mapper__'):
                    instrument_declarative(cls, registry, metadata)
                    logging.getLogger(__file__).info( 'Instrumented %s: __tablename__=%s [polymorphic_identity=%s]' % \
                                                          (cls, cls.table, cls.mapper.polymorphic_identity) )
            except InvalidRequestError:
                logging.info('skipping declarative instrumentation of %s' % cls)

    @property
    def connected(self):
        return metadata.bind is not None

    def get_or_initiate_transaction(self):
        assert self.connected
        return Session().transaction

    def set_transaction_and_connection(self, transaction):
        pass
    
    def finalise_session(self):
        nested = Session().transaction.nested
        if nested:   
            # This is necessary to facilitate testing.  When testing, code continually
            # runs in a nested transaction inside a real transaction which will both
            # eventually be rolled back.  This is done so that this method can use the
            # nested state of the transaction to detect that it is called during a test.
            # If called during a test, this method should NOT commit, and it should NOT
            # nnuke the session 
            return

        self.commit()

        context = ExecutionContext.get_context()
        if context.system_control.db_control.is_in_memory:
            Session.expunge_all()
        else:
            Session.remove()
        
    def disconnect(self):
        """Disposes the current SQLAlchemy Engine and .remove() the Session."""
        metadata.bind.dispose()
        metadata.bind = None
        Session.remove()

    def commit(self):
        """Commits the current transaction. Programmers should not need to deal with such transaction
           management explicitly, since the framework already manages transactions itself."""
        # Called on elixir.session (via import in persist), since it knows about the current session fro the current context
        Session.commit()
        
    def rollback(self):
        """Rolls back the current transaction. Programmers should not need to deal with such transaction
           management explicitly, since the framework already manages transactions itself."""
        # Called on elixir.session (via import in persist), since it knows about the current session fro the current context
        Session.rollback()

    def create_db_tables(self, transaction, eggs_in_order):
        metadata.create_all(bind=Session.connection())
        for egg in eggs_in_order:
            self.initialise_schema_version_for(egg)

    def drop_db_tables(self, transaction):
        metadata.drop_all(bind=Session.connection())

    def execute_one(self, sql):
        return Session.execute(sql).fetchone()

    def migrate_db(self, eggs_in_order):
        with Operations.context(MigrationContext.configure(Session.connection())) as op:
            self.op = op
            return super(SqlAlchemyControl, self).migrate_db(eggs_in_order)

    def initialise_schema_version_for(self, egg=None, egg_name=None, egg_version=None):
        assert egg or (egg_name and egg_version)
        if egg:
            egg_name = egg.name
            egg_version = egg.version
        existing_versions = Session.query(SchemaVersion).filter_by(egg_name=egg_name)
        already_created = existing_versions.count() > 0
        assert not already_created, 'The schema for the "%s" egg has already been created previously at version %s' % \
            (egg_name, existing_versions.one().version)
        Session.add(SchemaVersion(version=egg_version, egg_name=egg_name))

    def remove_schema_version_for(self, egg=None, egg_name=None):
        assert egg or egg_name
        if egg:
            egg_name = egg.name
        schema_version_for_egg = Session.query(SchemaVersion).filter_by(egg_name=egg_name).one()
        Session.delete(schema_version_for_egg)

    def schema_version_for(self, egg, default=None):
        existing_versions = Session.query(SchemaVersion).filter_by(egg_name=egg.name)
        number_versions_found = existing_versions.count()
        assert number_versions_found <= 1, 'More than one existing schema version found for egg %s' % egg.name
        if number_versions_found == 1:
            return existing_versions.one().version
        else:
            assert default, 'No existing schema version found for egg %s, and you did not specify a default version' % egg.name
            return default
            

    def update_schema_version_for(self, egg):
        current_version = Session.query(SchemaVersion).filter_by(egg_name=egg.name).one()
        current_version.version = egg.version


class PersistedField(Field):
    """A :class:`reahl.component.modelinterface.Field` which takes an integer as input, and
       yields an instance of `class_to_query` as parsed Python object. The Python object returned
       is selected from the Session. The instance with 'id' equal to the given integer
       is the one returned.
       
       :param class_to_query: The class to query by id from the Session.
       
       (See :class:`reahl.component.modelinterface.Field` for other arguments.)
    """
    def __init__(self, class_to_query, default=None, required=False, required_message=None, label=None, readable=None, writable=None):
        label = label or _('')
        super(PersistedField, self).__init__(default=default, required=required, required_message=required_message, label=label, readable=readable, writable=writable)
        self.class_to_query = class_to_query
        self.add_validation_constraint(IntegerConstraint())

    def parse_input(self, unparsed_input):
        object_id = int(unparsed_input)
        return Session.query(self.class_to_query).filter_by(id=object_id).one()

    def unparse_input(self, parsed_value):
        instance = parsed_value
        if instance:
            return six.text_type(instance.id)
        return ''


class SchemaVersion(Base):
    __tablename__ = 'reahl_schema_version'
    id = Column(Integer, primary_key=True)
    version =  Column(String(50))
    egg_name = Column(String)




