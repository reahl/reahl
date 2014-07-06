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


from __future__ import unicode_literals
from __future__ import print_function
from reahl.tofu import Fixture, set_up, tear_down

from reahl.component.context import ExecutionContext
from reahl.component.dbutils import SystemControl
from reahl.component.config import StoredConfiguration


class CleanDatabase(Fixture):
    """A Fixture to be used as run fixture. Upon set up, it creates a new empty database with the
       correct database schema for the project and sets up any persistent classes for use with that 
       schema. It also connects to the database. Upon tear down, the Fixture disconnects from the database.
    """
    commit = False

    def new_reahlsystem(self):
        return self.config.reahlsystem

    def new_config(self):
        config = StoredConfiguration('etc/')
        config.configure()
        return config

    def new_context(self, config=None, system_control=None):
        context = ExecutionContext()
        context.set_config( config or self.config )
        context.set_system_control(system_control or self.system_control)
        return context

    def new_system_control(self):
        return SystemControl(self.config)

    def new_test_dependencies(self):
        return []

    @set_up
    def init_database(self):
        with self.context:
            orm_control = self.config.reahlsystem.orm_control
            for dependency in self.test_dependencies:
                orm_control.instrument_classes_for(dependency)
            if not self.system_control.is_in_memory:
                self.system_control.initialise_database(yes=True)
            self.system_control.connect()

    @tear_down
    def disconnect(self):
        with self.context:
            self.system_control.disconnect()




