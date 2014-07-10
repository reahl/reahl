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

"""Support for the SQLite database backend."""


from __future__ import unicode_literals
from __future__ import print_function
import os
import exceptions
import shutil
import os.path
from datetime import date
import logging

import sqlite3

from reahl.component.dbutils import DatabaseControl


class SQLiteControl(DatabaseControl):
    """A DatabaseControl implementation for SQLite."""
    uri_regex_string = r'sqlite:///' + \
        r'(?P<database>.*)(?P<user>)(?P<password>)(?P<host>)(?P<port>)$'

    def __init__(self, url, config):
        super(SQLiteControl, self).__init__(url, config)
        if not config.reahlsystem.serialise_parallel_requests:
            config.reahlsystem.serialise_parallel_requests = True
            logging.getLogger(__name__).warning('Overriding config setting[reahlsystem.serialise_parallel_requests] to True. Sqlite cannot handle concurrency.')
    
    def get_dbapi_connection_creator(self):
        # See: http://stackoverflow.com/questions/2182591/python-sqlite-3-roll-back-to-save-point-fails
        def connect(*args, **kwargs): 
            conn = sqlite3.connect(self.database_name, check_same_thread=False) 
            conn.isolation_level = None
            conn.execute('PRAGMA foreign_keys = ON') # http://www.sqlite.org/foreignkeys.html
            return conn
        return connect

    @property    
    def is_in_memory(self):
        return (self.database_name == ':memory:') or (self.database_name == '')
        
    @property
    def login_args(self):
        return []
    
    def create_db_user(self):
        return 0

    def drop_db_user(self):
        return 0

    def drop_database(self, yes=False):
        if not self.is_in_memory:
            try:
                os.remove(self.database_name)
            except exceptions.OSError:
                pass
        return 0

    def create_database(self):
        return 0

    def backup_database(self, directory):
        today = date.today()
        filename = '%s.sqlite.%s' % (self.database_name, today.strftime('%A'))
        full_path = os.path.join(directory, filename)
        shutil.copyfile(self.database_name, full_path)
        return 0
        
    def restore_database(self, filename):
        shutil.copyfile(filename, self.database_name)
        return 0
        
    def size_database(self, orm_control):
        return os.path.getsize(self.database_name)
        return result[0]
