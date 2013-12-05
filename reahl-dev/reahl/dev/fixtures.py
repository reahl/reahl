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

# Copyright (C) 2006 Reahl Software Services (Pty) Ltd.  All rights reserved. (www.reahl.org)


from reahl.tofu import Fixture, set_up, tear_down

from reahl.component_dev.fixtures import ConfiguredFixture

class CleanDatabase(ConfiguredFixture):
    """A Fixture to be used as run fixture. Upon set up, it creates a new empty database with the
       correct database schema for the project and sets up any persistent classes for use with that 
       schema. It also connects to the database. Upon tear down, the Fixture disconnects from the database.
    """
    commit = False
    @set_up
    def init_database(self):
        with self.context:
            orm_control = self.config.reahlsystem.orm_control
            for dependency in self.test_dependencies:
                orm_control.instrument_classes_for(dependency)
            self.system_control.initialise_database(yes=True)
            self.system_control.connect()

    @tear_down
    def disconnect(self):
        with self.context:
            self.system_control.disconnect()




