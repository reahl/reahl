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

"""The Reahl production commandline utility."""

from __future__ import print_function, unicode_literals, absolute_import, division

import pprint
import six

from pkg_resources import DistributionNotFound

from reahl.component.dbutils import SystemControl
from reahl.component.shelltools import Command, ReahlCommandline, AliasFile
from reahl.component.context import ExecutionContext
from reahl.component.config import EntryPointClassList, Configuration, StoredConfiguration, MissingValue
from reahl.component.eggs import ReahlEgg




class ProductionCommand(Command):
    """Superclass used for all production shell commands."""
    def assemble(self):
        self.parser.add_argument('config_directory', type=str,  help='a reahl configuration directory')

    def execute(self, args):
        self.create_context(args.config_directory)
        self.directory = args.config_directory

    def create_context(self, config_directory):
        try:
            self.context = ExecutionContext.for_config_directory(config_directory)
        except DistributionNotFound as ex:
            ex.args = ('%s (In development? Did you forget to do a "reahl setup -- develop -N"?)' % ex.args[0],)
            raise
        self.context.install()
        self.context.system_control = SystemControl(self.context.config)

    @property
    def sys_control(self):
        return self.context.system_control
    
    @property
    def config(self):
        return self.context.config


class ListConfig(ProductionCommand):
    """Lists current configuration settings."""
    keyword = 'listconfig'

    def assemble(self):
        super(ListConfig, self).assemble()
        self.parser.add_argument('-v', '--values', action='store_true', dest='print_values', help='prints the currently configured value')
        self.parser.add_argument('-f', '--files', action='store_true', dest='print_files', help='prints the filename where the setting should be defined')
        self.parser.add_argument('-d', '--defaults', action='store_true', dest='print_defaults', help='prints the default value')
        self.parser.add_argument('-m', '--missing', action='store_true', dest='print_missing_only', help='prints the missing values only')
        self.parser.add_argument('-i', '--info', action='store_true', dest='print_description', help='prints a description')

    def create_context(self, config_directory):
        self.context = ExecutionContext(name=self.__class__.__name__)

    def execute(self, args):
        super(ListConfig, self).execute(args)
        self.context.install()

        print('Listing config for %s' % self.directory)
        config = StoredConfiguration(self.directory)
        config.configure(validate=False)
        for config_file, key, value, setting in config.list_all():
            to_print = '%-35s' % key
            if args.print_files:
                to_print += '\t%s' % config_file
            if args.print_values:
                to_print += '\t%s' % value
            if args.print_defaults:
                if setting.defaulted:
                    message = six.text_type(setting.default)
                    if setting.dangerous:
                        message += ' (DANGEROUS DEFAULT)'
                elif setting.automatic:
                    message = 'AUTOMATIC'
                else:
                    message = 'NO DEFAULT'
                to_print += '\t%s' % message
            if args.print_description:
                to_print += '\t%s' % setting.description

            if args.print_missing_only and not isinstance(value, MissingValue):
                pass
            else:
                print(to_print)


class CheckConfig(ProductionCommand):
    """Checks current configuration settings."""
    keyword = 'checkconfig'
    def execute(self, args):
        super(CheckConfig, self).execute(args)
        print('Checking config in %s' % self.directory)
        config = StoredConfiguration(self.directory)
        config.configure(validate=True)
        print('Config parses OK')


class CreateDBUser(ProductionCommand):
    """Creates the database user."""
    keyword = 'createdbuser'
    def assemble(self):
        super(CreateDBUser, self).assemble()
        self.parser.add_argument('-n', '--no-create-password', action='store_true', dest='no_create_password',
                                 help='create the user without a password')
        self.parser.add_argument('-U', '--super-user-name', dest='super_user_name', default=None,
                                 help='the name of the priviledged user who may perform this operation')
    def execute(self, args):
        super(CreateDBUser, self).execute(args)
        return self.sys_control.create_db_user(super_user_name=args.super_user_name,
                                               create_with_password=not args.no_create_password)


class DropDBUser(ProductionCommand):
    """Drops the database user."""
    keyword = 'dropdbuser'
    def assemble(self):
        super(DropDBUser, self).assemble()
        self.parser.add_argument('-U', '--super-user-name', dest='super_user_name', default=None,
                                 help='the name of the priviledged user who may perform this operation')

    def execute(self, args):
        super(DropDBUser, self).execute(args)
        return self.sys_control.drop_db_user(super_user_name=args.super_user_name)


class DropDB(ProductionCommand):
    """Drops the database."""
    keyword = 'dropdb'
    def assemble(self):
        super(DropDB, self).assemble()
        self.parser.add_argument('-y', '--yes', action='store_true', dest='yes',
                                 help='automatically answers yes on prompts')
        self.parser.add_argument('-U', '--super-user-name', dest='super_user_name', default=None,
                                 help='the name of the priviledged user who may perform this operation')

    def execute(self, args):
        super(DropDB, self).execute(args)
        return self.sys_control.drop_database(super_user_name=args.super_user_name, yes=args.yes)


