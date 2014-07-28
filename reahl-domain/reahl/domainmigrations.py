

from __future__ import unicode_literals
from __future__ import print_function

from sqlalchemy import Column, String
from alembic import op

from reahl.component.migration import Migration

class ElixirToDeclarativeChanges(Migration):
    version = '3.0'
    def upgrade(self):
        for table_name, inheriting_table_name in [('webusersession', 'usersession'),
                                                  ('userinput', 'sessiondata'),
                                                  ('persistedexception', 'sessiondata'),
                                                  ('persistedfile', 'sessiondata'),
                                                  ('emailandpasswordsystemaccount', 'systemaccount'),
                                                  ('verificationrequest', 'request'),
                                                  ('verifyemailrequest', 'verificationrequest'),
                                                  ('newpasswordrequest', 'verificationrequest'),
                                                  ('activateaccount', 'deferredaction'),
                                                  ('changeaccountemail', 'deferredaction')
                                                  ]:
            self.change_inheriting_table(table_name, inheriting_table_name)

        # Task in elixir did not generate a row_type for use as discriminator
        op.add_column('task', 'row_type', Column('row_type', String(40)))


        # Rename of relationship on EmailAndPasswordSystemAccount
        op.drop_constraint('accountmanagementinterface_session_id_fk', accountmanagementinterface)
        op.alter_column('accountmanagementinterface', 'session_id', new_column_name='user_session_id')
        op.create_foreign_key(accountmanagementinterface_user_session_id_fkey, 'accountmanagementinterface', 
                              'usersession', ['user_session_id'], ['id'], ondelete='CASCADE')

        

    def change_inheriting_table(self, table_name, inherited_table_name):
        # Tables of classes that inherit from another had xxx_id to refer to parent, instead of just id
        # Constraints were based on this (primary and foreign)
        op.drop_constraint('%s_%s_id_fkey' % (table_name, inherited_table_name), table_name)
        op.drop_constraint('%s_pk' % table_name, table_name)
        op.alter_column(table_name, '%s_id' % inheriting_table_name, new_column_name='id')
        op.create_primary_key('%s_pk' % table_name, table_name, ['id'])
        op.create_foreign_key('%s_id_fkey' % table_name, table_name, inheriting_table_name, ['id'], ['id'], ondelete='CASCADE')

            
    def upgrade_cleanup(self):
        print('executing AddDate (upgrade_cleanup)')
