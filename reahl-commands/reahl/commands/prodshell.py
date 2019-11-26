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

import sys
import os.path
import os
import shutil

import pprint
import six
import inspect
import textwrap

from pkg_resources import DistributionNotFound, get_distribution

from reahl.component.dbutils import SystemControl
from reahl.component.shelltools import Command, ReahlCommandline, AliasFile
from reahl.component.context import ExecutionContext
from reahl.component.config import EntryPointClassList, Configuration, ConfigSetting, StoredConfiguration, MissingValue
from reahl.component.eggs import ReahlEgg
from reahl.component.exceptions import DomainException

from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.completion.filesystem import PathCompleter



class ComponentInfo(Command):
    """Gives information about a given reahl component"""
    keyword = 'componentinfo'
    def assemble(self):
        self.parser.add_argument('component_name', type=str,  help='the name of a component')

    def execute(self, args):
        egg = ReahlEgg(get_distribution(args.component_name))
        print('Name: %s' % egg.name)
        print('Version: %s' % egg.version)
        configuration_class = egg.configuration_spec
        if configuration_class:
            self.print_configuration_info(configuration_class)
        if egg.translation_package:
            self.print_locale_info(egg)

    def print_locale_info(self, egg):
        print('\nLocale info:\n')
        print('\tTranslation package: %s' % egg.translation_package.__name__)
        print('\tTranslation POT: %s' % egg.translation_pot_filename)

    def print_configuration_info(self, configuration_class):
        print('\nConfiguration (%s):\n' % configuration_class.filename)
        if configuration_class.__doc__:
            for line in inspect.getdoc(configuration_class).split('\n'):
                print('\t%s' % line)
            print('')
        for name, value in configuration_class.__dict__.items():
            if isinstance(value, ConfigSetting):
                print('\t%s.%s:\t\t\t%s' % (configuration_class.config_key, name, value.description))


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


class CommandlineMenu(object):
    pass


class ExistingConfig(object):
    def __init__(self, config):
        self.config = config

    @classmethod
    def from_user_prompt(cls):
        path_exist_validator = Validator.from_callable(os.path.exists, error_message='Path does not exist, choose another', move_cursor_to_end=True)
        config_directory = prompt('Existing config directory name: ',
                                  completer=PathCompleter(only_directories=True, expanduser=True),
                                  validator=path_exist_validator)
        return ExistingConfig(cls.config_from_directory(config_directory))

    @classmethod
    def config_from_directory(cls, config_directory):
        try:
            context = ExecutionContext.for_config_directory(config_directory)
        except DistributionNotFound as ex:
            ex.args = ('%s (In development? Did you forget to do a "reahl setup -- develop -N"?)' % ex.args[0],)
            raise
        context.install()
        config = StoredConfiguration(config_directory)
        config.configure(validate=False)
        return config


class RootApplication(object):
    def __init__(self, root_application):
        self.root_application = root_application

    @classmethod
    def from_user_prompt(cls):

        def user_provides_site_root():
            site_root_str = prompt('Enter the site root application locator: ', default='my.module.Example')
            if not getattr(sys.modules[__name__], site_root_str):
                print("WARNING: site_root class %s does not exist, continuing regardless." % site_root_str)
            return site_root_str

        def existing_config():
            config = ExistingConfig.from_user_prompt().config
            site_root = config.web.site_root
            return site_root

        menu = Menu('Root application module')
        menu.add_menu_item('From existing config ? ', existing_config)
        menu.add_menu_item('Provide it yourself ? ', user_provides_site_root)
        menu.prompt()

        site_root_module = menu.call_selected()

        return RootApplication(site_root_module)

    def create_site_root_config_file(self, directory_path):
        class_part = self.root_application.__name__
        module_part = self.root_application.__module__
        config_lines = [
            'from %s import %s' % (module_part, class_part),
            '',
            'web.site_root = %s' % class_part
        ]

        with open(os.path.join(directory_path.directory_path, 'web.config.py'), 'w+') as web_config_file:
            web_config_file.writelines('%s\n' % l for l in config_lines)


