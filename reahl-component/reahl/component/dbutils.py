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

"""Utilities to manipulate underlying databases - sometimes via an ORM tool.

.. uml:: ../../../reahl-component/reahl/component_dev/database_components.puml

"""


import re
from contextlib import contextmanager
import urllib.parse

import pkg_resources 

from reahl.component.exceptions import ProgrammerError
from reahl.component.eggs import ReahlEgg
from reahl.component.migration import MigrationPlan


class CouldNotFindDatabaseControlException(Exception):
    def __init__(self, url):
        super().__init__(url)
        self.url = url


class SystemControl:
    """Used to control all aspects relating to the underlying database as per the configuration of the system.

    Any Reahl system is assumed to have a database backing it. Our
    dealings with a databases vary in two dimentions. The first of
    these dimantions is the different database backends that can be
    used. How one controls the backend itself (such as creating users,
    dropping databases, etc) differs depending on the particular
    backend used.

    Regardless of which backend is used, one can also use an ORM layer
    on top of the database. Things like instrumenting classes,
    creating database tables of dealing with database transactions are
    dependent on the ORM implementation used.

    The SystemControl allows you to control all these aspects of the
    database. It does so by delegating methods relating to the
    database backend to a :class:`DatabaseControl` of the correct
    kind, and by delegating the methods relating to ORM operations to
    an :class:`ORMControl` of the correct kind.

    The type of :class:`DatabaseControl` used is inferred from the
    configured `reahlsystem.connection_uri` in `reahl.config.py`. The
    actual :class:`ORMControl` used is configured as the
    `reahlsystem.orm_control` in `reahl.config.py`.

    A programmer should use the SystemControl of the system as
    programmatic interface to the database without regard for which
    technology-specific classes it delegates to in order to do its
    work.

    """
    def __init__(self, config):
        self.config = config
        self.connection_uri = self.config.reahlsystem.connection_uri
        self.db_control = self.db_control_for_uri(self.connection_uri)
        self.orm_control = self.config.reahlsystem.orm_control
        self.orm_control.system_control = self

    def connect(self, auto_commit=False):
        """Connects and logs into the database."""
        self.orm_control.connect(auto_commit=auto_commit)
        if self.db_control.is_in_memory:
            self.create_db_tables()

    @contextmanager
    def auto_connected(self):
        if self.connected:
            yield

        self.connect()
        try:
            yield
        finally:
            self.disconnect()

    @property
    def connected(self):
        """Returns True if the system is currently connected to the database."""
        return self.orm_control.connected

    def disconnect(self):
        """Disconnects from the database."""
        self.orm_control.disconnect()

    def managed_transaction(self):
        return self.orm_control.managed_transaction()

    def nested_transaction(self):
        return self.orm_control.nested_transaction()

    def finalise_session(self):
        self.orm_control.finalise_session()

    def commit(self):
        """Commits the database."""
        self.orm_control.commit()

    def rollback(self):
        """Rolls back the database."""
        self.orm_control.rollback()

    def db_control_for_uri(self, url):
        for i in self.config.reahlsystem.databasecontrols:
            if i.matches_uri(url):
                return i(url, self.config)
        raise CouldNotFindDatabaseControlException(url)

    def __getattr__(self, name):
        return getattr(self.db_control, name)

    def size_database(self):
        """Returns the current size of the database."""
        with self.orm_control.managed_transaction():
            return self.db_control.size_database(self.orm_control)

    def create_db_tables(self):
        """Creates the underlying database schema."""
        eggs_in_order = ReahlEgg.get_all_relevant_interfaces(self.config.reahlsystem.root_egg)
        with self.orm_control.managed_transaction() as transaction:
            return self.orm_control.create_db_tables(transaction, eggs_in_order)

    def drop_db_tables(self):
        """Removes the underlying database schema."""
        with self.orm_control.managed_transaction() as transaction:
            return self.orm_control.drop_db_tables(transaction)

    def initialise_database(self):
        """Ensures a new clean database exists, with a schema created. This drops an existing database if one is present."""
        self.drop_database()
        self.create_database()
        self.connect()
        try:
            self.create_db_tables()
        finally:
            self.disconnect()

    def migrate_db(self, explain=False):
        """Runs the database migrations relevant to the current system."""
        self.orm_control.migrate_db(ReahlEgg.interface_for(pkg_resources.get_distribution(self.config.reahlsystem.root_egg)), explain=explain)
        return 0

    def diff_db(self, output_sql=False):
        """Computes the changes in schema between the current database and what the current system expects."""
        return self.orm_control.diff_db(output_sql=output_sql)

    def do_daily_maintenance(self):
        """Runs the all the scheduled jobs relevant to the current system."""
        with self.orm_control.managed_transaction() as transaction:
            ReahlEgg.do_daily_maintenance_for_egg(self.config.reahlsystem.root_egg)

    def create_db_user(self, super_user_name=None, create_with_password=True):
        """Creates the database user."""
        return self.db_control.create_db_user(super_user_name=super_user_name, create_with_password=create_with_password)

    def drop_db_user(self, super_user_name=None):
        """Drops the database user."""
        return self.db_control.drop_db_user(super_user_name=super_user_name)
    
    def drop_database(self, super_user_name=None):
        """Drops the database (if it exists)."""
        return self.db_control.drop_database(super_user_name=super_user_name)
    
    def create_database(self, super_user_name=None):
        """Creates the database."""
        return self.db_control.create_database(super_user_name=super_user_name)
    
    def backup_database(self, directory, super_user_name=None):
        """Backs up the database."""
        return self.db_control.backup_database(directory, super_user_name=super_user_name)
    
    def backup_all_databases(self, directory, super_user_name=None):
        """Backs up all databases on the current machine."""
        return self.db_control.backup_all_databases(directory, super_user_name=super_user_name)
    
    def restore_database(self, filename, super_user_name=None):
        """Restores a databases from the given backup."""
        return self.db_control.restore_database(filename, super_user_name=super_user_name)
    
    def restore_all_databases(self, filename, super_user_name=None):
        """Restores all databases from the given backup."""
        return self.db_control.restore_all_databases(filename, super_user_name=super_user_name)

    

