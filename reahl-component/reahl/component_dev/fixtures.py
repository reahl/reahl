# Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from reahl.tofu import Fixture

from reahl.component.context import ExecutionContext
from reahl.component.dbutils import SystemControl
from reahl.component.config import StoredConfiguration

class ConfiguredFixture(Fixture):
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
    



