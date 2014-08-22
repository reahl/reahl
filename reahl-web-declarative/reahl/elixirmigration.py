

from __future__ import unicode_literals
from __future__ import print_function

import logging

from sqlalchemy import Column, String, Integer
from alembic import op

from reahl.component.migration import Migration
from reahl.component.context import ExecutionContext


def fk_name(table_name, column_name, other_table_name):
    return 'fk_%s_%s_%s' % (table_name, column_name, other_table_name)

def pk_name(table_name):
    return 'pk_%s' % table_name

def ix_name(table_name, column_name):
    return 'ix_%s_%s' % (table_name, column_name)


class ElixirToDeclarativeChanges(Migration):
    version = '3.0'

    def upgrade(self):
        self.rename_primary_key_constraints()
        self.rename_foreign_keys_constraints()

        self.change_inheriting_table_ids()
        self.change_session_scoped('accountmanagementinterface')

        self.change_new_password_request()
        self.change_task()
        self.rename_link_table()
        self.move_party_systemaccount_relationship()

        self.replace_elixir()

    def rename_pk_column(self, table_name, old_name, new_name, primary_key_columns):
        self.rename_pk(table_name, primary_key_columns)
        self.schedule('alter', op.alter_column, table_name, old_name, new_column_name=new_name)

    def rename_pk(self, table_name, primary_key_columns, old_table_name=None):
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

    def rename_link_table(self):
        old_table_name = 'requirement_deferred_actions__deferredaction_requirements'
        new_table_name = 'deferredaction_requirement'

        # Rename table itself
        self.schedule('alter', op.rename_table, old_table_name, new_table_name)

        # Rename of foreign key names
        for old_name, other_table_name in [
                ('deferredaction_requirements_fk', 'deferredaction'),
                ('requirement_deferred_actions_fk', 'requirement') ]:
            column_name = '%s_id' % other_table_name
            new_name = fk_name(new_table_name, column_name, other_table_name)
            self.schedule('drop_fk', op.drop_constraint, old_name, old_table_name)
            self.schedule('create_fk', op.create_foreign_key, new_name, new_table_name, other_table_name, [column_name], ['id'])

        # Primary keys are renamed according to new naming convention - in this case the table too
        self.rename_pk(new_table_name, ['deferredaction_id', 'requirement_id'], old_table_name=old_table_name)

    def change_inheriting_table_ids(self):
        for table_name, old_id_column_name, inheriting_table_name in [
                              ('webusersession', 'usersession_id', 'usersession'),
                              ('persistedexception', 'sessiondata_id', 'sessiondata'),
                              ('persistedfile', 'sessiondata_id', 'sessiondata'),
                              ('userinput', 'sessiondata_id', 'sessiondata'),
                              ('emailandpasswordsystemaccount', 'systemaccount_id', 'systemaccount'),
                              ('verifyemailrequest', 'verificationrequest_requirement_id', 'verificationrequest'),
                              ('verificationrequest', 'requirement_id', 'requirement'),
                              ('activateaccount', 'deferredaction_id', 'deferredaction'),
                              ('changeaccountemail', 'deferredaction_id', 'deferredaction')
                            ]:
            self.change_inheriting_table(table_name, old_id_column_name, inheriting_table_name)

    def change_new_password_request(self):
        # NewPasswordRequest inherits, but also has a composite primary key, so it cannot be delt with like
        #  other inheriting tables
        table_name = 'newpasswordrequest'
        self.schedule('drop_fk', op.drop_constraint, 'newpasswordrequest_verificationrequest_requirement_id_fkey', table_name)
        self.rename_pk_column(table_name, 'verificationrequest_requirement_id', 'id', ['id', 'system_account_id'])
        self.schedule('create_fk', op.create_foreign_key, fk_name(table_name, 'id', 'verificationrequest'), table_name, 
                      'verificationrequest', ['id'], ['id'], ondelete='CASCADE')
        # NewPasswordRequest relationship to system_account
        self.schedule('drop_fk', op.drop_constraint, 'newpasswordrequest_system_account_id_fk', table_name)
        self.schedule('create_fk', op.create_foreign_key, fk_name(table_name, 'system_account_id', 'systemaccount'), table_name, 
                      'systemaccount', ['system_account_id'], ['id'], deferrable=True, initially='DEFERRED')

    def rename_primary_key_constraints(self):
        # The names of primary key constraints change according to naming convention 
        #  (some non-standard ones are dealt with individually)
        for table_name in [
                  'accountmanagementinterface',
                  'deferredaction',
                  'party',
                  'queue',
                  'reahl_schema_version',
                  'requirement',
                  'sessiondata',
                  'systemaccount',
                  'task',
                  'usersession']:
            self.rename_pk(table_name, ['id'])

    def change_task(self):
        # Task in elixir did not generate a row_type for use as discriminator
        self.schedule('alter', op.add_column, 'task', Column('row_type', String(40)))

        # Task in elixir's queue_id was NULLABLE, but should not be (Tasks HAVE to be in a Queue now)
        self.schedule('alter', op.alter_column, 'task', 'queue_id', nullable=True)

        # Rename of relationship foreign key Task.reserved_by_id -> reserved_by_party_id
        old_name = 'reserved_by_id'
        new_name = 'reserved_by_party_id'
        self.schedule('drop_fk', op.drop_constraint, '%s_%s_fk' % ('task', old_name), 'task')
        self.schedule('alter', op.alter_column, 'task', old_name, new_column_name=new_name)
        self.schedule('create_fk', op.create_foreign_key, fk_name('task', new_name, 'party'), 'task', 'party', [new_name], ['id'])

        self.schedule('drop_pk', op.drop_index, ix_name('task', 'reserved_by_id'))
        self.schedule('indexes', op.create_index, ix_name('task','reserved_by_party_id'), 'task', ['reserved_by_party_id'])

    def rename_foreign_keys_constraints(self):
        # The names of foreign key constraints change according to naming convention 
        for old_fk_name, table_name, column_name, other_table_name, other_column_name, create_kwargs in [
                ('usersession_account_id', 'usersession', 'account_id', 'systemaccount', 'id', 
                  {}),
                ('sessiondata_web_session_id', 'sessiondata', 'web_session_id', 'webusersession', 'id', 
                  {'ondelete':'CASCADE'}),
                ('activateaccount_system_account_id', 'activateaccount', 'system_account_id', 'systemaccount', 'id', 
                  {'deferrable':True, 'initially':'DEFERRED'}),
                ('changeaccountemail_system_account_id', 'changeaccountemail', 'system_account_id', 'systemaccount', 'id', 
                  {'deferrable':True, 'initially':'DEFERRED'}),
                ('task_queue_id', 'task', 'queue_id', 'queue', 'id', 
                  {})
                ]:
                self.schedule('drop_fk', op.drop_constraint, '%s_fk' % old_fk_name, table_name)
                self.schedule('create_fk', op.create_foreign_key, fk_name(table_name, column_name, other_table_name), table_name, 
                              other_table_name, [column_name], [other_column_name], **create_kwargs)

    def move_party_systemaccount_relationship(self):
        # A SystemAccount now points to its 'owner' (a Party) instead of Party which previously pointed to a SystemAccount
        # TODO?:Assert no rows for : select count(*) from party group by system_account_party_id having count(*) > 1;
        self.schedule('drop_fk', op.drop_constraint, 'party_system_account_id_fk', 'party')
        self.schedule('alter', op.add_column, 'systemaccount', Column('owner_party_id', Integer))
        migrate_data = 'UPDATE systemaccount SET owner_party_id = PARTY.id FROM PARTY WHERE PARTY.system_account_id = systemaccount.id'
        self.schedule('data', op.execute, migrate_data)
        self.schedule('cleanup', op.drop_column, 'party', 'system_account_id')
        self.schedule('create_fk', op.create_foreign_key, fk_name('systemaccount', 'owner_party_id', 'party'), 
                      'systemaccount', 'party', ['owner_party_id'], ['id'])
        self.schedule('drop_pk', op.drop_index, ix_name('party','system_account_id'))

    def replace_elixir(self):
        # reahl-declarative is new, and replaces reahl-elixir-impl
        orm_control = ExecutionContext.get_context().system_control.orm_control
        self.schedule('cleanup', orm_control.initialise_schema_version_for, egg_name='reahl-web-declarative', egg_version=self.version)
        self.schedule('cleanup', orm_control.remove_schema_version_for, egg_name='reahl-web-elixirimpl')
