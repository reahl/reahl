# Copyright 2013-2020 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""Support for the MySQL database backend.

To use MySql:

- install reahl-mysqlsupport;
- add it as a dependency in your .reahlproject; and
- in reahl.config.py, set reahlsystem.connection_uri to a mysql URI.

URIs are as `defined by SqlAlchemy <http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls>`_

"""


import subprocess
import gzip
from datetime import date
from contextlib import closing
import os.path
import socket
import getpass

from reahl.component.dbutils import DatabaseControl
from reahl.component.shelltools import Executable

import MySQLdb

class MysqlControl(DatabaseControl):
    """A DatabaseControl implementation for MySQL."""
    control_matching_regex = r'^mysql:'

    def login_args(self, login_username=None):
        args = []
        if self.host:
            args += ['-h', self.host]
        if self.port:
            args += ['-P', str(self.port)]
        if login_username:
            args += ['-u', login_username]
        return args

    def execute(self, sql, login_username=None, password=None, database_name=None):
        login_args = {}
        if database_name:
            login_args['db'] = database_name
        if self.host:
            login_args['host'] = self.host
        if self.port:
            login_args['port'] = self.port
        login_args['user'] = login_username or getpass.getuser()
        if password:
            login_args['passwd'] = password
            
        connection = MySQLdb.connect(**login_args)
        try:
            with connection.cursor() as cursor:
                return cursor.execute(sql)
        finally:
            connection.close()

    def get_superuser_password(self):
        return os.environ.get('MYSQL_PWD', None)
    
    def create_db_user(self, super_user_name=None, create_with_password=True):
        super_user_name = super_user_name or 'root'
        super().create_db_user(super_user_name=super_user_name, create_with_password=create_with_password)
        identified = 'by \'%s\'' % self.password if create_with_password else 'with \'auth_sock\''
        self.execute('create user %s identified %s;' % (self.user_name, identified),
                     login_username=super_user_name, password=self.get_superuser_password())
        return 0

    def drop_db_user(self, super_user_name=None):
        super_user_name = super_user_name or 'root'
        super().drop_db_user(super_user_name=super_user_name)
        self.execute('drop user %s;' % self.user_name,
                     login_username=super_user_name, password=self.get_superuser_password())
        return 0

    def drop_database(self, super_user_name=None):
        super_user_name = super_user_name or 'root'
        self.execute('drop database if exists %s;' % self.database_name,
                     login_username=super_user_name, password=self.get_superuser_password())
        return 0

    def create_database(self, super_user_name=None):
        super_user_name = super_user_name or 'root'
        self.execute('create database %s;' % self.database_name,
                     login_username=super_user_name, password=self.get_superuser_password())

        if self.user_name:
            self.execute('grant all privileges on %s.* to %s;' % (self.database_name, self.user_name),
                         login_username=super_user_name, password=self.get_superuser_password())
        return 0

    def backup_database(self, directory, super_user_name=None):
        super_user_name = super_user_name or 'root'
        today = date.today()
        filename = '%s.%s.sql.gz' % (self.database_name, today.strftime('%A'))
        full_path = os.path.join(directory, filename)
        with closing(gzip.open(full_path, 'wb')) as zipped_file:
            proc = Executable('mysqldump').Popen(self.login_args(login_username=super_user_name) + ['--databases', self.database_name],
                                                  stdout=subprocess.PIPE)
            for line in proc.stdout:
                zipped_file.write(line)
        return 0

    def backup_all_databases(self, directory, super_user_name=None):
        super_user_name = super_user_name or 'root'
        today = date.today()
        hostname = self.host
        if hostname == 'localhost':
            hostname = socket.gethostname()
        filename = '%s-all.%s.sql.gz' % (hostname, today.strftime('%A'))
        full_path = os.path.join(directory, filename)

        with closing(gzip.open(full_path, 'wb')) as zipped_file:
            proc = Executable('mysqldump').Popen(['--all-databases'] + self.login_args(login_username=super_user_name),
                                                  stdout=subprocess.PIPE)
            for line in proc.stdout:
                zipped_file.write(line)
        return 0

    def restore_database(self, filename, super_user_name=None):
        super_user_name = super_user_name or 'root'
        return self.restore_all_databases(filename, super_user_name=super_user_name)

    def restore_all_databases(self, filename, super_user_name=None):
        super_user_name = super_user_name or 'root'
        with closing(gzip.open(filename, 'rb')) as zipped_file:
            proc = Executable('mysql').Popen(self.login_args(login_username=super_user_name),
                                             stdin=subprocess.PIPE)
            for line in zipped_file:
                proc.stdin.write(line)
        return 0

    def size_database(self, orm_control):
        sql = '''SELECT  SUM(ROUND(((DATA_LENGTH + INDEX_LENGTH) / 1024 ), 2)) AS "SIZE IN kB"
          FROM INFORMATION_SCHEMA.TABLES
          WHERE TABLE_SCHEMA = "%s";''' % self.database_name
        result = orm_control.execute_one(sql)
        return '%s kB' % (result[0] if result[0] else 0)
