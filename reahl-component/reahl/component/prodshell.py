# Copyright 2009-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from __future__ import unicode_literals
from __future__ import print_function


from pkg_resources import DistributionNotFound

from reahl.component.dbutils import SystemControl
from reahl.component.shelltools import Command, ReahlCommandline
from reahl.component.context import ExecutionContext
from reahl.component.config import EntryPointClassList, Configuration, StoredConfiguration, MissingValue
from reahl.component.eggs import ReahlEgg




class ProdShellConfig(Configuration):
    commands = EntryPointClassList('reahl.component.prodcommands', description='The commands (classes) available to the production commandline shell')


class ProductionCommand(Command):
    """Superclass used for all production shell commands."""
    options = []
    usage_args = '<config_directory>'
    
    def execute(self, options, args):
        self.create_context(args[0])
        self.directory = args[0]

    def verify_commandline(self, options, args):
        if not len(args) >= 1:
            self.parser.error('No config directory given')

    def create_context(self, config_directory):
        try:
            self.context = ExecutionContext.for_config_directory(config_directory)
        except DistributionNotFound as ex:
            ex.args = ('%s (In development? Did you forget to do a "reahl setup -- develop -N"?)' % ex.args[0],)
            raise
        with self.context:
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
    options = ProductionCommand.options +\
               [('-v', '--values', dict(action='store_true', dest='print_values', help='prints the currently configured value')),
               ('-f', '--files', dict(action='store_true', dest='print_files', help='prints the filename where the setting should be defined')),
               ('-d', '--defaults', dict(action='store_true', dest='print_defaults', help='prints the default value')),
               ('-m', '--missing', dict(action='store_true', dest='print_missing_only', help='prints the missing values only')),
               ('-i', '--info', dict(action='store_true', dest='print_description', help='prints a description'))]

    def create_context(self, config_directory):
        self.context = ExecutionContext()

    def execute(self, options, args):
        super(ListConfig, self).execute(options, args)
        with self.context:
            print('Listing config for %s' % self.directory)
            config = StoredConfiguration(self.directory)
            config.configure(validate=False)
            for config_file, key, value, setting in config.list_all():
                to_print = '%-35s' % key
                if options.print_files:
                    to_print += '\t%s' % config_file
                if options.print_values:
                    to_print += '\t%s' % value
                if options.print_defaults:
                    if setting.defaulted:
                        message = setting.default
                        if setting.dangerous:
                            message += ' (DANGEROUS DEFAULT)'
                    elif setting.automatic:
                        message = 'AUTOMATIC'
                    else:
                        message = 'NO DEFAULT'
                    to_print += '\t%s' % message
                if options.print_description:
                    to_print += '\t%s' % setting.description

                if options.print_missing_only and not isinstance(value, MissingValue):
                    pass
                else:
                    print(to_print)


class CheckConfig(ProductionCommand):
    """Checks current configuration settings."""
    keyword = 'checkconfig'
    def execute(self, options, args):
        super(CheckConfig, self).execute(options, args)
        print('Checking config in %s' % self.directory)
        config = StoredConfiguration(self.directory)
        config.configure(validate=True)
        print('Config parses OK')


class CreateDBUser(ProductionCommand):
    """Creates the database user."""
    keyword = 'createdbuser'
    def execute(self, options, args):
        super(CreateDBUser, self).execute(options, args)
        return self.sys_control.create_db_user()


class DropDBUser(ProductionCommand):
    """Drops the database user."""
    keyword = 'dropdbuser'
    def execute(self, options, args):
        super(DropDBUser, self).execute(options, args)
        return self.sys_control.drop_db_user()


class DropDB(ProductionCommand):
    """Drops the database."""
    keyword = 'dropdb'
    options = [('-y', '--yes', dict(action='store_true', dest='yes',
                                      help='automatically answers yes on prompts'))]
    def execute(self, options, args):
        super(DropDB, self).execute(options, args)
        return self.sys_control.drop_database(yes=options.yes)


class CreateDB(ProductionCommand):
    """Creates the database."""
    keyword = 'createdb'
    def execute(self, options, args):
        super(CreateDB, self).execute(options, args)
        return self.sys_control.create_database()


