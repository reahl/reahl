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

import platform
import sys
import os
import os.path
import re
import subprocess

import pkg_resources

from reahl.dev.devdomain import Project
from reahl.dev.devshell import WorkspaceCommand
from reahl.dev.exceptions import CouldNotConfigureServer

from reahl.component.shelltools import Executable, Command
from reahl.component.exceptions import DomainException
from reahl.component.config import StoredConfiguration
from reahl.component.decorators import memoized
from reahl.webdev.webserver import ReahlWebServer, ServerSupervisor

from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.completion.filesystem import PathCompleter


class ServeCurrentProject(WorkspaceCommand):
    """Serves the project configured in the given directory (defaults to ./etc)."""
    keyword = 'serve'

    def assemble(self):
        super().assemble()
        self.parser.add_argument('-s', '--seconds-between-restart', action='store', type=int, dest='max_seconds_between_restarts',
                                 default=3, help='poll only every n seconds for filesystem changes (optional)')
        self.parser.add_argument('-d', '--monitor-directory', action='append', dest='monitored_directories', default=[],
                                 help='add a directory to monitor for changes'
                                 ' (the current directory is always included)')
        self.parser.add_argument('-D', '--dont-restart', action='store_false', dest='restart', default=True, 
                                 help='run as unsupervised server which does not monitor for filesystem changes')
        self.parser.add_argument('config_directory', default='etc', nargs='?',
                                 help='the configuration directory of the system to serve')

    def execute(self, args):
        project = Project.from_file(self.workspace, self.workspace.startup_directory)
        with project.paths_set():
            try:
                if args.restart:
                    ServerSupervisor(sys.argv[1:]+['--dont-restart'],
                                     args.max_seconds_between_restarts,
                                     ['.']+args.monitored_directories).run()
                else:
                    config_directory = args.config_directory
                    print('\nUsing config from %s\n' % config_directory, flush=True)
                    
                    try:
                        reahl_server = ReahlWebServer.from_config_directory(config_directory)
                    except pkg_resources.DistributionNotFound as ex:
                        terminate_keys = 'Ctrl+Break' if platform.system() == 'Windows' else 'Ctrl+C'
                        print('\nPress %s to terminate\n\n' % terminate_keys, flush=True)
                        raise CouldNotConfigureServer(ex)

                    reahl_server.start()
                    print('\n\nServing http on port %s, https on port %s (config=%s, flush=True)' % \
                                     (reahl_server.port, reahl_server.encrypted_port, config_directory))
                    terminate_keys = 'Ctrl+Break' if platform.system() == 'Windows' else 'Ctrl+C'
                    print('\nPress %s to terminate\n\n' % terminate_keys, flush=True)

                    notify = Executable('notify-send')
                    try:
                        notify.call(['Reahl', 'Server restarted'])
                    except:
                        pass

                    reahl_server.wait_for_server_to_complete()
            except KeyboardInterrupt:
                print('\nShutting down', flush=True)
            except CouldNotConfigureServer as ex:
                print(ex, flush=True)
        return 0


class SyncFiles(Command):
    """Uses the sitecopy program to upload / sync static files to a remote webserver."""
    keyword = 'syncfiles'

    def get_site_name(self):
        if not os.path.isfile('sitecopy.rc'):
            raise DomainException(message='Could not find a sitecopy config file "sitecopy.rc" in the current directory')
        with open('sitecopy.rc') as config_file:
            for line in config_file:
                match = re.match('.*(?!#).*site\s+(\S+)', line)
                if match:
                    return match.group(1)
        raise DomainException(message='Cannot find the site name in sitecopy.rc')

    def assemble(self):
        self.parser.add_argument('-f', '--fetch-first', action='store_true', dest='fetch_first',
                                 help='first fetch data from the site to ensure we are in sync')
        self.parser.add_argument('site_name', default=None, nargs='?',
                                 help='the name of the site as listed in sitecopy.rc')

    def execute(self, args):
        super().execute(args)
        self.sitecopy = Executable('sitecopy')

        try:
            site_name = args.site_name or self.get_site_name()
            local_info_file = os.path.expanduser(os.path.join('~', '.sitecopy', site_name))
            if args.fetch_first or not os.path.exists(local_info_file):
                if os.path.exists(local_info_file):
                    os.remove(local_info_file)
                self.sitecopy.check_call('-r sitecopy.rc --fetch'.split()+[site_name])
            self.sitecopy.check_call('-r sitecopy.rc --update'.split()+[site_name])
        except subprocess.CalledProcessError as ex:
            raise DomainException(message='Running "%s" failed with exit code %s' % (' '.join(ex.cmd), ex.returncode))