class DatabaseControl:
    """An interface to the underlying database backend technology used. 

    This class has the responsibility to manage the low-level backend
    operations, such as creating/dropping databases or users.

    In order to support a new type of database, subclass this class
    and implement its methods appropriately for that backend.

    Don't use this class directly, rather call the methods on the
    :class:`SystemControl`. It delegates to the appropriate underlying
    :class:`ORMControl` and/or :class:`DatabaseControl` as
    appropriate.
    """
    control_matching_regex = r'^$'
    def __init__(self, url, config):
        self.config = config
        self.connection_uri = url
        uri_parts = urllib.parse.urlparse(url)
        self.user_name = self.unquote(uri_parts.username)
        self.password = self.unquote(uri_parts.password)
        self.host = self.unquote(uri_parts.hostname)
        self.port = uri_parts.port
        self.database_name = self.unquote(uri_parts.path[1:] if uri_parts.path.startswith('/') else uri_parts.path)
        if not self.database_name:
            raise ProgrammerError('Please specify a database name in reahlsystem.connection_uri')

    def unquote(self, value):
        return urllib.parse.unquote(value) if value else None

    def get_dbapi_connection_creator(self):
        return None

    @property
    def is_in_memory(self):
        return False

    @classmethod
    def matches_uri(cls, url):
        return re.match(cls.control_matching_regex, url) is not None

    def create_db_user(self, super_user_name=None, create_with_password=True):
        assert self.user_name, 'No user name in URI %s' % self.connection_uri

    def drop_db_user(self, super_user_name=None):
        assert self.user_name, 'No user name in URI %s' % self.connection_uri

    
class NullDatabaseControl(DatabaseControl):
    """A stubbed-out :class:`DatabaseControl` for systems that do not have any database at all."""

    def donothing(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        return self.donothing


class ORMControl:
    """An interface to higher-level database operations that may be dependent on the ORM technology used.

    This class has the responsibility to manage the higher-level
    backend operations, such as instrumenting persisted classes,
    creating database schemas, migration, etc.

    In order to support a new type of ORM, subclass this class
    and implement its methods appropriately for that ORM.

    Don't use this class directly, rather call the methods on the
    :class:`SystemControl`. It delegates to the appropriate underlying
    :class:`ORMControl` and/or :class:`DatabaseControl` as
    appropriate.

    .. versionchanged: 5.0
       Signature changed from taking eggs_in_order to taking root_egg.
    """
    def migrate_db(self, root_egg, explain=False):
        plan = MigrationPlan(root_egg, self)
        if explain:
            try:
                plan.do_planning()
            finally:
                plan.explain()
        else:
            plan.do_planning()
            plan.execute()
                   

    @contextmanager
    def nested_transaction(self):
        """A context manager for code that needs to run in a nested transaction.

        .. versionchanged:: 5.0
           Changed to yield a TransactionVeto which can be used to override when the transaction will be committed or not.
        """
        pass

    @contextmanager
    def managed_transaction(self):
        pass
    def connect(self, auto_commit=False):
        pass
    @property
    def connected(self):
        pass
    def finalise_session(self):
        pass
    def disconnect(self):
        pass
    def commit(self):
        """Commits the current transaction. Programmers should not need to deal with such transaction
           management explicitly, since the framework already manages transactions itself."""
        pass
    def rollback(self):
        """Rolls back the current transaction. Programmers should not need to deal with such transaction
           management explicitly, since the framework already manages transactions itself."""
        pass
    def create_db_tables(self, transaction, eggs_in_order):
        pass
    def drop_db_tables(self, transaction):
        pass
    def execute_one(self, sql):
        pass
    def prune_schemas_to_only(self, live_versions):
        pass
    def diff_db(self, output_sql=False):
        pass
    def initialise_schema_version_for(self, egg=None, egg_name=None, egg_version=None):
        pass
    def remove_schema_version_for(self, egg=None, egg_name=None, fail_if_not_found=True):
        pass
    def schema_version_for(self, egg, default=None):
        pass
    def set_schema_version_for(self, version):
        pass



