# Copyright 2016-2020 Reahl Software Services (Pty) Ltd. All rights reserved.
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



import urllib.parse

from reahl.tofu import Fixture, expected, scenario
from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import easter_egg

from reahl.component.exceptions import ProgrammerError
from reahl.component.dbutils import DatabaseControl, SystemControl, CouldNotFindDatabaseControlException
from reahl.component.config import Configuration, ReahlSystemConfig


class StubDatabaseControl(DatabaseControl):
    control_matching_regex = r'^myprefix://'


class DBControlFixture(Fixture):
    def new_config(self):
        line = 'StubDatabaseControl = reahl.component_dev.test_dbutils:StubDatabaseControl'
        easter_egg.add_entry_point_from_line('reahl.component.databasecontrols', line)

        config = Configuration()
        config.reahlsystem = ReahlSystemConfig()
        return config


@with_fixtures(DBControlFixture)
def test_finding_database_control(dbcontrol_fixture):
    """The correct DatabaseControl will be found from the entry point
       reahl.component.databasecontrols for a given
       reahlsystem.connection_uri config setting based on its control_matching_regex.

    """
    fixture = dbcontrol_fixture
    fixture.config.reahlsystem.connection_uri = 'myprefix://theuser:thepasswd@thehost:123/thedb'
    system_control = SystemControl(fixture.config)
    assert isinstance(system_control.db_control, StubDatabaseControl) 

    fixture.config.reahlsystem.connection_uri = 'wrongprefix://theuser:thepasswd@thehost:123/thedb'
    with expected(CouldNotFindDatabaseControlException):
        SystemControl(fixture.config)


class URIScenarios(Fixture):

    @scenario
    def all_settings_given(self):
        self.uri = 'myprefix://theuser:thepasswd@thehost:123/thedb'
        self.database_name = 'thedb'
        self.user_name = 'theuser'
        self.password = 'thepasswd'
        self.host = 'thehost'
        self.port = 123

    @scenario
    def not_all_settings_given(self):
        self.uri = 'myprefix://theuser@thehost/thedb'
        self.database_name = 'thedb'
        self.user_name = 'theuser'
        self.password = None
        self.host = 'thehost'
        self.port = None

    @scenario
    def minimal(self):
        self.uri = 'myprefix:///:memory:'
        self.database_name = ':memory:'
        self.user_name = None
        self.password = None
        self.host = None
        self.port = None


@with_fixtures(DBControlFixture, URIScenarios)
def test_database_control_settings(dbcontrol_fixture, uri_scenario):
    """DatabaseControl settings are read from the
       reahlsystem.connection_uri config setting parsed as an RFC1808 URI
    """
    fixture = dbcontrol_fixture
    fixture.config.reahlsystem.connection_uri = uri_scenario.uri
    system_control = SystemControl(fixture.config)

    assert system_control.db_control.database_name == uri_scenario.database_name
    assert system_control.db_control.user_name == uri_scenario.user_name
    assert system_control.db_control.password == uri_scenario.password
    assert system_control.db_control.host == uri_scenario.host
    assert system_control.db_control.port == uri_scenario.port


@with_fixtures(DBControlFixture)
def test_minimum_required_database_control_settings(dbcontrol_fixture):
    """The minimum an uri should contain is a database name.
    """
    fixture = dbcontrol_fixture
    fixture.config.reahlsystem.connection_uri = 'myprefix:///'
    with expected(ProgrammerError, test='Please specify a database name in reahlsystem.connection_uri'):
        SystemControl(fixture.config)


@with_fixtures(DBControlFixture)
def test_database_control_url_safe_parts(dbcontrol_fixture):
    """URL parts are unquoted, as they may contain URL quoted characters.
    """
    fixture = dbcontrol_fixture

    def quote(values):
        return [urllib.parse.quote(i) for i in values]

    expected_parts \
        = [expected_user_name, expected_password, expected_host, expected_db] \
        = ['usêrname', 'p#=sword', 'hõst', 'd~t∀b^s∊']
    uri = 'myprefix://%s:%s@%s:456/%s' % tuple(quote(expected_parts))
    assert not set(expected_parts).intersection(quote(expected_parts))

    fixture.config.reahlsystem.connection_uri = uri

    system_control = SystemControl(fixture.config)

    assert system_control.db_control.user_name == expected_user_name
    assert system_control.db_control.password == expected_password
    assert system_control.db_control.host == expected_host
    assert system_control.db_control.port == 456
    assert system_control.db_control.database_name == expected_db




