# Copyright 2019-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from alembic import op

from reahl.component.migration import Migration
from sqlalchemy import UnicodeText, Unicode, Column, Integer, String, PrimaryKeyConstraint




class CreateDatabase(Migration):
    def schedule_upgrades(self):
        self.orm_control.assert_dialect(self, 'postgresql')
        self.schedule('alter', op.create_table, 'reahl_schema_version',
                      Column('id', Integer(), nullable=False),
                      Column('version', String(length=50), nullable=True),
                      Column('egg_name', String(), nullable=True),
                      PrimaryKeyConstraint('id', name='reahl_schema_version_pkey')
                      )
        # self.schedule('indexes', op.create_index, 'reahl_schema_version_id_seq', 'reahl_schema_version', ['id'])


class ChangesToBeMySqlCompatible(Migration):
    def schedule_upgrades(self):
        self.orm_control.assert_dialect(self, 'postgresql')
        self.schedule('alter', op.alter_column, 'reahl_schema_version', 'egg_name',
                      existing_type=UnicodeText, type_=Unicode(80), existing_nullable=False)