class Menu:
    def __init__(self, message):
        self.message = message
        self.menu_items = []
        self.selected_key_string = None
        self.indent_level = 0

    @property
    def indent(self):
        return '  ' * self.indent_level

    def add_menu_item(self, message, callable_, *args, **kwargs):
        menu_item = MenuItem(message, callable_, args, kwargs)
        self.menu_items.append(menu_item)
        return menu_item

    def get_menu_item(self, key):
        return self.menu_items[key-1]

    def prompt(self):
        messages = [self.message]
        allowed_words = []
        self.ensure_exit_menu_item_exists()
        for index, mi in enumerate(self.menu_items):
            key = index + 1
            messages.append('%s %s' % (self.indent, mi.as_option(key)))
            allowed_words.append('%s' % key)
        messages.append('%s%s: ' % (self.indent, 'Type your selection'))

        prompt_message = '\n'.join(messages)
        allowed_menu_selection_validator = Validator.from_callable(lambda x: x in allowed_words,
                                                                   error_message='Not a valid selection',
                                                                   move_cursor_to_end=True)

        selected_key_string = prompt(prompt_message,
                                     validator=allowed_menu_selection_validator,
                                     completer=WordCompleter(allowed_words))
        return self.get_menu_item(int(selected_key_string))

    def show(self):
        selected = self.prompt()
        try:
            return selected.call_callable()
        except Exception as e:
            prompt('Something is wrong with the option you chose [%s]. Press <enter> and choose another item.' % str(e))
            return self.show()

    def ensure_exit_menu_item_exists(self):
        exit_str = 'Exit'
        if self.menu_items[-1].message != exit_str:
            self.add_menu_item(exit_str, sys.exit, 0)


class MenuItem:
    def __init__(self, message, callable_item, args, kwargs):
        self.message = message
        self.callable_item = callable_item
        self.callable_args = args
        self.callable_kwargs = kwargs

    def as_option(self, key):
        return '(%s) - %s ' % (key, self.message)

    def call_callable(self):
        return self.callable_item(*self.callable_args, **self.callable_kwargs)


class BasicConfig:
    def __init__(self):
        self.target_config_directory = None
        self.root_egg = None
        self.site_root = None
        self.reahl_debug = True
        self.database = None

    def ask_detail_questions(self):
        self.ask_target_directory()
        self.ask_root_egg()
        self.ask_site_root()
        self.ask_reahl_debug()
        self.ask_database_questions()

    def ask_database_questions(self):
        menu = Menu('Database type')
        menu.add_menu_item('Sqlite', SQLiteConfig)
        menu.add_menu_item('Postgresql', PostgreSQLConfig)
        menu.add_menu_item('MySql', MySQLConfig)
        self.database = menu.show()
        self.database.ask_detail_questions()

    def ask_target_directory(self):
        def not_path_exists(x):
            return not os.path.exists(x)
        path_exist_validator = Validator.from_callable(not_path_exists, error_message='Path exists, choose another', move_cursor_to_end=True)
        self.target_config_directory = prompt('%s: ' % 'New config directory name',
                                              completer=WordCompleter(words=['etc-prod']), validator=path_exist_validator)

    def ask_reahl_debug(self):
        menu = Menu('Configure the application to run in DEBUG mode')
        menu.add_menu_item('Yes? ', lambda: True)
        menu.add_menu_item('No? ', lambda: False)
        self.reahl_debug = menu.show()

    def ask_root_egg(self):
        menu = Menu('What is the name of your main component?')
        menu.add_menu_item('From existing config? ', self.get_root_egg_from_existing_config)
        menu.add_menu_item('Provide it yourself? ', self.get_root_egg_from_user)
        self.root_egg = menu.show()

    def get_root_egg_from_user(self):
        return prompt('Enter the main component name', default=os.path.basename(os.getcwd()))

    def get_root_egg_from_existing_config(self):
        return self.existing_config.reahlsystem.root_egg

    def ask_site_root(self):
        menu = Menu('Root application module')
        menu.add_menu_item('From existing config? ', self.get_site_root_from_existing_config)
        menu.add_menu_item('Provide it yourself? ', self.get_site_root_from_user)
        self.site_root = menu.show()

    def get_site_root_from_user(self):
        module_name = prompt('Enter the site root module: ', default='my.module')
        class_name = prompt('Enter the site root class: ', default='MyApp')
        exec('from %s import %s' % (module_name, class_name))
        return getattr(sys.modules[module_name], class_name)

    def get_site_root_from_existing_config(self):
        return self.existing_config.web.site_root

    @property
    @memoized
    def existing_config(self):
        path_exist_validator = Validator.from_callable(os.path.exists,
                                                       error_message='Path does not exist, choose existing path',
                                                       move_cursor_to_end=True)
        config_directory = prompt('%s: ' % 'Existing config directory name',
                                  completer=PathCompleter(only_directories=True, expanduser=True),
                                  validator=path_exist_validator)
        return self.read_existing_config(config_directory)

    def read_existing_config(self, config_directory):
        config = StoredConfiguration(config_directory)
        config.configure(validate=False)
        return config


