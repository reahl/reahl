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

"""Support for the MySQL database backend.

To use MySql:

- install reahl-mysqlsupport;
- add it as a dependency in your .reahlproject; and
- in reahl.config.py, set reahlsystem.connection_uri to a mysql URI.

URIs are as `defined by SqlAlchemy <http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls>`_

"""

from __future__ import print_function, unicode_literals, absolute_import, division

import six
import io
import subprocess
import gzip
from datetime import date
from contextlib import closing
import os.path
import socket

from reahl.component.dbutils import DatabaseControl
from reahl.component.shelltools import Executable


class MysqlControl(DatabaseControl):
    """A DatabaseControl implementation for MySQL."""
    control_matching_regex = r'^mysql:'

    def login_args(self, login_username=None):
        args = []
        if self.host:
            args += ['-h', self.host]
        if self.port:
            args += ['-P', six.text_type(self.port)]
        if login_username:
            args += ['-u', login_username]
        return args

    def create_db_user(self, super_user_name=None, create_with_password=True):
        super(MysqlControl, self).create_db_user(super_user_name=super_user_name, create_with_password=create_with_password)
        identified = 'by \'%s\'' % self.password if create_with_password else 'with \'auth_sock\'' 
        Executable('mysql').check_call( self.login_args(login_username=super_user_name)
                                        + ['-e', 'create user %s identified %s;' % (self.user_name, identified)])
        return 0

    def drop_db_user(self, super_user_name=None):
        super(MysqlControl, self).drop_db_user(super_user_name=super_user_name)
        Executable('mysql').check_call( self.login_args(login_username=super_user_name)
                                        + ['-e', 'drop user %s;' % self.user_name])
        return 0

    def drop_database(self, super_user_name=None, yes=False):
        cmd_args = self.login_args(login_username=super_user_name) 
        if yes:
            cmd_args.append('-f')

        Executable('mysqladmin').check_call(['drop'] + cmd_args + [self.database_name])
        return 0

    def create_database(self, super_user_name=None):
        Executable('mysqladmin').check_call(['create']
                                          + self.login_args(login_username=super_user_name)
                                          + [self.database_name])
        if self.user_name:
            Executable('mysql').check_call(self.login_args(login_username=super_user_name)
                                           + ['-e', 'grant all privileges on %s.* to %s;' % (self.database_name, self.user_name)])
        Executable('mysqladmin').check_call(['flush-privileges'] + self.login_args(login_username=super_user_name))
        return 0

    def backup_database(self, directory, super_user_name=None):
        today = date.today()
        filename = '%s.%s.sql.gz' % (self.database_name, today.strftime('%A'))
        full_path = os.path.join(directory, filename)
        with closing(gzip.open(full_path, 'wb')) as zipped_file:
            proc = Executable('mysqldump').Popen(self.login_args(login_username=super_user_name) + [self.database_name],
                                                  stdout=subprocess.PIPE)
            for line in proc.stdout:
                zipped_file.write(line)
        return 0

    def backup_all_databases(self, directory, super_user_name=None):
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
        return self.restore_all_databases(filename, super_user_name=super_user_name)

    def restore_all_databases(self, filename, super_user_name=None):
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
