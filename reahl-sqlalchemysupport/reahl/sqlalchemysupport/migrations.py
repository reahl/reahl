# Copyright 2019 Reahl Software Services (Pty) Ltd. All rights reserved.
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

import logging

from alembic import op

from reahl.component.migration import Migration, MigrationUnit
from sqlalchemy import UnicodeText, Unicode, Column, Integer, String, PrimaryKeyConstraint
from sqlalchemy.engine import reflection
from reahl.component.context import ExecutionContext


class SafelyRenameKey(MigrationUnit):
    def __init__(self, migration, create_key_op):
        super().__init__(migration)
        self.drop_broke = False
        self.create_key_op = create_key_op

    def call(self, to_call, args, kwargs):
        if self.drop_broke and to_call is self.create_key_op:
            pass #TODO: are the current specs for the constraint the same as the new one ?
        else:
            if self.exists_constraint_named(args[0], args[1]):
                super().call(to_call, args, kwargs)
            else:
                if to_call is op.drop_constraint:
                    self.drop_broke = True
                else:
                    raise

    def exists_constraint_named(self, contraint_name, table_name):
        context = ExecutionContext.get_context()
        orm_control = context.system_control.orm_control
        import pdb;pdb.set_trace()
        with orm_control.managed_transaction() as transaction:
            inspector = reflection.inspection.Inspector.from_engine(transaction)
            table_foreign_keys = inspector.get_foregin_keys(table_name)
            return contraint_name in table_foreign_keys


class SafelyRenameForeignKey(SafelyRenameKey):
    def __init__(self, migration):
        super().__init__(migration, op.create_foreign_key)


class SafelyRenamePrimaryKey(SafelyRenameKey):
    def __init__(self, migration):
        super().__init__(migration, op.create_primary_key)


# class SafelyIgnore(MigrationUnit):
#     def __init__(self, migration):
#         super().__init__(migration)
#
#     def call(self, to_call, args, kwargs):
#         try:
#             super().call(to_call, args, kwargs)
#         except:
#             logging.getLogger(__name__).info(' ignoring change: %s(%s, %s)' % (to_call.__name__, args, kwargs))


class GenesisMigration(Migration):
    version = '2.0'

    def schedule_upgrades(self):
        self.schedule('alter', op.create_table, 'reahl_schema_version',
                      Column('id', Integer(), nullable=False),
                      Column('version', String(length=50), nullable=True),
                      Column('egg_name', String(), nullable=True),
                      PrimaryKeyConstraint('id', name='reahl_schema_version_pkey')
                      )
        # self.schedule('indexes', op.create_index, 'reahl_schema_version_id_seq', 'reahl_schema_version', ['id'])


class ChangesToBeMySqlCompatible(Migration):
    version = '4.0.0a1'

    def schedule_upgrades(self):
        self.schedule('alter', op.alter_column, 'reahl_schema_version', 'egg_name',
                      existing_type=UnicodeText, type_=Unicode(80), existing_nullable=False)

