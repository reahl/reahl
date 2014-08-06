

from __future__ import unicode_literals
from __future__ import print_function

from sqlalchemy import Column, String
from alembic import op

from reahl.component.migration import Migration

class ElixirToDeclarativeChanges(Migration):
    version = '3.0'
    def upgrade(self):
        for table_name, inheriting_table_name in [('webusersession', 'usersession_id', 'usersession'),
                                                  ('userinput', 'sessiondata_id', 'sessiondata'),
                                                  ('persistedexception', 'sessiondata_id', 'sessiondata'),
                                                  ('persistedfile', 'sessiondata_id', 'sessiondata'),
                                                  ('emailandpasswordsystemaccount', 'systemaccount_id', 'systemaccount'),
                                                  ('verificationrequest', 'requirement_id', 'request'),
                                                  ('verifyemailrequest', 'verificationrequest_requirement_id', 'verificationrequest'),
#!!!                                                  ('newpasswordrequest', 'verificationrequest_requirement_id', 'verificationrequest'),
                                                  ('activateaccount', 'deferredaction_id', 'deferredaction'),
                                                  ('changeaccountemail', 'deferredaction_id', 'deferredaction')
                                                  ]:
            self.change_inheriting_table(table_name, inheriting_table_name)

        # Task in elixir did not generate a row_type for use as discriminator
        op.add_column('task', 'row_type', Column('row_type', String(40)))
        # Task in elixir's queue_id was NULLABLE, but should not be (Tasks HAVE to be in a Queue now)
        op.alter_column('task', 'queue_id', nullable=False)

        # Rename of relationship on @session_scoped things
        self.change_web_session_for_session_scoped('accountmanagementinterface')

        # Rename of relationship foreign key Task.reserved_by_id -> reserved_by_party_id
        op.drop_constraint('task_reserved_by_id_fk', 'task')
        op.alter_column('task', 'reserved_by_id', new_column_name='reserved_by_party_id')
        op.create_foreign_key('task_reserved_by_party_id_fkey', 'task', 'party', ['reserved_by_party_id'], ['id'])
        
        # Rename of foreign key names for relationships
        for name_base, table_name, column_name, other_table_name, other_column_name 
            in [('usersession_account_id', 'usersession', 'account_id', 'systemaccount', 'id'),
                ('sessiondata_web_session_id', 'sessiondata', 'web_session_id', 'webusersession', 'id'),
                ('deferredaction_requirements', 'requirement_deferred_actions__deferredaction_requirements', 'deferredaction_id', 'deferredaction', 'id'),
                ('requirement_deferred_actions', 'requirement_deferred_actions__deferredaction_requirements', 'requirement_id', 'requirement', 'id'),
                ('activateaccount_system_account_id', 'activateaccount', 'system_account_id', 'systemaccount', 'id'),
                ('changeaccountemail_system_account_id', 'changeaccountemail', 'system_account_id', 'systemaccount', 'id'),
                ('task_queue_id', 'task', 'queue_id', 'queue', 'id')
                   ]:
                op.drop_constraint('%s_fk' % name_base, table_name)
                op.create_foreign_key('%s_fkey' % name_base, table_name, other_table_name, [column_name], [other_column_name])
        # Move of relationship between Party and SystemAccount
        # TODO:Assert no rows for : select count(*) from party group by system_account_party_id having count(*) > 1;
        op.drop_constraint('party_system_account_id_fk', 'party')
        op.execute('UPDATE systemaccount SET owner_party_id = PARTY.id FROM PARTY WHERE PARTY.system_account_id = systemaccount.id')
        op.create_foreign_key('systemaccount_party_id_fkey', 'systemaccount', 'party', ['party_id'], ['id'])
        

        
    def change_web_session_for_session_scoped(self, table_name):
        op.drop_constraint('%s_session_id_fk' % table_name, table_name)
        op.alter_column('accountmanagementinterface', 'session_id', new_column_name='user_session_id')
        op.create_foreign_key('%s_user_session_id_fkey' % table_name, table_name, 
                              'usersession', ['user_session_id'], ['id'], ondelete='CASCADE')


    def change_inheriting_table(self, table_name, old_id_column_name, inherited_table_name):
        # Tables of classes that inherit from another had xxx_id to refer to parent, instead of just id
        # Constraints were based on this (primary and foreign)
        op.drop_constraint('%s_%s_fkey' % (table_name, old_id_column_name), table_name)
        op.drop_constraint('%s_pkey' % table_name, table_name)
        op.alter_column(table_name, old_id_column_name, new_column_name='id')
        op.create_primary_key('%s_pkey' % table_name, table_name, ['id'])
        op.create_foreign_key('%s_id_fkey' % table_name, table_name, inherited_table_name, ['id'], ['id'], ondelete='CASCADE')

            
    def upgrade_cleanup(self):
        print('executing AddDate (upgrade_cleanup)')
