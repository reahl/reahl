# Copyright 2020 Reahl Software Services (Pty) Ltd. All rights reserved.
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

import queue
import textwrap

from pathlib import Path
from unittest.mock import patch

from reahl.webdev.commands import CreateConfig
from reahl.tofu import temp_dir, Fixture, file_with
from reahl.tofu.pytestsupport import with_fixtures


class PromptStub:
    def __init__(self):
        self.messages_responses = queue.Queue()

    def __call__(self, message, *args, **kwargs):
        assert not self.messages_responses.empty(), 'No Response for message: %s' % message
        (expected_message, response) = self.messages_responses.get()
        assert message == expected_message, 'Message not expected: %s'
        return response

    def when_prompted_type(self, message, response):
        expected_message = message
        if isinstance(message, list):
            expected_message = self.delimit_with_newlines(message)
        self.messages_responses.put((expected_message, response))

    def delimit_with_newlines(self, message_list):
        return '\n'.join(message_list)


class PromptFixture(Fixture):
    def run_command(self):
        with patch(CreateConfig.__module__+'.prompt', new=self.prompt):
            c = CreateConfig()
            c.do([])

    def new_working_directory(self):
        return temp_dir()

    def new_prompt(self):
        return PromptStub()

    def new_etc_path(self):
        return Path(self.working_directory.name).joinpath('etc')

    def new_existing_etc_path(self):
        path = Path(self.working_directory.name).joinpath('existing-etc')
        path.mkdir()
        return path

    def new_existing_etc(self):
        class Etc:
            reahl_config = file_with(str(self.existing_etc_path.joinpath('reahl.config.py')), '\n'.join(self.new_expected_reahl_config(root_egg='reahl-doc')))
            web_config = file_with(str(self.existing_etc_path.joinpath('web.config.py')), '\n'.join(self.new_expected_web_config(module='reahl.doc.examples.tutorial.addresslist.addresslist', root_class='AddressBookUI')))
        return Etc

    config_directory_question = 'New config directory name:'

    main_component_menu = ['What is the name of your main component?',
                           ' (1) - From existing config?  ',
                           ' (2) - Provide it yourself?  ',
                           ' (3) - Exit ',
                           'Type your selection: ']

    root_application_menu = ['Root application module',
                            ' (1) - From existing config?  ',
                            ' (2) - Provide it yourself?  ',
                            ' (3) - Exit ',
                            'Type your selection: ']

    debug_menu = ['Configure the application to run in DEBUG mode',
                  ' (1) - Yes?  ',
                  ' (2) - No?  ',
                  ' (3) - Exit ',
                  'Type your selection: ']

    database_type_menu = ['Database type',
                          ' (1) - Sqlite ',
                          ' (2) - Postgresql ',
                          ' (3) - MySql ',
                          ' (4) - Exit ',
                          'Type your selection: ']

    sqlite_menu = ['SQLite options',
                   ' (1) - SQLite - in memory ',
                   ' (2) - SQLite - file ',
                   ' (3) - Exit ',
                   'Type your selection: ']

    def new_expected_reahl_config(self, root_egg='myegg', connection_uri='None', debug='False'):
        return textwrap.dedent('''
            reahlsystem.root_egg = '%s'
            reahlsystem.debug = %s
            reahlsystem.connection_uri = '%s'
        ''' % (root_egg, debug, connection_uri) ).splitlines()

    def new_expected_web_config(self, module='myegg', root_class='AddressBookUI'):
        return textwrap.dedent('''
            from %s import %s

            web.site_root = %s
        ''' % (module, root_class, root_class) ).splitlines()

    def get_lines_of_file(self, filename):
        with open(str(self.etc_path.joinpath(filename))) as f:
            return f.read().splitlines()

    def navigate_up_to_database(self):
        expected_interaction = self.prompt
        expected_interaction.when_prompted_type('New config directory name: ', str(self.etc_path))
        expected_interaction.when_prompted_type(self.main_component_menu, 2)
        expected_interaction.when_prompted_type('Enter the main component name', 'mycomponent')
        expected_interaction.when_prompted_type(self.root_application_menu, 2)
        expected_interaction.when_prompted_type('Enter the site root module: ', 'reahl.doc.examples.tutorial.hello.hello')
        expected_interaction.when_prompted_type('Enter the site root class: ', 'HelloUI')

    def navigate_to_completion_from_debug(self):
        expected_interaction = self.prompt
        expected_interaction.when_prompted_type(self.debug_menu, 1)
        expected_interaction.when_prompted_type(self.database_type_menu, 1)
        expected_interaction.when_prompted_type(self.sqlite_menu, 2)
        expected_interaction.when_prompted_type('Enter the file_path for the db: ', '/tmp/reahl-sqlite.db')


