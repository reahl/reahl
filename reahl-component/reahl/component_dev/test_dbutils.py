# Copyright 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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
from nose.tools import istest
from reahl.tofu import test, Fixture, vassert, expected

from reahl.stubble import easter_egg

from reahl.component.dbutils import DatabaseControl, SystemControl, CouldNotFindDatabaseControlException

from reahl.component.config import Configuration, ReahlSystemConfig


class TestDatabaseControl(DatabaseControl):
    control_matching_regex = r'^myprefix://'
    uri_regex_string = r'myprefix://(?P<database>.*):(?P<user>.*):(?P<password>.*):(?P<host>.*):(?P<port>.*)$'


class DBControlFixture(Fixture):
    def new_config(self):
        line = 'TestDatabaseControl = reahl.component_dev.test_dbutils:TestDatabaseControl'
        easter_egg.add_entry_point_from_line('reahl.component.databasecontrols', line)

        config = Configuration()
        config.reahlsystem = ReahlSystemConfig()
        return config

        
@test(DBControlFixture)
def finding_database_control(fixture):
    """The correct DatabaseControl will be found from the entry point
       reahl.component.databasecontrols for a given
       reahlsystem.connection_uri config setting based on its control_matching_regex.

    """
    fixture.config.reahlsystem.connection_uri = 'myprefix://theuser:thepasswd@thehost:123/thedb'
    system_control = SystemControl(fixture.config)
    vassert( isinstance(system_control.db_control, TestDatabaseControl) )

    fixture.config.reahlsystem.connection_uri = 'wrongprefix://theuser:thepasswd@thehost:123/thedb'
    with expected(CouldNotFindDatabaseControlException):
        SystemControl(fixture.config)


@test(DBControlFixture)
def database_control_settings(fixture):
    """DatabaseControl settings are read from the
       reahlsystem.connection_uri config setting parsed as an RFC1808 URI
    """
    fixture.config.reahlsystem.connection_uri = 'myprefix://theuser:thepasswd@thehost:123/thedb'
    system_control = SystemControl(fixture.config)

    vassert( system_control.db_control.database_name == 'thedb' )
    vassert( system_control.db_control.user_name == 'theuser' )
    vassert( system_control.db_control.password == 'thepasswd' )
    vassert( system_control.db_control.host == 'thehost' )
    vassert( system_control.db_control.port == 123 )




