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

"""Various bits of support for SQLAlchemy and declarative."""

from __future__ import print_function, unicode_literals, absolute_import, division

from abc import ABCMeta
import six
import weakref
from contextlib import contextmanager
import logging

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, scoped_session, relationship
from sqlalchemy.ext.declarative import instrument_declarative, declarative_base, DeclarativeMeta
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy import Column, Integer, ForeignKey
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.autogenerate import compare_metadata

from reahl.component.i18n import Catalogue
from reahl.component.eggs import ReahlEgg
from reahl.component.dbutils import ORMControl
from reahl.component.context import ExecutionContext, NoContextFound
from reahl.component.modelinterface import Field, IntegerConstraint
from reahl.component.exceptions import ProgrammerError
from reahl.component.config import Configuration

_ = Catalogue('reahl-sqlalchemysupport')


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


naming_convention = {
  'ix': 'ix_%(column_0_label)s',
  'uq': 'uq_%(table_name)s_%(column_0_name)s',
#  'ck': 'ck_%(table_name)s_%(constraint_name)s',
  'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
  'pk': 'pk_%(table_name)s'
}

def fk_name(table_name, column_name, other_table_name):
    """Returns the name that will be used in the database for a foreign key, given:

       :arg table_name: The name of the table from which the foreign key points.
       :arg column_name: The name of the column in which the foreign key pointer is stored.
       :arg other_table_name: The name of the table to which this foreign key points.
    """
    return 'fk_%s_%s_%s' % (table_name, column_name, other_table_name)

def pk_name(table_name):
    """Returns the name that will be used in the database for a primary key, given:

       :arg table_name: The name of the table to which the primary key belongs.
    """
    return 'pk_%s' % table_name

def ix_name(table_name, column_name):
    """Returns the name that will be used in the database for an index key, given:

       :arg table_name: The name of the table to which the index belongs.
       :arg column_name: The name of the column that is indexed.
    """
    return 'ix_%s_%s' % (table_name, column_name)


Session = scoped_session(sessionmaker(autoflush=True, autocommit=False), scopefunc=reahl_scope) #: A shared SQLAlchemy session, scoped using the current :class:`reahl.component.context.ExecutionContext`
metadata = MetaData(naming_convention=naming_convention)  #: a metadata for use with other SqlAlchemy tables, shared with declarative classes using Base


class DeclarativeABCMeta(DeclarativeMeta, ABCMeta):
    """ Prevent metaclass conflict in subclasses that want multiply inherit from
    ancestors that have ABCMeta as metaclass """
    pass


Base = declarative_base(class_registry=weakref.WeakValueDictionary(), metadata=metadata, metaclass=DeclarativeABCMeta)    #: A Base for using with declarative


class QueryAsSequence(object):
    """Used to adapt a SqlAlchemy Query to behave like a normal
      `Python sequence type <https://docs.python.org/3/glossary.html#term-sequence>`_.

      QueryAsSequence only implements a few useful methods, not the full
      :class:`collections.abc.Sequence` protocol.
      
      :param query: The :class:`Query` object to adapt.
      :keyword map_function: An optional function to map each instance returned (similar to `function` in the standard :meth:`map` function).
    """
    def __init__(self, query, map_function=lambda instance: instance):
        self.original_query = query
        self.query = query
        self.map_function = map_function

    def __len__(self):
        """Returns the number of items that would be returned by executing the query."""
        return self.query.count()

    def __getitem__(self, key):
        """Returns the items requested by executing an modifed query representing only the requested slice."""
        if isinstance(key, slice):
            return [self.map_function(i) for i in self.query[key]]
        else:
            return self.map_function(self.query[key])

    def sort(self, key=None, reverse=False):
        """Modifies the query to be ordered as requested.

        :keyword key: A SqlAlchemy `order_by criterion <http://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.order_by>`_ to be used for sorting.
        :keyword reverse: If True, use descending order.
        """
        if key:
            if reverse:
                self.query = self.original_query.order_by(None).order_by(key.desc())
            else:
                self.query = self.original_query.order_by(None).order_by(key)
        else:
            self.query = self.original_query



def session_scoped(cls):
    """A decorator for making a class session-scoped.

       It adds a relationship to the user_session on any decorated Entity and ensures that
       the Entity will be deleted if the UserSession is deleted.

       Two classmethods are also added to the decorated class:


       **classmethod** for_session(cls, user_session, \*\*kwargs)

          This method assumes that there should be only one instance of the Entity class
          for a given UserSession. When called, it will return that instance if it exists.
          If it does not exist, it will construct the instance. The kwargs supplied will be
          passed along when creating the instance.

       **classmethod** for_current_session(cls, \*\*kwargs)

          Works the same as for_session() except that you need not pass a UserSession, the
          current UserSession is assumed.
    """
    cls.user_session_id = Column(Integer, ForeignKey('usersession.id', ondelete='CASCADE'), index=True)
    cls.user_session = relationship('UserSession', cascade='all, delete')

    @classmethod
    def for_current_session(cls, **kwargs):
        user_session = ExecutionContext.get_context().session
        return cls.for_session(user_session, **kwargs)
    cls.for_current_session = for_current_session

    @classmethod
    def for_session(cls, user_session, **kwargs):
        found = Session.query(cls).filter_by(user_session=user_session)
        if found.count() >= 1:
            return found.one()
        instance = cls(user_session=user_session, **kwargs)
        Session.add(instance)
        return instance
    cls.for_session = for_session

    return cls


class SqlAlchemyControl(ORMControl):
    """An ORMControl for dealing with SQLAlchemy."""
    def __init__(self, echo=False):
        self.echo = echo
        self.engine = None
        
    @contextmanager
    def nested_transaction(self):
        """A context manager for code that needs to run in a nested transaction."""
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
            all_classes.extend(i.get_persisted_classes_in_order()) # So that they get imported
        
        declarative_classes = [i for i in all_classes if issubclass(i, Base)]
        self.instrument_declarative_classes(declarative_classes)

    def instrument_declarative_classes(self, all_classes):
        registry = {}
        for cls in all_classes:
            try:
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
        assert self.connected
        metadata.bind.dispose()
        metadata.bind = None
        Session.remove()

    def commit(self):
        """Commits the current transaction. Programmers should not need to deal with such transaction
           management explicitly, since the framework already manages transactions itself."""
        Session.commit()
        
    def rollback(self):
        """Rolls back the current transaction. Programmers should not need to deal with such transaction
           management explicitly, since the framework already manages transactions itself."""
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

    def diff_db(self):
        return compare_metadata(MigrationContext.configure(Session.connection()), metadata)

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
        current_versions = Session.query(SchemaVersion).filter_by(egg_name=egg.name)
        assert current_versions.count() == 1, 'Found %s versions for %s, expected exactly 1' % (current_versions.count(), egg.name)
        current_version = current_versions.one()
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
    egg_name = Column(String(80))