@with_fixtures(PromptFixture)
def test_reading_from_existing_config(fixture):

    etc = fixture.new_existing_etc()

    expected_interaction = fixture.prompt
    expected_interaction.when_prompted_type('New config directory name: ', str(fixture.etc_path))
    expected_interaction.when_prompted_type(fixture.main_component_menu, 1)
    expected_interaction.when_prompted_type('Existing config directory name: ', str(fixture.existing_etc_path))
    expected_interaction.when_prompted_type(fixture.root_application_menu, 1)

    fixture.navigate_to_completion_from_debug()
    fixture.run_command()

    assert fixture.get_lines_of_file('reahl.config.py') == fixture.new_expected_reahl_config(root_egg='reahl-doc', debug=True, connection_uri='sqlite:////tmp/reahl-sqlite.db')
    assert fixture.get_lines_of_file('web.config.py') == fixture.new_expected_web_config(module='reahl.doc.examples.tutorial.addresslist.addresslist', root_class='AddressBookUI')


@with_fixtures(PromptFixture)
def test_manual_config(fixture):

    expected_interaction = fixture.prompt
    expected_interaction.when_prompted_type('New config directory name: ', str(fixture.etc_path))
    expected_interaction.when_prompted_type(fixture.main_component_menu, 2)
    expected_interaction.when_prompted_type('Enter the main component name', 'mycomponent')
    expected_interaction.when_prompted_type(fixture.root_application_menu, 2)
    expected_interaction.when_prompted_type('Enter the site root module: ', 'reahl.doc.examples.tutorial.hello.hello')
    expected_interaction.when_prompted_type('Enter the site root class: ', 'HelloUI')

    fixture.navigate_to_completion_from_debug()
    fixture.run_command()

    assert fixture.get_lines_of_file('reahl.config.py') == fixture.new_expected_reahl_config(root_egg='mycomponent', debug=True, connection_uri='sqlite:////tmp/reahl-sqlite.db')
    assert fixture.get_lines_of_file('web.config.py') == fixture.new_expected_web_config(module='reahl.doc.examples.tutorial.hello.hello', root_class='HelloUI')


@with_fixtures(PromptFixture)
def test_database_sqlite(fixture):

    expected_interaction = fixture.prompt
    fixture.navigate_up_to_database()
    
    expected_interaction.when_prompted_type(fixture.debug_menu, 1)
    expected_interaction.when_prompted_type(fixture.database_type_menu, 1)
    expected_interaction.when_prompted_type(fixture.sqlite_menu, 2)
    expected_interaction.when_prompted_type('Enter the file_path for the db: ', '/tmp/reahl-sqlite.db')

    fixture.run_command()

    assert fixture.get_lines_of_file('reahl.config.py') == fixture.new_expected_reahl_config(root_egg='mycomponent', debug=True, connection_uri='sqlite:////tmp/reahl-sqlite.db')
 

@with_fixtures(PromptFixture)
def test_database_postgresql(fixture):

    expected_interaction = fixture.prompt
    fixture.navigate_up_to_database()
    
    expected_interaction.when_prompted_type(fixture.debug_menu, 1)
    expected_interaction.when_prompted_type(fixture.database_type_menu, 2)
    expected_interaction.when_prompted_type('username ? ', 'pgsqluser')
    expected_interaction.when_prompted_type('password (will be echoed to screen) ? ', 'topsecret')
    expected_interaction.when_prompted_type('hostname ? ', 'somehost')
    expected_interaction.when_prompted_type('port ? ', '123')
    expected_interaction.when_prompted_type('database name ? ', 'testpostgresqldb')

    fixture.run_command()

    assert fixture.get_lines_of_file('reahl.config.py') == fixture.new_expected_reahl_config(root_egg='mycomponent', debug=True, connection_uri='postgresql://pgsqluser:topsecret@somehost:123/testpostgresqldb')


@with_fixtures(PromptFixture)
def test_database_postgresql_empties(fixture):

    expected_interaction = fixture.prompt
    fixture.navigate_up_to_database()
    
    expected_interaction.when_prompted_type(fixture.debug_menu, 1)
    expected_interaction.when_prompted_type(fixture.database_type_menu, 2)
    expected_interaction.when_prompted_type('username ? ', '')
    expected_interaction.when_prompted_type('password (will be echoed to screen) ? ', '')
    expected_interaction.when_prompted_type('hostname ? ', '')
    expected_interaction.when_prompted_type('port ? ', '')
    expected_interaction.when_prompted_type('database name ? ', '')

    fixture.run_command()

    assert fixture.get_lines_of_file('reahl.config.py') == fixture.new_expected_reahl_config(root_egg='mycomponent', debug=True, connection_uri='postgresql://')


@with_fixtures(PromptFixture)
def test_database_mysql(fixture):

    expected_interaction = fixture.prompt
    fixture.navigate_up_to_database()

    expected_interaction.when_prompted_type(fixture.debug_menu, 1)
    expected_interaction.when_prompted_type(fixture.database_type_menu, 3)
    expected_interaction.when_prompted_type('username ? ', 'mysqluser')
    expected_interaction.when_prompted_type('password (will be echoed to screen) ? ', 'topsecret2')
    expected_interaction.when_prompted_type('hostname ? ', 'anotherhost')
    expected_interaction.when_prompted_type('port ? ', '456')
    expected_interaction.when_prompted_type('database name ? ', 'testmysqldb')

    fixture.run_command()

    assert fixture.get_lines_of_file('reahl.config.py') == fixture.new_expected_reahl_config(root_egg='mycomponent', debug=True, connection_uri='mysql://mysqluser:topsecret2@anotherhost:456/testmysqldb')


