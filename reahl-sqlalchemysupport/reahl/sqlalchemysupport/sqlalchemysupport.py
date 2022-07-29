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

"""Various bits of support for SQLAlchemy and declarative.

Run 'reahl componentinfo reahl-sqlalchemysupport' for configuration information.
"""


from abc import ABCMeta
import weakref
from contextlib import contextmanager
import logging
import pprint

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, scoped_session, relationship
from sqlalchemy.ext.declarative import instrument_declarative, declarative_base, DeclarativeMeta
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy import Column, Integer, ForeignKey
from alembic.runtime.migration import MigrationContext
from alembic.operations import Operations
from alembic.autogenerate import produce_migrations, render_python_code

from reahl.component.i18n import Catalogue
from reahl.component.eggs import ReahlEgg
from reahl.component.dbutils import ORMControl
from reahl.component.context import ExecutionContext, NoContextFound
from reahl.component.modelinterface import Field, IntegerConstraint
from reahl.component.exceptions import ProgrammerError, DomainException
from reahl.component.config import Configuration, ConfigSetting

_ = Catalogue('reahl-sqlalchemysupport')


class SqlAlchemyConfig(Configuration):
    filename = 'sqlalchemy.config.py'
    config_key = 'sqlalchemy'

    engine_create_args = ConfigSetting(description='Extra create arguments passed to sqlalchemy.create_engine()',
                                       default={'pool_pre_ping': True})

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


class QueryAsSequence:
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
    cls.user_session = relationship('UserSession')

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


class TransactionVeto:
    """An object that can be used to force the transaction to be committed or not.

    .. versionadded: 5.0

    """
    should_commit = None  #: Set this to True to force a commit or False to force a rollback
    @property
    def has_voted(self):
        return self.should_commit is not None


