# Copyright 2014-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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




from sqlalchemy import Column, String, UnicodeText, Integer, Text, PrimaryKeyConstraint, LargeBinary, BigInteger
from alembic import op

from reahl.sqlalchemysupport.elixirmigration import MigrateElixirToDeclarative
from reahl.sqlalchemysupport import fk_name, ix_name

from reahl.component.migration import Migration
from reahl.component.context import ExecutionContext


class CreateDatabase(Migration):
    def schedule_upgrades(self):
        self.orm_control.assert_dialect(self, 'postgresql')
        self.schedule('alter', op.create_table, 'sessiondata',
                      Column('id', Integer(), nullable=False),
                      Column('web_session_id', Integer(), nullable=True),
                      Column('region_name', Text(), nullable=False),
                      Column('channel_name', Text(), nullable=False),
                      Column('row_type', String(length=40), nullable=True),
                      PrimaryKeyConstraint('id', name='sessiondata_pkey')
                      )
        self.schedule('create_fk', op.create_foreign_key, 'sessiondata_web_session_id_fk', 'sessiondata',
                      'usersession', ['web_session_id'], ['id'], ondelete='CASCADE')

        # self.schedule('indexes', op.create_index, 'sessiondata_id_seq', 'sessiondata', ['id'])
        self.schedule('indexes', op.create_index, 'ix_sessiondata_web_session_id', 'sessiondata', ['web_session_id'], unique=False)

        self.schedule('alter', op.create_table, 'webusersession',
                      Column('usersession_id', Integer(), nullable=False),
                      Column('salt', String(length=40), nullable=False),
                      Column('secure_salt', String(length=40), nullable=False),
                      PrimaryKeyConstraint('usersession_id', name='webusersession_pkey')
                      )
        self.schedule('create_fk', op.create_foreign_key, 'webusersession_usersession_id_fkey', 'webusersession',
                      'usersession', ['usersession_id'], ['id'], ondelete='CASCADE')

        self.schedule('alter', op.create_table, 'persistedexception',
                      Column('sessiondata_id', Integer(), nullable=False),
                      Column('exception', LargeBinary(), nullable=False),
                      Column('input_name', Text(), nullable=True),
                      PrimaryKeyConstraint('sessiondata_id', name='persistedexception_pkey')
                      )
        self.schedule('create_fk', op.create_foreign_key, 'persistedexception_sessiondata_id_fkey', 'persistedexception',
                      'sessiondata', ['sessiondata_id'], ['id'], ondelete='CASCADE')

        self.schedule('alter', op.create_table, 'persistedfile',
                      Column('sessiondata_id', Integer(), nullable=False),
                      Column('input_name', Text(), nullable=False),
                      Column('filename', Text(), nullable=False),
                      Column('file_data', LargeBinary(), nullable=False),
                      Column('content_type', Text(), nullable=False),
                      Column('size', BigInteger(), nullable=False),
                      PrimaryKeyConstraint('sessiondata_id', name='persistedfile_pkey')
                      )
        self.schedule('create_fk', op.create_foreign_key, 'persistedfile_sessiondata_id_fkey', 'persistedfile',
                      'sessiondata', ['sessiondata_id'], ['id'], ondelete='CASCADE')

        self.schedule('alter', op.create_table, 'userinput',
                      Column('sessiondata_id', Integer(), nullable=False),
                      Column('key', Text(), nullable=False),
                      Column('value', Text(), nullable=False),
                      PrimaryKeyConstraint('sessiondata_id', name='userinput_pkey')
                      )
        self.schedule('create_fk', op.create_foreign_key, 'userinput_sessiondata_id_fkey', 'userinput',
                      'sessiondata', ['sessiondata_id'], ['id'], ondelete='CASCADE')


class RenameRegionToUi(Migration):

    def schedule_upgrades(self):
        self.orm_control.assert_dialect(self, 'postgresql')
        self.schedule('alter', op.alter_column, 'sessiondata', 'region_name', new_column_name='ui_name')


class ElixirToDeclarativeWebDeclarativeChanges(MigrateElixirToDeclarative):
    def schedule_upgrades(self):
        super().schedule_upgrades()
        self.replace_elixir()

    def rename_primary_key_constraints(self):
        self.rename_pk('sessiondata', ['id'])

    def rename_foreign_keys_constraints(self):
        self.recreate_foreign_key_constraint('sessiondata_web_session_id', 'sessiondata', 'web_session_id', 'webusersession', 'id', ondelete='CASCADE')

    def change_inheriting_table_ids(self):
        for table_name, old_id_column_name, inheriting_table_name in [
                              ('webusersession', 'usersession_id', 'usersession'),
                              ('persistedexception', 'sessiondata_id', 'sessiondata'),
                              ('persistedfile', 'sessiondata_id', 'sessiondata'),
                              ('userinput', 'sessiondata_id', 'sessiondata')
                            ]:
            self.change_inheriting_table(table_name, old_id_column_name, inheriting_table_name)

    def replace_elixir(self):
        # reahl-declarative is new, and replaces reahl-elixir-impl
        orm_control = ExecutionContext.get_context().system_control.orm_control
        self.schedule('cleanup', orm_control.remove_schema_version_for, egg_name='reahl-web-elixirimpl', fail_if_not_found=False)


class MergeWebUserSessionToUserSession(Migration):
    def schedule_upgrades(self):
        self.orm_control.assert_dialect(self, 'postgresql')
        self.schedule('drop_pk', op.drop_index, ix_name('usersession', 'account_id'))
        self.schedule('alter', op.drop_column, 'usersession', 'account_id')
        self.schedule('alter', op.add_column, 'usersession', Column('salt', String(40), nullable=False))
        self.schedule('alter', op.add_column, 'usersession', Column('secure_salt', String(40), nullable=False))
        self.schedule('alter', op.drop_table, 'webusersession')
        self.schedule('data', op.execute, 'delete from usersession')

        self.schedule('drop_fk', op.drop_constraint, fk_name('sessiondata', 'web_session_id', 'webusersession'), 'sessiondata')
        self.schedule('create_fk', op.create_foreign_key, fk_name('sessiondata', 'web_session_id', 'usersession'), 'sessiondata',
                      'usersession', ['web_session_id'], ['id'], ondelete='CASCADE')


class RenameContentType(Migration):
    def schedule_upgrades(self):
        self.orm_control.assert_dialect(self, 'postgresql')
        self.schedule('alter', op.add_column, 'persistedfile', Column('mime_type', UnicodeText, nullable=False))
        self.schedule('data', op.execute, 'update persistedfile set mime_type=content_type')
        self.schedule('cleanup', op.drop_column, 'persistedfile', 'content_type')


class AllowNullUserInputValue(Migration):
    def schedule_upgrades(self):
        self.orm_control.assert_dialect(self, 'postgresql')
        self.schedule('alter', op.alter_column, 'userinput', 'value', existing_nullable=False, nullable=True)


class AddViewPathToSessionData(Migration):
    def schedule_upgrades(self):
        self.orm_control.assert_dialect(self, 'postgresql', 'mysql')
        self.schedule('alter', op.alter_column, 'sessiondata', 'channel_name', existing_nullable=False, nullable=True, existing_type=UnicodeText)
        self.schedule('alter', op.add_column, 'sessiondata', Column('view_path', UnicodeText, nullable=False))


class AddPolimorphicEntityName(Migration):
    def schedule_upgrades(self):
        self.orm_control.assert_dialect(self, 'postgresql', 'mysql')
        self.schedule('data', op.execute, 'update sessiondata set row_type=\'sessiondata\' where row_type is null')
        
