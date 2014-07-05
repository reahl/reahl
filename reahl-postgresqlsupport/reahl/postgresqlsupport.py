# Copyright 2010, 2011, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""Support for the PostgreSQL database backend."""

from __future__ import unicode_literals
from __future__ import print_function
import six
import subprocess
import gzip
from datetime import date
from contextlib import closing
import os.path

from reahl.component.dbutils import DatabaseControl
from reahl.component.shelltools import Executable

class PostgresqlControl(DatabaseControl):
    """A DatabaseControl implementation for PostgreSQL."""
    uri_regex_string = r'postgres(ql)?://' + \
        r'(?P<user>\w+)(:(?P<password>\w+))?' + \
        r'@(?P<host>\w+)(:(?P<port>\d+))?' + \
        r'/(?P<database>\w+)$'

    @property
    def login_args(self):
	if self.host == 'localhost' and self.port == 5432:
            return []
        return ['-h', self.host, '-p', six.text_type(self.port)]

    def create_db_user(self):
         Executable('createuser').check_call(['-DSRlP'] + self.login_args + [self.user_name])
         return 0

    def drop_db_user(self):
        Executable('dropuser').check_call(self.login_args + [self.user_name])
        return 0

    def drop_database(self, yes=False):
        cmd_args = self.login_args
        last_part = ['-i', self.database_name]
        if yes:
            last_part = [self.database_name]

        Executable('dropdb').check_call(cmd_args+last_part)
        return 0

    def create_database(self):
        cmd_args = ['-Eunicode'] + self.login_args + ['-T', 'template0', '-O', self.user_name,  self.database_name]
        Executable('createdb').check_call(cmd_args)
        return 0

    def backup_database(self, directory):
        today = date.today()
        filename = '%s.psql.%s' % (self.database_name, today.strftime('%A'))
        full_path = os.path.join(directory, filename)
        with open(full_path, 'w') as destination_file:
            cmd_args = ['-Fc', '-o'] + self.login_args + [self.database_name]
            Executable('pg_dump').check_call(cmd_args, stdout=destination_file)
        return 0

    def backup_all_databases(self, directory):
        today = date.today()
        hostname = self.host
        if hostname == 'localhost':
            hostname = socket.gethostname()
        filename = '%s-all.%s.sql.gz' % (hostname, today.strftime('%A'))
        full_path = os.path.join(directory, filename)

        with closing(gzip.open(full_path, 'wb')) as zipped_file:
            proc = Executable('pg_dumpall').Popen([ '-o'] + self.login_args, stdout=subprocess.PIPE)
            for line in proc.stdout:
                zipped_file.write(line)
        return 0

        
    def restore_database(self, filename):
        cmd = ['-C', '-Fc', '-d', 'postgres', filename]
        Executable('pg_restore').check_call(['-C', '-Fc', '-d', 'postgres', filename])
        return 0

    def restore_all_databases(self, filename):
        with closing(gzip.open(filename, 'rb')) as zipped_file:
            proc = Executable('psql').Popen(['-d', 'template1'], stdin=subprocess.PIPE)
            for line in zipped_file:
                proc.stdin.write(line)
        return 0
        
    def size_database(self, orm_control):
        sql = 'select pg_size_pretty(pg_database_size(\'%s\'));' % self.database_name
        result = orm_control.execute_one(sql)
        return result[0]