class ConfigFile:
    def __init__(self, file_path):
        self.file_path = file_path
        self.config_lines = []

    def add_line(self, line):
        self.config_lines.append(line)

    def write(self):
        with open(self.file_path, 'w+') as config_file:
            config_file.writelines('%s\n' % l for l in self.config_lines)


class DatabaseConfig:
    def __init__(self, db_url_scheme):
        self.db_url_scheme = db_url_scheme
        self.username = None
        self.password = None
        self.hostname = None
        self.port = None
        self.database_name = None

    @property
    def url(self):
        username_part = self.username if self.username else ''
        password_part = ':%s' % self.password if self.password else ''
        hostname_part = '@%s' % self.hostname if self.hostname else ''
        port_part = ':%s' % self.port if self.port else ''
        db_part = '/%s' % self.database_name if self.database_name else ''
        return '%s://%s%s%s%s%s' % (self.db_url_scheme, username_part, password_part, hostname_part, port_part, db_part)

    @property
    def hostname_default(self):
        return ''

    @property
    def database_name_default(self):
        return 'reahl'

    @property
    def port_default(self):
        return ''

    def ask_detail_questions(self):
        self.username = prompt('username ? ', default='')
        self.password = prompt('password (will be echoed to screen) ? ', default='')
        self.hostname = prompt('hostname ? ', default=self.hostname_default)
        self.port = prompt('port ? ', default=self.port_default)
        self.database_name = prompt('database name ? ', default=self.database_name_default)


class SQLiteConfig(DatabaseConfig):
    def __init__(self):
        super().__init__('sqlite')
        self.in_memory = False
        self.file_path = False

    @property
    def url(self):
        if self.file_path:
            self.database_name = self.file_path
        elif self.in_memory:
            self.database_name = ':memory:'
        if self.database_name:
            return super().url
        raise Exception('SQLite should be in_memory or for file_path')

    def set_to_in_memory(self):
        self.in_memory = True

    def set_file_path(self):
        file_path = prompt('Enter the file_path for the db: ', default='/tmp/myapp.db')
        self.file_path = file_path

    def ask_detail_questions(self):
        menu = Menu('SQLite options')
        menu.add_menu_item('SQLite - in memory', self.set_to_in_memory)
        menu.add_menu_item('SQLite - file', self.set_file_path)
        menu.show()


class PostgreSQLConfig(DatabaseConfig):
    def __init__(self):
        super().__init__('postgresql')


class MySQLConfig(DatabaseConfig):
    def __init__(self):
        super().__init__('mysql')


class CreateConfig(WorkspaceCommand):
    """Interactively create new set of configuration settings."""
    keyword = 'createconfig'

    def execute(self, args):
        print('\n')

        basic_config = BasicConfig()
        basic_config.ask_detail_questions()

        os.mkdir(basic_config.target_config_directory)
        self.create_reahl_system_config_file(basic_config)
        self.create_web_config_file(basic_config)

        print('\n')
        print('%s: %s' % ('Created config in', basic_config.target_config_directory))

    def create_reahl_system_config_file(self, basic_config):
        reahl_config = ConfigFile(os.path.join(basic_config.target_config_directory, 'reahl.config.py'))
        reahl_config.add_line('')
        reahl_config.add_line("reahlsystem.root_egg = '%s'" % str(basic_config.root_egg))
        reahl_config.add_line('reahlsystem.debug = %s' % str(basic_config.reahl_debug))
        reahl_config.add_line("reahlsystem.connection_uri = '%s'" % basic_config.database.url)
        reahl_config.write()

    def create_web_config_file(self, basic_config):
        class_part = basic_config.site_root.__name__
        module_part = basic_config.site_root.__module__
        reahl_config = ConfigFile(os.path.join(basic_config.target_config_directory, 'web.config.py'))
        reahl_config.add_line('')
        reahl_config.add_line('from %s import %s' % (module_part, class_part))
        reahl_config.add_line('')
        reahl_config.add_line('web.site_root = %s' % class_part)
        reahl_config.write()
