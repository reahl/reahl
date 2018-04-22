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

"""Support for the PostgreSQL database backend.

To use Postgresql:

- install reahl-postgresqlsupport;
- add it as a dependency in your .reahlproject; and
- in reahl.config.py, set reahlsystem.connection_uri to a postgresql URI.

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


class PostgresqlControl(DatabaseControl):
    """A DatabaseControl implementation for PostgreSQL."""
    control_matching_regex = r'^postgres(ql)?:'

    def login_args(self, login_username=None):
        args = []
        if self.host:
            args += ['-h', self.host]
        if self.port:
            args += ['-p', six.text_type(self.port)]
        if login_username:
            args += ['-U', login_username]
        return args

    def create_db_user(self, super_user_name=None, create_with_password=True):
        create_password_option = 'P' if create_with_password else ''
        Executable('createuser').check_call(['-DSRl%s' % create_password_option]
                                            + self.login_args(login_username=super_user_name)
                                            + [self.user_name])
        return 0

    def drop_db_user(self, super_user_name=None):
        Executable('dropuser').check_call(self.login_args(login_username=super_user_name) + [self.user_name])
        return 0

    def drop_database(self, super_user_name=None, yes=False):
        cmd_args = self.login_args(login_username=super_user_name) + ['--if-exists']
        last_part = ['-i', self.database_name]
        if yes:
            last_part = [self.database_name]

        Executable('dropdb').check_call(cmd_args + last_part)
        return 0

    def create_database(self, super_user_name=None):
        owner_option = ['-O', self.user_name] if self.user_name else []
        Executable('createdb').check_call(['-Eunicode']
                                          + self.login_args(login_username=super_user_name)
                                          + ['-T', 'template0']
                                          + owner_option + [self.database_name])
        return 0

    def backup_database(self, directory, super_user_name=None):
        today = date.today()
        filename = '%s.psql.%s' % (self.database_name, today.strftime('%A'))
        full_path = os.path.join(directory, filename)
        with io.open(full_path, 'w') as destination_file:
            cmd_args = ['-Fc', '-o'] + self.login_args(login_username=super_user_name) + [self.database_name]
            Executable('pg_dump').check_call(cmd_args, stdout=destination_file)
        return 0

    def backup_all_databases(self, directory, super_user_name=None):
        today = date.today()
        hostname = self.host
        if hostname == 'localhost':
            hostname = socket.gethostname()
        filename = '%s-all.%s.sql.gz' % (hostname, today.strftime('%A'))
        full_path = os.path.join(directory, filename)

        with closing(gzip.open(full_path, 'wb')) as zipped_file:
            proc = Executable('pg_dumpall').Popen(['-o'] + self.login_args(login_username=super_user_name),
                                                  stdout=subprocess.PIPE)
            for line in proc.stdout:
                zipped_file.write(line)
        return 0


    def restore_database(self, filename, super_user_name=None):
        Executable('pg_restore').check_call(self.login_args(login_username=super_user_name)
                                            + ['-C', '-Fc', '-d', 'postgres', filename])
        return 0

    def restore_all_databases(self, filename, super_user_name=None):
        with closing(gzip.open(filename, 'rb')) as zipped_file:
            proc = Executable('psql').Popen(self.login_args(login_username=super_user_name)
                                            + ['-d', 'postgres'], stdin=subprocess.PIPE)
            for line in zipped_file:
                proc.stdin.write(line)
        return 0

    def size_database(self, orm_control):
        sql = 'select pg_size_pretty(pg_database_size(\'%s\'));' % self.database_name
        result = orm_control.execute_one(sql)
        return result[0]
