

from __future__ import unicode_literals
from __future__ import print_function

import logging

from sqlalchemy import Column, String, Integer
from alembic import op

from reahl.component.migration import Migration


class ElixirToDeclarativeChanges(Migration):
    version = '3.0'

    def upgrade(self):
        inheriting_tables = [
                              ('webusersession', 'usersession_id', 'usersession'),
                              ('persistedexception', 'sessiondata_id', 'sessiondata'),
                              ('persistedfile', 'sessiondata_id', 'sessiondata'),
                              ('userinput', 'sessiondata_id', 'sessiondata'),
                              ('emailandpasswordsystemaccount', 'systemaccount_id', 'systemaccount'),
                              ('verifyemailrequest', 'verificationrequest_requirement_id', 'verificationrequest'),
                              ('verificationrequest', 'requirement_id', 'requirement'),
                              ('activateaccount', 'deferredaction_id', 'deferredaction'),
                              ('changeaccountemail', 'deferredaction_id', 'deferredaction')
                            ]
        for table_name, old_id_column_name, inheriting_table_name in inheriting_tables:
            self.change_inheriting_table(table_name, old_id_column_name, inheriting_table_name)

        # NewPasswordRequest inherits, but also has a composite primary key
        self.schedule('drop_fk', op.drop_constraint, 'newpasswordrequest_verificationrequest_requirement_id_fkey', 'newpasswordrequest')
        self.rename_pk_column('newpasswordrequest', 'verificationrequest_requirement_id', 'id', ['id', 'system_account_id'])
        self.schedule('create_fk', op.create_foreign_key, 'newpasswordrequest_id_fkey', 'newpasswordrequest', 'verificationrequest', ['id'], ['id'], ondelete='CASCADE')
        # NewPasswordRequest relationship to system_account
        self.schedule('drop_fk', op.drop_constraint, 'newpasswordrequest_system_account_id_fk', 'newpasswordrequest')
        self.schedule('create_fk', op.create_foreign_key, 'newpasswordrequest_system_account_id_fkey', 'newpasswordrequest', 'systemaccount', 
                              ['system_account_id'], ['id'], deferrable=True, initially='DEFERRED')
       
        # Task in elixir did not generate a row_type for use as discriminator
        self.schedule('alter', op.add_column, 'task', Column('row_type', String(40)))
        # Task in elixir's queue_id was NULLABLE, but should not be (Tasks HAVE to be in a Queue now)
        self.schedule('alter', op.alter_column, 'task', 'queue_id', nullable=True)

        # Rename of relationship on @session_scoped things
        self.change_web_session_for_session_scoped('accountmanagementinterface')

        # Rename of relationship foreign key Task.reserved_by_id -> reserved_by_party_id
        self.schedule('drop_fk', op.drop_constraint, 'task_reserved_by_id_fk', 'task')
        self.schedule('alter', op.alter_column, 'task', 'reserved_by_id', new_column_name='reserved_by_party_id')
        self.schedule('create_fk', op.create_foreign_key, 'task_reserved_by_party_id_fkey', 'task', 'party', ['reserved_by_party_id'], ['id'])
        
        # Rename of foreign key names for relationships
        for name_base, table_name, column_name, other_table_name, other_column_name, create_kwargs in [
                ('usersession_account_id', 'usersession', 'account_id', 'systemaccount', 'id', {}),
                ('sessiondata_web_session_id', 'sessiondata', 'web_session_id', 'webusersession', 'id', {'ondelete':'CASCADE'}),
                ('activateaccount_system_account_id', 'activateaccount', 'system_account_id', 'systemaccount', 'id', {'deferrable':True, 'initially':'DEFERRED'}),
                ('changeaccountemail_system_account_id', 'changeaccountemail', 'system_account_id', 'systemaccount', 'id', {'deferrable':True, 'initially':'DEFERRED'}),
                ('task_queue_id', 'task', 'queue_id', 'queue', 'id', {})
                ]:
                self.schedule('drop_fk', op.drop_constraint, '%s_fk' % name_base, table_name)
                self.schedule('create_fk', op.create_foreign_key, '%s_fkey' % name_base, table_name, other_table_name, [column_name], [other_column_name], **create_kwargs)

        # Rename of foreign key names for many-to-many relationship link table 
        for old_name, new_name, table_name, column_name, other_table_name, other_column_name in [
                ('deferredaction_requirements_fk', 'requirement_deferred_actions__deferredac_deferredaction_id_fkey', 
                 'requirement_deferred_actions__deferredaction_requirements', 'deferredaction_id', 'deferredaction', 'id'),
                ('requirement_deferred_actions_fk', 'requirement_deferred_actions__deferredactio_requirement_id_fkey', 
                 'requirement_deferred_actions__deferredaction_requirements', 'requirement_id', 'requirement', 'id')
                   ]:
                self.schedule('drop_fk', op.drop_constraint, old_name, table_name)
                self.schedule('create_fk', op.create_foreign_key, new_name, table_name, other_table_name, [column_name], [other_column_name])

        # Move of relationship between Party and SystemAccount
        # TODO:Assert no rows for : select count(*) from party group by system_account_party_id having count(*) > 1;
        self.schedule('drop_fk', op.drop_constraint, 'party_system_account_id_fk', 'party')
        self.schedule('alter', op.add_column, 'systemaccount', Column('owner_party_id', Integer))
        self.schedule('data', op.execute, 'UPDATE systemaccount SET owner_party_id = PARTY.id FROM PARTY WHERE PARTY.system_account_id = systemaccount.id')
        self.schedule('cleanup', op.drop_column, 'party', 'system_account_id')
        self.schedule('create_fk', op.create_foreign_key, 'systemaccount_owner_party_id_fkey', 'systemaccount', 'party', ['owner_party_id'], ['id'])
        self.schedule('drop_pk', op.drop_index, 'ix_party_system_account_id')
        self.schedule('drop_pk', op.drop_index, 'ix_task_reserved_by_id')
        self.schedule('indexes', op.create_index, 'ix_task_reserved_by_party_id', 'task', ['reserved_by_party_id'])

        # reahl-declarative is new, and replaces reahl-elixir-impl
        orm_control = ExecutionContext.get_context().system_control.orm_control
        self.schedule('cleanup', orm_control.initialise_schema_version_for(egg_name='reahl-declarative', egg_version=self.version))
        self.schedule('cleanup', orm_control.remove_schema_version_for(egg_name='reahl-elixir-impl'))


    def rename_pk_column(self, table_name, old_name, new_name, primary_key_columns):
        self.schedule('drop_pk', op.drop_constraint, '%s_pkey' % table_name, table_name)
        self.schedule('alter', op.alter_column, table_name, old_name, new_column_name=new_name)
        self.schedule('create_pk', op.create_primary_key, '%s_pkey' % table_name, table_name, primary_key_columns)

    def create_index(self, table_name, index_name, primary_key_columns):
        self.schedule('indexes', op.create_index, index_name, table_name, primary_key_columns)

    def change_web_session_for_session_scoped(self, table_name):
        self.schedule('drop_fk', op.drop_constraint, '%s_session_id_fk' % table_name, table_name)
        self.schedule('alter', op.alter_column, table_name, 'session_id', new_column_name='user_session_id')
        self.schedule('create_fk', op.create_foreign_key, '%s_user_session_id_fkey' % table_name, table_name, 
                                'usersession', ['user_session_id'], ['id'], ondelete='CASCADE')
        self.schedule('drop_pk', op.drop_index, 'ix_%s_session_id' % table_name)
        self.schedule('indexes', op.create_index, 'ix_%s_user_session_id' % table_name, table_name, ['user_session_id'])

    def change_inheriting_table(self, table_name, old_id_column_name, inherited_table_name):
        # Tables of classes that inherit from another had xxx_id to refer to parent, instead of just id
        # Constraints were based on this (primary and foreign)
        self.schedule('drop_fk', op.drop_constraint, '%s_%s_fkey' % (table_name, old_id_column_name), table_name)
        self.rename_pk_column(table_name, old_id_column_name, 'id', ['id'])
        self.schedule('create_fk', op.create_foreign_key, '%s_id_fkey' % table_name, table_name, inherited_table_name, ['id'], ['id'], ondelete='CASCADE')

            
