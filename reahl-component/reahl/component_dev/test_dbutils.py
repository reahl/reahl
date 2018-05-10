# Copyright 2016, 2017, 2018 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from __future__ import print_function, unicode_literals, absolute_import, division

from reahl.tofu import Fixture, expected
from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import easter_egg

from reahl.component.dbutils import DatabaseControl, SystemControl, CouldNotFindDatabaseControlException
from reahl.component.config import Configuration, ReahlSystemConfig


class StubDatabaseControl(DatabaseControl):
    control_matching_regex = r'^myprefix://'
    uri_regex_string = r'myprefix://(?P<database>.*):(?P<user>.*):(?P<password>.*):(?P<host>.*):(?P<port>.*)$'


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


@with_fixtures(DBControlFixture)
def test_database_control_settings(dbcontrol_fixture):
    """DatabaseControl settings are read from the
       reahlsystem.connection_uri config setting parsed as an RFC1808 URI
    """
    fixture = dbcontrol_fixture
    fixture.config.reahlsystem.connection_uri = 'myprefix://theuser:thepasswd@thehost:123/thedb'
    system_control = SystemControl(fixture.config)

    assert system_control.db_control.database_name == 'thedb' 
    assert system_control.db_control.user_name == 'theuser' 
    assert system_control.db_control.password == 'thepasswd' 
    assert system_control.db_control.host == 'thehost' 
    assert system_control.db_control.port == 123 