class CreateDB(ProductionCommand):
    """Creates the database."""
    keyword = 'createdb'
    def assemble(self):
        super(CreateDB, self).assemble()
        self.parser.add_argument('-U', '--super-user-name', dest='super_user_name', default=None,
                                 help='the name of the priviledged user who may perform this operation')

    def execute(self, args):
        super(CreateDB, self).execute(args)
        return self.sys_control.create_database(super_user_name=args.super_user_name)


class BackupDB(ProductionCommand):
    """Backs up the database."""
    keyword = 'backupdb'
    def assemble(self):
        super(BackupDB, self).assemble()
        self.parser.add_argument('-d', '--directory', dest='directory', default='/tmp', help='the directory to back up to')
        self.parser.add_argument('-U', '--super-user-name', dest='super_user_name', default=None,
                                 help='the name of the priviledged user who may perform this operation')
    def execute(self, args):
        super(BackupDB, self).execute(args)
        return self.sys_control.backup_database(args.directory, super_user_name=args.super_user_name)


class RestoreDB(ProductionCommand):
    """Restores the database."""
    keyword = 'restoredb'

    def assemble(self):
        super(RestoreDB, self).assemble()
        self.parser.add_argument('-f', '--filename', dest='filename', default='/tmp/data.pgsql', help='the file to restore from')
        self.parser.add_argument('-U', '--super-user-name', dest='super_user_name', default=None,
                                 help='the name of the priviledged user who may perform this operation')

    def execute(self, args):
        super(RestoreDB, self).execute(args)
        return self.sys_control.restore_database(args.filename, super_user_name=args.super_user_name)


class BackupAllDB(ProductionCommand):
    """Backs up all the databases on the host this project config points to."""
    keyword = 'backupall'
    def assemble(self):
        super(BackupAllDB, self).assemble()
        self.parser.add_argument('-d', '--directory', dest='directory', default='/tmp', help='the direcotry to back up to')
        self.parser.add_argument('-U', '--super-user-name', dest='super_user_name', default=None,
                                 help='the name of the priviledged user who may perform this operation')
        
    def execute(self, args):
        super(BackupAllDB, self).execute(args)
        return self.sys_control.backup_all_databases(args.directory, super_user_name=args.super_user_name)


class RestoreAllDB(ProductionCommand):
    """Restores all the databases on the host this project config points to."""
    keyword = 'restoreall'
    def assemble(self):
        super(RestoreAllDB, self).assemble()
        self.parser.add_argument('-f', '--filename', dest='filename', default='/tmp/data.sql', help='the file to restore from')
        self.parser.add_argument('-U', '--super-user-name', dest='super_user_name', default=None,
                                 help='the name of the priviledged user who may perform this operation')
        
    def execute(self, args):
        super(RestoreAllDB, self).execute(args)
        return self.sys_control.restore_all_databases(args.filename, super_user_name=args.super_user_name)


class SizeDB(ProductionCommand):
    """Prints the current size of the database."""
    keyword = 'sizedb'
    def execute(self, args):
        super(SizeDB, self).execute(args)
        self.context.install()
        with self.sys_control.auto_connected():
            print('Database size: %s' % self.sys_control.size_database())
        return 0


class CreateDBTables(ProductionCommand):
    """Creates all necessary tables in the database."""
    keyword = 'createdbtables'
    def execute(self, args):
        super(CreateDBTables, self).execute(args)
        self.context.install()
        with self.sys_control.auto_connected():
            return self.sys_control.create_db_tables()


class DropDBTables(ProductionCommand):
    """Drops all necessary tables in the database."""
    keyword = 'dropdbtables'
    def execute(self, args):
        super(DropDBTables, self).execute(args)
        self.context.install()
        with self.sys_control.auto_connected():
            return self.sys_control.drop_db_tables()


class MigrateDB(ProductionCommand):
    """Runs all necessary database migrations."""
    keyword = 'migratedb'
    def execute(self, args):
        super(MigrateDB, self).execute(args)
        self.context.install()
        with self.sys_control.auto_connected():
            return self.sys_control.migrate_db()


class DiffDB(ProductionCommand):
    """Prints out a diff between the current database schema and what is expected by the current code."""
    keyword = 'diffdb'
    def execute(self, args):
        super(DiffDB, self).execute(args)
        self.context.install()
        with self.sys_control.auto_connected():
            pprint.pprint(self.sys_control.diff_db(), indent=2, width=20)


class ListDependencies(ProductionCommand):
    """List all dependency eggs in dependency order."""
    keyword = 'listdeps'
    def assemble(self):
        super(ListDependencies, self).assemble()
        self.parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='list direct dependencies too')
        
    def execute(self, args):
        super(ListDependencies, self).execute(args)
        self.context.install()
        distributions = ReahlEgg.compute_ordered_dependent_distributions(self.config.reahlsystem.root_egg)
        for distribution in distributions:
            deps = ''
            if args.verbose:
                deps = '[%s]' % (' | '.join([six.text_type(i) for i in distribution.requires()]))
            print('%s %s' % (distribution, deps))
        return 0


class RunJobs(ProductionCommand):
    """Runs all registered scripts."""
    keyword = 'runjobs'
    def execute(self, args):
        super(RunJobs, self).execute(args)
        self.context.install()
        with self.sys_control.auto_connected():
            self.sys_control.do_daily_maintenance()
        return 0



