# Copyright 2013-2020 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.component.migration import Migration


class ReahlCommandsReahlSchemaInitialise(Migration):
    def schedule_upgrades(self):
        self.orm_control.assert_dialect(self, 'postgresql')
        self.schedule('data', self.orm_control.initialise_schema_version_for, egg_name='reahl-commands', egg_version='4.0.0a1')

