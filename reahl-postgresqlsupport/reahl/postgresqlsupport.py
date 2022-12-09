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

"""Support for the PostgreSQL database backend.

To use Postgresql:

- install reahl-postgresqlsupport;
- add it as a dependency in your .reahlproject; and
- in reahl.config.py, set reahlsystem.connection_uri to a postgresql URI.

URIs are as `defined by SqlAlchemy <http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls>`_

"""


import io
import subprocess
import gzip
from datetime import date
from contextlib import closing, contextmanager
import os.path
import socket
import getpass

import psycopg2
import psycopg2.extensions

from reahl.component.dbutils import DatabaseControl
from reahl.component.exceptions import DomainException, ProgrammerError
from reahl.component.shelltools import Executable, ExecutableNotInstalledException


@contextmanager
def as_domain_exception(exception_to_translate):
    try:
        yield
    except exception_to_translate as e:
        raise DomainException(message=str(e))


class PostgresqlControl(DatabaseControl):
    """A DatabaseControl implementation for PostgreSQL."""
    control_matching_regex = r'^postgres(ql)?:'

    def execute(self, sql, login_username=None, password=None, database_name=None):
        login_args = {}
        if not (database_name or self.database_name):
            raise ProgrammerError('no database name specified')
        login_args['dbname'] = database_name or self.database_name
        if self.host:
            login_args['host'] = self.host
        if self.port:
            login_args['port'] = self.port
        login_args['user'] = login_username or getpass.getuser()
        if password:
            login_args['password'] = password

        #https://stackoverflow.com/questions/68084078/psycopg2-errors-activesqltransaction-create-tablespace-cannot-run-inside-a-tran
        # https://github.com/psycopg/psycopg2/issues/941
        # this used to work until pre psycopg 2.8.6. Since 2.9:
        # with psycopg2.connect(...) as connection:
        # # This starts a transaction as of v2.9
        # ...
        # with psycopg2.connect(**login_args) as connection:
        #     connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        #     connection.autocommit = True
        #     with connection.cursor() as cursor:
        #         return cursor.execute(sql)

        try:
            connection = psycopg2.connect(**login_args)
            connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            connection.autocommit = True
            with connection.cursor() as cursor:
                return cursor.execute(sql)
        finally:
            if connection:
                connection.close()

    def get_superuser_password(self):
        return os.environ.get('PGPASSWORD', None)
    
    def login_args(self, login_username=None):
        args = []
        if self.host:
            args += ['-h', self.host]
        if self.port:
            args += ['-p', str(self.port)]
        if login_username:
            args += ['-U', login_username]
        return args

    def create_db_user(self, super_user_name=None, create_with_password=True):
        create_password_option = 'PASSWORD \'%s\'' % self.password if create_with_password and self.password else ''
        self.execute('create user %s %s;' % (self.user_name or getpass.getuser(), create_password_option),
                     login_username=super_user_name, password=self.get_superuser_password(), database_name='postgres')
        return 0
    
    def drop_db_user(self, super_user_name=None):
        self.execute('drop user %s;' % self.user_name, login_username=super_user_name, password=self.get_superuser_password(), database_name='postgres')
        return 0

    def drop_database(self, super_user_name=None):
        self.execute('drop database if exists %s;' % self.database_name,
                     login_username=super_user_name, password=self.get_superuser_password(), database_name='postgres')

        return 0

    def create_database(self, super_user_name=None):
        owner_option = 'owner %s' % self.user_name if self.user_name else ''
        self.execute('create database %s with %s template template0 encoding \'UTF8\';' \
                     % (self.database_name, owner_option), login_username=super_user_name, password=self.get_superuser_password(), database_name='postgres')
        return 0

    def backup_database(self, directory, super_user_name=None):
        today = date.today()
        filename = '%s.psql.%s' % (self.database_name, today.strftime('%A'))
        full_path = os.path.join(directory, filename)
        with io.open(full_path, 'w') as destination_file:
            cmd_args = ['-Fc', '-o'] + self.login_args(login_username=super_user_name) + [self.database_name]
            with as_domain_exception(ExecutableNotInstalledException):
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
            with as_domain_exception(ExecutableNotInstalledException):
                proc = Executable('pg_dumpall').Popen(['-o'] + self.login_args(login_username=super_user_name),
                                                      stdout=subprocess.PIPE)
            for line in proc.stdout:
                zipped_file.write(line)
        return 0

    def restore_database(self, filename, super_user_name=None):
        with as_domain_exception(ExecutableNotInstalledException):
            Executable('pg_restore').check_call(self.login_args(login_username=super_user_name)
                                            + ['-C', '-Fc', '-d', 'postgres', filename])
        return 0

    def restore_all_databases(self, filename, super_user_name=None):
        with closing(gzip.open(filename, 'rb')) as zipped_file:
            with as_domain_exception(ExecutableNotInstalledException):
                proc = Executable('psql').Popen(self.login_args(login_username=super_user_name)
                                                + ['-d', 'postgres'], stdin=subprocess.PIPE)
            for line in zipped_file:
                proc.stdin.write(line)
        return 0

    def size_database(self, orm_control):
        sql = 'select pg_size_pretty(pg_database_size(\'%s\'));' % self.database_name
        result = orm_control.execute_one(sql)
        return result[0]