class BackupDB(ProductionCommand):
    """Backs up the database."""
    keyword = 'backupdb'
    options = ProductionCommand.options +\
              [('-d', '--directory', dict(dest='directory', default='/tmp', help='the direcotry to back up to'))]
    def execute(self, options, args):
        super(BackupDB, self).execute(options, args)
        return self.sys_control.backup_database(options.directory)


class RestoreDB(ProductionCommand):
    """Restores up the database."""
    keyword = 'restoredb'
    options = ProductionCommand.options +\
              [('-f', '--filename', dict(dest='filename', default='/tmp/data.pgsql', help='the file to restore from'))]
    def execute(self, options, args):
        super(RestoreDB, self).execute(options, args)
        return self.sys_control.restore_database(options.filename)


class BackupAllDB(ProductionCommand):
    """Backs up all the databases on the host this project config points to."""
    keyword = 'backupall'
    options = ProductionCommand.options +\
              [('-d', '--directory', dict(dest='directory', default='/tmp', help='the direcotry to back up to'))]
    def execute(self, options, args):
        super(BackupAllDB, self).execute(options, args)
        return self.sys_control.backup_all_databases(options.directory)


class RestoreAllDB(ProductionCommand):
    """Restores all the databases on the host this project config points to."""
    keyword = 'restoreall'
    options = ProductionCommand.options +\
              [('-f', '--filename', dict(dest='filename', default='/tmp/data.sql', help='the file to restore from'))]
    def execute(self, options, args):
        super(RestoreAllDB, self).execute(options, args)
        return self.sys_control.restore_all_databases(options.filename)


class SizeDB(ProductionCommand):
    """Prints the current size of the database."""
    keyword = 'sizedb'
    def execute(self, options, args):
        super(SizeDB, self).execute(options, args)
        with self.context:
            with self.sys_control.auto_connected():
                print('Database size: %s' % self.sys_control.size_database())
        return 0


class CreateDBTables(ProductionCommand):
    """Creates all necessary tables in the database."""
    keyword = 'createdbtables'
    def execute(self, options, args):
        super(CreateDBTables, self).execute(options, args)
        with self.context:
            with self.sys_control.auto_connected():
                return self.sys_control.create_db_tables()


class DropDBTables(ProductionCommand):
    """Drops all necessary tables in the database."""
    keyword = 'dropdbtables'
    def execute(self, options, args):
        super(DropDBTables, self).execute(options, args)
        with self.context:
            with self.sys_control.auto_connected():
                return self.sys_control.drop_db_tables()


class MigrateDB(ProductionCommand):
    """Runs all necessary database migrations."""
    keyword = 'migratedb'
    def execute(self, options, args):
        super(MigrateDB, self).execute(options, args)
        with self.context:
            with self.sys_control.auto_connected():
                return self.sys_control.migrate_db()


class ListDependencies(ProductionCommand):
    """List all dependency eggs in dependency order."""
    keyword = 'listdeps'
    options = ProductionCommand.options +\
              [('-v', '--verbose', dict(action='store_true', dest='verbose', help='list direct dependencies too'))]
    def execute(self, options, args):
        super(ListDependencies, self).execute(options, args)
        with self.context:
            distributions = ReahlEgg.compute_ordered_dependent_distributions(self.config.reahlsystem.root_egg)
            for distribution in distributions:
                deps = ''
                if options.verbose:
                    deps = '[%s]' % (' | '.join([six.text_type(i) for i in distribution.requires()]))
                print('%s %s' % (distribution, deps))
        return 0


class RunJobs(ProductionCommand):
    """Runs all registered scripts."""
    keyword = 'runjobs'
    def execute(self, options, args):
        super(RunJobs, self).execute(options, args)
        with self.context:
            with self.sys_control.auto_connected():
                self.sys_control.do_daily_maintenance()
        return 0



class ProductionCommandline(ReahlCommandline):
    """The main class for invoking commands on projects in production environments."""
    def __init__(self, options):
        super(ProductionCommandline, self).__init__(options, ProdShellConfig())

