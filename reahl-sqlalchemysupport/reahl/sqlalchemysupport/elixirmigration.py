from __future__ import print_function, unicode_literals, absolute_import, division
# Copyright 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from alembic import op

from reahl.component.migration import Migration
from reahl.sqlalchemysupport import fk_name, pk_name, ix_name


class MigrateElixirToDeclarative(Migration):
    version = '3.0'

    def schedule_upgrades(self):
        self.rename_primary_key_constraints()
        self.rename_foreign_keys_constraints()
        self.change_inheriting_table_ids()
        self.change_session_scoped_classes()

    def rename_primary_key_constraints(self):
        pass
        
    def rename_foreign_keys_constraints(self):
        pass
        
    def change_inheriting_table_ids(self):
        pass
        
    def change_session_scoped_classes(self):
        pass

    def rename_pk_column(self, table_name, old_name, new_name, primary_key_columns):
        self.rename_pk(table_name, primary_key_columns)
        self.schedule('alter', op.alter_column, table_name, old_name, new_column_name=new_name)

    def rename_pk(self, table_name, primary_key_columns, old_table_name=None):
        # The names of primary key constraints change according to naming convention 
        #  (some non-standard ones are dealt with individually)
        old_table_name = old_table_name or table_name
        self.schedule('drop_pk', op.drop_constraint, '%s_pkey' % old_table_name, old_table_name)
        self.schedule('create_pk', op.create_primary_key, 'pk_%s' % table_name, table_name, primary_key_columns)

    def change_session_scoped(self, table_name):
        # Rename of session_id relationship on @session_scoped things 
        old_name = 'session_id'
        new_name = 'user_session_id'
        self.schedule('drop_fk', op.drop_constraint, '%s_%s_fk' % (table_name, old_name), table_name)
        self.schedule('alter', op.alter_column, table_name, old_name, new_column_name=new_name)
        self.schedule('create_fk', op.create_foreign_key, fk_name(table_name, new_name, 'usersession'), table_name, 
                      'usersession', [new_name], ['id'], ondelete='CASCADE')
        self.schedule('drop_pk', op.drop_index, ix_name(table_name, old_name))
        self.schedule('indexes', op.create_index, ix_name(table_name, new_name), table_name, [new_name])

    def change_inheriting_table(self, table_name, old_id_column_name, inherited_table_name):
        # Tables of classes that inherit from another had xxx_id to refer to parent, instead of just id
        # Constraints were based on this (primary and foreign)
        self.schedule('drop_fk', op.drop_constraint, '%s_%s_fkey' % (table_name, old_id_column_name), table_name)
        self.rename_pk_column(table_name, old_id_column_name, 'id', ['id'])
        self.schedule('create_fk', op.create_foreign_key, fk_name(table_name, 'id', inherited_table_name), table_name, 
                      inherited_table_name, ['id'], ['id'], ondelete='CASCADE')

    def recreate_foreign_key_constraint(self, old_fk_name, table_name, column_name, other_table_name, other_column_name, **create_kwargs):
        # The names of foreign key constraints change according to naming convention 
        self.schedule('drop_fk', op.drop_constraint, '%s_fk' % old_fk_name, table_name)
        self.schedule('create_fk', op.create_foreign_key, fk_name(table_name, column_name, other_table_name), table_name, 
                       other_table_name, [column_name], [other_column_name], **create_kwargs)


class ElixirToDeclarativeSqlAlchemySupportChanges(MigrateElixirToDeclarative):
    def rename_primary_key_constraints(self):
        self.rename_pk('reahl_schema_version', ['id'])