class DirectoryPath(object):
    def __init__(self, directory_path):
        self.directory_path = directory_path

    @classmethod
    def from_user_prompt(cls, hint=None):
        def not_path_exists(x):
            return not os.path.exists(x)
        path_exist_validator = Validator.from_callable(not_path_exists, error_message='Path exists, choose another', move_cursor_to_end=True)
        directory_path = prompt('New %sdirectory name: ' % ('%s ' % hint if hint else ''),
                                completer=WordCompleter(words=['etc-prod']), validator=path_exist_validator)
        return DirectoryPath(directory_path)

    def create_directory(self):
        os.mkdir(self.directory_path)
        return self.directory_path


class Menu(object):
    def __init__(self, message):
        #assert isinstance(Menu, parent_menu) if parent_menu else True, parent_menu
        self.message = message
        self.menu_items = []
        self.selected_key_string = None
        #self.indent_level = parent_menu.indent_level+1 if parent_menu else 0
        self.indent_level = 0

    @property
    def indent(self):
        return '  ' * self.indent_level

    def add_menu_item(self, message, callable, *args, **kwargs):
        self.menu_items.append(MenuItem(self.get_next_menu_item_key(), message, callable, *args, **kwargs))
        return len(self.menu_items)

    def get_next_menu_item_key(self):
        return len(self.menu_items)+1

    def get_menu_item(self, key):
        return self.menu_items[key-1]

    def get_selected_menu_item(self):
        if self.selected_key_string:
            return self.menu_items[int(self.selected_key_string)-1]
        return None

    def prompt(self):
        messages = ['%s' % self.message]
        allowed_words = []
        self.ensure_exit_menu_item()
        for mi in self.menu_items:
            messages.append('%s %s' % (self.indent, mi.as_option()))
            allowed_words.append('%s' % mi.key)
        messages.append('%sType your selection: ' % self.indent)

        prompt_message = '\n'.join(messages)
        allowed_menu_selection_validator = Validator.from_callable(lambda x: x in allowed_words,
                                                                   error_message='Not a valid selection',
                                                                   move_cursor_to_end=True)

        self.selected_key_string = prompt(prompt_message,
                                          validator=allowed_menu_selection_validator,
                                          completer=WordCompleter(['%s' % mi.key for mi in self.menu_items]))
        return self.selected_key_string

    def call_selected(self):
        if self.selected_key_string:
            try:
                return self.get_selected_menu_item().call_callable()
            except Exception as e:
                prompt('Something is wrong with the option you made [%s]. Press <enter> and choose another item. ' % str(e) )
                self.prompt()
                return self.call_selected()

    def ensure_exit_menu_item(self):
        if self.menu_items[-1].message != 'Exit':
            self.add_menu_item('Exit', sys.exit, 0)


class MenuItem(object):
    def __init__(self, key, message, callable_item, *args, **kwargs):
        self.key = key
        self.message = message
        self.callable_item = callable_item
        self.callable_args = args
        self.callable_kwargs = kwargs

    def as_option(self):
        return '(%s) - %s ' % (self.key, self.message)

    def call_callable(self):
        if not self.callable_args and not self.callable_kwargs:
            return self.callable_item()
        if self.callable_args and not self.callable_kwargs:
            return self.callable_item(self.callable_args)
        if not self.callable_args and self.callable_kwargs:
            return self.callable_item(self.callable_kwargs)
        return self.callable_item(self.callable_args, self.callable_kwargs)


class DatabaseConfig(object):

    def create_url(self):
        return 'database:///'

    def create_config(self, config_path):
        config_lines = [
            "reahlsystem.connection_uri = '%s'" % self.create_url()
        ]

        with open(os.path.join(config_path.directory_path, 'reahl.config.py'), 'w+') as web_config_file:
            web_config_file.writelines('%s\n' % l for l in config_lines)


class SqliteConfig(DatabaseConfig):
    def __init__(self, in_memory=False, file_path=None):
        self.in_memory = in_memory
        self.file_path = file_path

    def create_url(self):
        url = 'sqlite:///%s'
        if self.file_path:
            return url % self.file_path
        elif self.in_memory:
            return url % ':memory:'
        raise Exception('Sqlite should be in_memory or for file_path')


    @classmethod
    def from_user_prompt(cls):

        def prompt_for_file_path():
            file_path = prompt('Enter the file_path for the db', default='/tmp/myapp.db')
            return SqliteConfig(file_path=file_path)

        menu = Menu('Sqlite options')
        menu.add_menu_item('Sqlite - in memory', SqliteConfig, in_memory=True)
        menu.add_menu_item('Sqlite - file', prompt_for_file_path)
        menu.prompt()

        return menu.call_selected()