class SqlAlchemyControl(ORMControl):
    """An ORMControl for dealing with SQLAlchemy."""
    def __init__(self, echo=False):
        self.echo = echo
        self.engine = None

    @contextmanager
    def nested_transaction(self):
        """A context manager for code that needs to run in a nested transaction.
        
        .. versionchanged:: 5.0
           Changed to yield a TransactionVeto which can be used to override when the transaction will be committed or not.
        """
        transaction = Session.begin_nested()
        transaction_veto = TransactionVeto()
        try:
            yield transaction_veto
        except Exception as ex:
            commit = getattr(ex, 'commit', False)
            raise
        else:
            commit = True
        finally:
            if transaction_veto.has_voted:
                commit = transaction_veto.should_commit
            if transaction.is_active:# some sqlalchemy exceptions automatically rollback the current transaction
                if commit:
                    transaction.commit()
                else:
                    transaction.rollback()

    @contextmanager
    def managed_transaction(self):
        transaction = self.get_or_initiate_transaction()
        try:
            yield transaction
        except:
            if transaction.is_active: # some sqlalchemy exceptions automatically rollback the current transaction
                transaction.rollback()
            raise
        else:
            transaction.commit()
        
    def connect(self, auto_commit=False):
        """Creates the SQLAlchemy Engine, bind it to the metadata and instrument the persisted classes 
           for the current reahlsystem.root_egg."""
        assert not self.connected
        context = ExecutionContext.get_context()

        config = context.config
        db_api_connection_creator = context.system_control.db_control.get_dbapi_connection_creator()
        
        create_args = config.sqlalchemy.engine_create_args.copy()
        if auto_commit:
            create_args['isolation_level'] = 'AUTOCOMMIT'
            create_args['execution_options'] = {'isolation_level': 'AUTOCOMMIT'}
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
    
    def finalise_session(self):
        nested = Session().transaction.nested
        if nested:   
            # This is necessary to facilitate testing.  When testing, code continually
            # runs in a nested transaction inside a real transaction which will both
            # eventually be rolled back.  This is done so that this method can use the
            # nested state of the transaction to detect that it is called during a test.
            # If called during a test, this method should NOT commit, and it should NOT
            # nuke the session
            Session.flush()
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

    def migrate_db(self, eggs_in_order, explain=False):
        opts = {'target_metadata': metadata}
        with Operations.context(MigrationContext.configure(connection=Session.connection(), opts=opts)) as op:
            self.op = op
            return super().migrate_db(eggs_in_order, explain=explain)

    def prune_schemas_to_only(self, live_versions):
        opts = {'target_metadata': metadata}
        with Operations.context(MigrationContext.configure(connection=Session.connection(), opts=opts)) as op:
            self.op = op
            to_remove = [i for i in self.get_outstanding_migrations().upgrade_ops.as_diffs() if i[0].startswith('remove_')]
            tables_to_drop = []
            unhandled = []
            for migration in to_remove:
                name = migration[0]
                if name == 'remove_table':
                    table = migration[1]
                    tables_to_drop.append(table)
                    for foreign_key in table.foreign_key_constraints:
                        op.drop_constraint(foreign_key.name, table.name)
                elif name == 'remove_index':
                    op.drop_index(migration[1].name)
                else:
                    unhandled.append(migration)
            for table in tables_to_drop:
                op.drop_table(table.name)

            if unhandled:
                print('These migrations have not been automatically done, please effect them by other means:')
                for migration in unhandled:
                    print(migration)

        installed_version_names = [version.name for version in live_versions]
        for created_schema_version in Session.query(SchemaVersion).all():
            if created_schema_version.egg_name not in installed_version_names:
                Session.delete(created_schema_version)

    def get_outstanding_migrations(self):
        return produce_migrations(MigrationContext.configure(connection=Session.connection()), metadata)
        
    def diff_db(self, output_sql=False):
        migrations = self.get_outstanding_migrations()
        if output_sql:
            commented_source_code = render_python_code(migrations.upgrade_ops, alembic_module_prefix='op2.', sqlalchemy_module_prefix="sqlalchemy.")
            uncommented_source_code = [i.strip() for i in commented_source_code.split('\n') if not i.strip().startswith('#')]
            source_code = '\n'.join(['import sqlalchemy']+uncommented_source_code)
            opts = {'as_sql': output_sql, 'target_metadata': metadata}
            with Operations.context(MigrationContext.configure(connection=Session.connection(), opts=opts)) as op2:
                exec(source_code, globals(), locals())
            return uncommented_source_code
        else:
            migrations_required = migrations.upgrade_ops.as_diffs()
            if migrations_required:
                pprint.pprint(migrations_required, indent=2, width=20)
            return migrations_required

    def initialise_schema_version_for(self, egg=None, egg_name=None, egg_version=None):
        assert egg or (egg_name and egg_version)
        if egg:
            egg_name = egg.name
            egg_version = str(egg.installed_version.version_number)
        existing_versions = Session.query(SchemaVersion).filter_by(egg_name=egg_name)
        already_created = existing_versions.count() > 0
        if already_created:
            raise DomainException(message='The schema for the "%s" egg has already been created previously at version %s' % \
                                  (egg_name, existing_versions.one().version))
        Session.add(SchemaVersion(version=egg_version, egg_name=egg_name))

    def remove_schema_version_for(self, egg=None, egg_name=None, fail_if_not_found=True):
        assert egg or egg_name
        if egg:
            egg_name = egg.name
        versions_to_delete = Session.query(SchemaVersion).filter_by(egg_name=egg_name)
        if fail_if_not_found or versions_to_delete.count() > 0:
            schema_version_for_egg = versions_to_delete.one()
            Session.delete(schema_version_for_egg)

    def schema_version_for(self, egg, default=None):
        if not Session.get_bind().has_table(SchemaVersion.__tablename__):
            return default

        existing_versions = Session.query(SchemaVersion).filter_by(egg_name=egg.name)
        number_versions_found = existing_versions.count()
        assert number_versions_found <= 1, 'More than one existing schema version found for egg %s' % egg.name
        if number_versions_found == 1:
            return existing_versions.one().version
        else:
            assert default, 'No existing schema version found for egg %s, and you did not specify a default version' % egg.name
            return default

    def set_schema_version_for(self, version):
        current_versions = Session.query(SchemaVersion).filter_by(egg_name=version.name)
        versions_count = current_versions.count()
        assert versions_count <= 1, 'Expected 0 or 1 SchemaVersions for %s, found %s' % (version.name, versions_count)
        if versions_count < 1:
            Session.add(SchemaVersion(version=str(version.version_number), egg_name=version.name))
        elif versions_count == 1:
            current_version = current_versions.one()
            current_version.version = str(version.version_number)

    def assert_dialect(self, migration, *supported_dialects):
        dialect_name = self.engine.dialect.name
        if dialect_name not in supported_dialects:
            raise DomainException(message='Migration %s does not support the database dialect you are running on (%s), only one of %s' % (migration, dialect_name, supported_dialects))


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
        super().__init__(default=default, required=required, required_message=required_message, label=label, readable=readable, writable=writable)
        self.class_to_query = class_to_query
        self.add_validation_constraint(IntegerConstraint())

    def parse_input(self, unparsed_input):
        object_id = int(unparsed_input)
        return Session.query(self.class_to_query).filter_by(id=object_id).one()

    def unparse_input(self, parsed_value):
        instance = parsed_value
        if instance:
            return str(instance.id)
        return ''


class SchemaVersion(Base):
    __tablename__ = 'reahl_schema_version'
    id = Column(Integer, primary_key=True)
    version = Column(String(50))
    egg_name = Column(String(80))


