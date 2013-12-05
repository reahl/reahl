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

import subprocess
import gzip
from datetime import date
from contextlib import closing
import os.path

from reahl.component.dbutils import DatabaseControl

class PostgresqlControl(DatabaseControl):
    """A DatabaseControl implementation for PostgreSQL."""
    uri_regex_string = r'postgres://' + \
        r'(?P<user>\w+)(:(?P<password>\w+))?' + \
        r'@(?P<host>\w+)(:(?P<port>\d+))?' + \
        r'/(?P<database>\w+)$'

    @property
    def login_args(self):
	if self.host == 'localhost' and self.port == 5432:
            return []
        return ['-h', self.host, '-p', str(self.port)]

    def create_db_user(self):
         cmd = ['createuser', '-DSRlP'] + self.login_args + [self.user_name]
         subprocess.check_call(cmd)
         return 0

    def drop_db_user(self):
        cmd = ['dropuser'] + self.login_args + [self.user_name]
        subprocess.check_call(cmd)
        return 0

    def drop_database(self, yes=False):
        cmd = ['dropdb'] + self.login_args
        last_part = ['-i', self.database_name]
        if yes:
            last_part = [self.database_name]

        subprocess.check_call(cmd+last_part)
        return 0

    def create_database(self):
        cmd = ['createdb', '-Eunicode'] + self.login_args + ['-T', 'template0', '-O', self.user_name,  self.database_name]
        subprocess.check_call(cmd)
        return 0

    def backup_database(self, directory):
        today = date.today()
        filename = '%s.psql.%s' % (self.database_name, today.strftime('%A'))
        full_path = os.path.join(directory, filename)
        with open(full_path, 'w') as destination_file:
            cmd = ['pg_dump', '-Fc', '-o'] + self.login_args + [self.database_name]
            subprocess.check_call(cmd, stdout=destination_file)
        return 0

    def backup_all_databases(self, directory):
        today = date.today()
        hostname = self.host
        if hostname == 'localhost':
            hostname = socket.gethostname()
        filename = '%s-all.%s.sql.gz' % (hostname, today.strftime('%A'))
        full_path = os.path.join(directory, filename)

        with closing(gzip.open(full_path, 'wb')) as zipped_file:
            cmd = ['pg_dumpall', '-o'] + self.login_args
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            for line in proc.stdout:
                zipped_file.write(line)
        return 0

        
    def restore_database(self, filename):
        cmd = ['pg_restore', '-C', '-Fc', '-d', 'postgres', filename]
        subprocess.check_call(cmd)
        return 0

    def restore_all_databases(self, filename):
        with closing(gzip.open(filename, 'rb')) as zipped_file:
            cmd = ['psql', '-d', 'template1']
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            for line in zipped_file:
                proc.stdin.write(line)
        return 0
        
    def size_database(self, orm_control):
        sql = 'select pg_size_pretty(pg_database_size(\'%s\'));' % self.database_name
        result = orm_control.execute_one(sql)
        return result[0]
