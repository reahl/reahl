# Copyright 2014-2020 Reahl Software Services (Pty) Ltd. All rights reserved.
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
from reahl.sqlalchemysupport import fk_name, ix_name


class MigrateElixirToDeclarative(Migration):
    """Inherit your own Migrations from this class in order to get access to a number of methods that 
       help with migrating common changes between Elixir and Declarative"""

    def schedule_upgrades(self):
        self.orm_control.assert_dialect(self, 'postgresql')
        self.rename_primary_key_constraints()
        self.rename_foreign_keys_constraints()
        self.change_inheriting_table_ids()
        self.change_session_scoped_classes()

    def rename_primary_key_constraints(self):
        """This method will be called to schedule changes to renamed primary keys. Override it if you have any in your component."""
        pass
        
    def rename_foreign_keys_constraints(self):
        """This method will be called to schedule changes to renamed foreign keys. Override it if you have any in your component."""
        pass
        
    def change_inheriting_table_ids(self):
        """This method will be called to schedule changes to the id columns of tables that inherit. Override it if you have any in your component."""
        pass
        
    def change_session_scoped_classes(self):
        """This method will be called to schedule changes to classes that are @session_scoped. Override it if you have any in your component."""
        pass

    def rename_pk_column(self, table_name, old_name, new_name, primary_key_columns):
        """Schedule changes necessary to rename a primary key column itself. It recreates the primary key,
           hence needs all info for doing so.

           :arg table_name: The name of the table to which the primary key belongs.
           :arg old_name: The old name of the primary key column.
           :arg new_name: The new name of the primary key column.
           :arg primary_key_columns: A list of strings (unicode in Py2, str in Py3) containing the names of the columns that should be included in the primary key.
        """
        self.rename_pk(table_name, primary_key_columns)
        self.schedule('alter', op.alter_column, table_name, old_name, new_column_name=new_name)

    def rename_pk(self, table_name, primary_key_columns, old_table_name=None):
        """Schedule changes necessary to rename a primary key (not the column) according to new naming conventions. It recreates the primary key,
           hence needs all info for doing so. 

           :arg table_name: The name of the table to which the primary key belongs.
           :arg primary_key_columns: A list of strings (unicode in Py2, str in Py3) containing the names of the columns that should be included in the primary key.
           :keyword old_table_name: Specify old_table_name if the table is also renamed during this migration (even if for other reasons).
        """
        old_table_name = old_table_name or table_name
        self.schedule('drop_pk', op.drop_constraint, '%s_pkey' % old_table_name, old_table_name)
        self.schedule('create_pk', op.create_primary_key, 'pk_%s' % table_name, table_name, primary_key_columns)

    def change_session_scoped(self, table_name):
        """Rename the old session_id relationship on @session_scoped things to user_session_id, and update
           the foreign keys and indexes accordingly.

           :arg table_name: The name of the table underlying the @session_scoped class.
        """
        old_name = 'session_id'
        new_name = 'user_session_id'
        self.schedule('drop_fk', op.drop_constraint, '%s_%s_fk' % (table_name, old_name), table_name)
        self.schedule('alter', op.alter_column, table_name, old_name, new_column_name=new_name)
        self.schedule('create_fk', op.create_foreign_key, fk_name(table_name, new_name, 'usersession'), table_name, 
                      'usersession', [new_name], ['id'], ondelete='CASCADE')
        self.schedule('drop_pk', op.drop_index, ix_name(table_name, old_name))
        self.schedule('indexes', op.create_index, ix_name(table_name, new_name), table_name, [new_name])

    def change_inheriting_table(self, table_name, old_id_column_name, parent_table_name):
        """Tables of classes that inherit from other classes (using joint table inheritance) named their
           primary key columns xxx_id (assuming the parent is called xxx here). These were also foreign
           keys to the primary key of the parent table. In our Declarative implementation we just always use
           the name `id` for a primary key regardless of the situation.

           This method renames such primary key columns, and deal with the knock-on effect of this change 
           to related primary and foreign key as well.

           :arg table_name: The name of the table underlying the child/inheriting class.
           :arg old_id_column_name: The old name of the primary key column of the child/inheriting class.
           :arg parent_table_name: The name of the table underlying the parent class.
        """
        self.schedule('drop_fk', op.drop_constraint, '%s_%s_fkey' % (table_name, old_id_column_name), table_name)
        self.rename_pk_column(table_name, old_id_column_name, 'id', ['id'])
        self.schedule('create_fk', op.create_foreign_key, fk_name(table_name, 'id', parent_table_name), table_name, 
                      parent_table_name, ['id'], ['id'], ondelete='CASCADE')

    def recreate_foreign_key_constraint(self, old_fk_name, table_name, column_name, other_table_name, other_column_name, **create_kwargs):
        """The names of foreign key constraints change according to naming convention. This method affects 
           such a name change, but in order to do it, it needs all details necessary to recreate the
           foreign key constraint.

           :arg old_fk_name: The previous name of the foreign key.
           :arg table_name: The name of the table from which the foreign key points.
           :arg column_name: The name of the column in which the foreign key pointer is stored.
           :arg other_table_name: The name of the table to which the foreign key points.
           :arg other_column_name: The name of the column to which the foreign key points.
           :kwarg create_kwargs: Additional keyword arguments to be passes to alembic's op.create_foreign_key
        """
        self.schedule('drop_fk', op.drop_constraint, '%s_fk' % old_fk_name, table_name)
        self.schedule('create_fk', op.create_foreign_key, fk_name(table_name, column_name, other_table_name), table_name, 
                       other_table_name, [column_name], [other_column_name], **create_kwargs)


class ElixirToDeclarativeSqlAlchemySupportChanges(MigrateElixirToDeclarative):
    def rename_primary_key_constraints(self):
        self.rename_pk('reahl_schema_version', ['id'])
