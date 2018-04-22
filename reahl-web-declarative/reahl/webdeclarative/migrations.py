# Copyright 2014-2018 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from sqlalchemy import Column, String, UnicodeText
from alembic import op

from reahl.sqlalchemysupport.elixirmigration import MigrateElixirToDeclarative
from reahl.sqlalchemysupport import fk_name, ix_name

from reahl.component.migration import Migration
from reahl.component.context import ExecutionContext


class RenameRegionToUi(Migration):
    version = '2.1'
    @classmethod
    def is_applicable(cls, current_schema_version, new_version):
        if super(cls, cls).is_applicable(current_schema_version, new_version):
            # reahl-declarative is new, and replaces reahl-elixir-impl. Therefore it thinks it is migrating from version 0 always.
            # We need to manually check that it's not coming from reahl-web-elixirimpl 2.0 or 2.1 instead.
            orm_control = ExecutionContext.get_context().system_control.orm_control

            class FakeElixirEgg(object):
                name = 'reahl-web-declarative'
            previous_elixir_version = orm_control.schema_version_for(FakeElixirEgg(), default='0.0')

            return previous_elixir_version != '0.0' and super(cls, cls).is_applicable(current_schema_version, previous_elixir_version)
        else:
            return False

    def schedule_upgrades(self):
        self.schedule('alter', op.alter_column, 'sessiondata', 'region_name', new_column_name='ui_name')


class ElixirToDeclarativeWebDeclarativeChanges(MigrateElixirToDeclarative):
    def schedule_upgrades(self):
        super(ElixirToDeclarativeWebDeclarativeChanges, self).schedule_upgrades()
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
        self.schedule('cleanup', orm_control.initialise_schema_version_for, egg_name='reahl-web-declarative', egg_version=self.version)
        self.schedule('cleanup', orm_control.remove_schema_version_for, egg_name='reahl-web-elixirimpl')


class MergeWebUserSessionToUserSession(Migration):
    version = '3.1'
    def schedule_upgrades(self):
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
    version = '3.1'
    def schedule_upgrades(self):
        self.schedule('alter', op.add_column, 'persistedfile', Column('mime_type', UnicodeText, nullable=False))
        self.schedule('data', op.execute, 'update persistedfile set mime_type=content_type')
        self.schedule('cleanup', op.drop_column, 'persistedfile', 'content_type')


class AllowNullUserInputValue(Migration):
    version = '4.0.0a1'
    def schedule_upgrades(self):
        self.schedule('alter', op.alter_column, 'userinput', 'value', existing_nullable=False, nullable=True)


