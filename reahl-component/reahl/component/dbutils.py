# Copyright 2008-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""Utilities to manipulate underlying databases - sometimes via an ORM tool."""

from __future__ import unicode_literals
from __future__ import print_function
import re
from contextlib import contextmanager
import logging

from reahl.component.eggs import ReahlEgg
from reahl.component.migration import MigrationSchedule, MigrationRun

class InvalidConnectionURIException(Exception):
    pass
    
    
class CouldNotFindDatabaseControlException(Exception):
    def __init__(self, url):
        super(CouldNotFindDatabaseControlException, self).__init__(url)
        self.url = url


class SystemControl(object):
    def __init__(self, config):
        self.config = config
        self.connection_uri = self.config.reahlsystem.connection_uri
        self.db_control = self.db_control_for_uri(self.connection_uri)
        self.orm_control = self.config.reahlsystem.orm_control
        self.orm_control.system_control = self

    def connect(self):
        self.orm_control.connect()
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
        return self.orm_control.connected

    def disconnect(self):
        self.orm_control.disconnect()
        
    def managed_transaction(self):
        return self.orm_control.managed_transaction()

    def nested_transaction(self):
        return self.orm_control.nested_transaction()
                
    def finalise_session(self):
        self.orm_control.finalise_session()

    def set_transaction_and_connection(self, transaction):
        self.orm_control.set_transaction_and_connection(transaction)

    def commit(self):
        self.orm_control.commit()
        
    def rollback(self):
        self.orm_control.rollback()

    def db_control_for_uri(self, url):
        for i in self.config.reahlsystem.databasecontrols:
            if i.matches_uri(url):
                return i(url, self.config)
        raise CouldNotFindDatabaseControlException(url)

    def __getattr__(self, name):
        return getattr(self.db_control, name)

    def size_database(self):
        with self.orm_control.managed_transaction():
            return self.db_control.size_database(self.orm_control)

    def create_db_tables(self):
        eggs_in_order = ReahlEgg.get_all_relevant_interfaces(self.config.reahlsystem.root_egg)
        with self.orm_control.managed_transaction() as transaction:
            return self.orm_control.create_db_tables(transaction, eggs_in_order)

    def drop_db_tables(self):
        with self.orm_control.managed_transaction() as transaction:
            return self.orm_control.drop_db_tables(transaction)

    def initialise_database(self, yes=False):
        self.drop_database(yes=yes)
        self.create_database()
        self.connect()
        try:
            self.create_db_tables()
        finally:
            self.disconnect() 

    def migrate_db(self):
        eggs_in_order = ReahlEgg.get_all_relevant_interfaces(self.config.reahlsystem.root_egg)
        self.orm_control.migrate_db(eggs_in_order)
        return 0

    def do_daily_maintenance(self):
        with self.orm_control.managed_transaction() as transaction:
            ReahlEgg.do_daily_maintenance_for_egg(self.config.reahlsystem.root_egg)


class DatabaseControl(object):
    def __init__(self, url, config):
        self.config = config
        self.connection_uri = url
        uri_parts = self.parse_connection_uri(url)
        self.user_name = uri_parts['user']
        self.password = uri_parts['password']
        self.host = uri_parts['host']
        port_string = uri_parts['port'] or '5432'
        self.port = int(port_string)
        self.database_name = uri_parts['database']

    def get_dbapi_connection_creator(self):
        return None

    @property    
    def is_in_memory(self):
        return False

    @classmethod
    def matches_uri(cls, url):
        try:
            cls.parse_connection_uri(url)
            return True
        except InvalidConnectionURIException:
            return False
    
    @classmethod
    def parse_connection_uri(cls, url):
        match = re.match(cls.uri_regex_string, url)
        if not match:
            raise InvalidConnectionURIException()
        return match.groupdict()

class NullDatabaseControl(DatabaseControl):
    uri_regex_string = r''
    @classmethod
    def parse_connection_uri(self, url):
        if not url:
            return {'user':'', 'password':'', 'host':'', 'port':'', 'database':''}
        raise InvalidConnectionURIException()

    def donothing(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        return self.donothing
        

class ORMControl(object):
    is_elixir = False

    def migrate_db(self, eggs_in_order):
        with self.managed_transaction():
            migration_run = MigrationRun(self, eggs_in_order)
            migration_run.schedule_migrations()
            migration_run.execute_migrations()