class PostgresqlConfig(DatabaseConfig):
    def __init__(self, username, password, hostname, port, database_name):
        self.username = username
        self.password = password
        self.hostname = hostname
        self.port = port
        self.database_name = database_name

    def create_url(self):
        username_part = self.username if self.username else ''
        password_part = ':%s' % self.password if self.password else ''
        hostname_part = '@%s' % self.hostname if self.hostname else ''
        port_part = ':%s' % self.port if self.port else ''
        db_part = '/%s' % self.database_name if self.database_name else ''
        return 'postgresql://%s%s%s%s%s' % (username_part, password_part, hostname_part, port_part, db_part)

    @classmethod
    def from_user_prompt(cls):
        return PostgresqlConfig(
            prompt('username ? ', default=''),
            prompt('password ? ', default=''),
            prompt('hostname ? ', default=''),
            prompt('port ?', default=''),
            prompt('database name ? ', default='reahl'))


class CloudPlatform(object):
    def create_config(self):
        pass


class LocalApp(CloudPlatform):

    def __init__(self, database_config):
        self.database_config = database_config

    @classmethod
    def from_user_prompt(cls):
        menu = Menu('Database type')
        menu.add_menu_item('Sqlite', SqliteConfig.from_user_prompt)
        menu.add_menu_item('Postgresql', PostgresqlConfig.from_user_prompt)
        # menu.add_menu_item('MySql', MySql)
        menu.prompt()
        database_config = menu.call_selected()

        return LocalApp(database_config)

    def create_config(self, config_path):
        self.database_config.create_config(config_path)


class Platform(object):
    def __init__(self, application):
        self.application = application

    @classmethod
    def from_user_prompt(cls):

        def not_yet_available():
            raise Exception('This option is not yet available')

        menu = Menu('Application platform')
        menu.add_menu_item('local, on this machine', LocalApp.from_user_prompt)
        menu.add_menu_item('AWS', not_yet_available)
        menu.add_menu_item('pythonanywhere', not_yet_available)
        # menu.add_menu_item('Docker')
        # menu.add_menu_item('Heroku')
        menu.prompt()

        return menu.call_selected()

    def create_config(self, new_config_path):
        self.application.create_config(new_config_path)



class CreateConfig(ProductionCommand):
    """Create new set of configuration settings."""
    keyword = 'createconfig'

    def assemble(self):
        #super(AddConfig, self).assemble()
        pass


    def execute(self, args):

        directories_to_remove = []
        try:

            print('\n')
            new_config_path = DirectoryPath.from_user_prompt(hint='config')
            config_dir = new_config_path.create_directory()
            directories_to_remove.append(config_dir)

            print('\n')
            site_root = RootApplication.from_user_prompt()
            site_root.create_site_root_config_file(new_config_path)

            print('\n')
            platform = Platform.from_user_prompt()
            platform.create_config(new_config_path)
            print('\n')
            print('Created config in [%s]' % new_config_path.directory_path)

        except :
            print('\nError, cleaning up...')
            for directory_path in directories_to_remove:
                print('Removing: %s' % directory_path)
                shutil.rmtree(directory_path)
            print('Error, cleaning up...done')
            raise


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


class ExportStaticFiles(ProductionCommand):
    """Exports all static web assets found in web.libraries to a specified directory."""
    keyword = 'exportstatics'
    def assemble(self):
        super(ExportStaticFiles, self).assemble()
        self.parser.add_argument('destination_directory', type=str,  help='the destination directory to export to')

    def execute(self, args):
        super(ExportStaticFiles, self).execute(args)
        if os.path.exists(args.destination_directory):
            raise DomainException(message='The path %s already exists. Please move it out of the way first.' % args.destination_directory)
        try:
            os.mkdir(args.destination_directory)
        except Exception as ex:
            raise DomainException(message='Could not create %s: %s' % (args.destination_directory, six.text_type(ex)))
            
        for packaged_file in self.config.web.frontend_libraries.packaged_files():
            print('extracting %s' % packaged_file.full_path)
            shutil.copy(packaged_file.full_path, args.destination_directory)


