# Copyright 2014, 2018 Reahl Software Services (Pty) Ltd. All rights reserved.
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
from sqlalchemy import Column, String, Integer, ForeignKey, UnicodeText, Unicode

from reahl.component.migration import Migration
from reahl.sqlalchemysupport.elixirmigration import MigrateElixirToDeclarative
from reahl.sqlalchemysupport import fk_name, ix_name


class ElixirToDeclarativeDomainChanges(MigrateElixirToDeclarative):
    def schedule_upgrades(self):
        super(ElixirToDeclarativeDomainChanges, self).schedule_upgrades()

        self.change_task()
        self.rename_link_table()
        self.move_party_systemaccount_relationship()

    def change_session_scoped_classes(self):
        self.change_session_scoped('accountmanagementinterface')

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
                              ('emailandpasswordsystemaccount', 'systemaccount_id', 'systemaccount'),
                              ('verifyemailrequest', 'verificationrequest_requirement_id', 'verificationrequest'),
                              ('verificationrequest', 'requirement_id', 'requirement'),
                              ('activateaccount', 'deferredaction_id', 'deferredaction'),
                              ('changeaccountemail', 'deferredaction_id', 'deferredaction')
                            ]:
            self.change_inheriting_table(table_name, old_id_column_name, inheriting_table_name)
        self.change_new_password_request()

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
                  'requirement',
                  'systemaccount',
                  'usersession',
                  'task']:
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
        for old_fk_name, table_name, column_name, other_table_name, other_column_name, create_kwargs in [
                ('usersession_account_id', 'usersession', 'account_id', 'systemaccount', 'id', 
                  {}),
                ('activateaccount_system_account_id', 'activateaccount', 'system_account_id', 'systemaccount', 'id', 
                  {'deferrable':True, 'initially':'DEFERRED'}),
                ('changeaccountemail_system_account_id', 'changeaccountemail', 'system_account_id', 'systemaccount', 'id', 
                  {'deferrable':True, 'initially':'DEFERRED'}),
                ('task_queue_id', 'task', 'queue_id', 'queue', 'id', 
                  {})
                ]:
            self.recreate_foreign_key_constraint(old_fk_name, table_name, column_name, other_table_name, other_column_name, **create_kwargs)
            
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


class AddLoginSession(Migration):
    version='3.1'    
    def schedule_upgrades(self):
        self.schedule('alter', op.create_table, 'loginsession', 
                      Column('id', Integer(), primary_key=True, nullable=False),
                      Column('row_type', String(length=40)),
                      Column('account_id', Integer(), ForeignKey('systemaccount.id')), 
                      Column('user_session_id', Integer(), ForeignKey('usersession.id')))
        self.schedule('indexes', op.create_index, ix_name('loginsession', 'account_id'), 'loginsession', ['account_id'])
        self.schedule('indexes', op.create_index, ix_name('loginsession', 'user_session_id'), 'loginsession', ['user_session_id'])


class ChangeSchemaToBeMySqlCompatible(Migration):
    version = '4.0.0a1'
    def schedule_upgrades(self):
        #the fk's were defined as DEFERRABLE INITIALLY deferred. Since MySQL does not cater for it, we need to remove it.
        other_table_name = 'systemaccount'
        for table_name in ['newpasswordrequest', 'changeaccountemail', 'activateaccount']:
            self.schedule('drop_fk', op.drop_constraint, fk_name(table_name, 'system_account_id', other_table_name), table_name)
            self.schedule('create_fk', op.create_foreign_key, fk_name(table_name, 'system_account_id', other_table_name), table_name,
                          other_table_name , ['system_account_id'], ['id'])

        # MySql does not allow unbounded Unicode/UnicodeText to be indexed etc
        for table_name in ['emailandpasswordsystemaccount', 'accountmanagementinterface', 'verifyemailrequest']:
            self.schedule('alter', op.alter_column, table_name, 'email', existing_type=UnicodeText, type_=Unicode(254),
                          existing_nullable=False)
        self.schedule('alter', op.alter_column, 'queue', 'name', existing_type=UnicodeText, type_=Unicode(120),
                      existing_nullable=False)


class ChangePasswordHash(Migration):
    version = '4.0.0a1'

    def schedule_upgrades(self):
        self.schedule('alter', op.alter_column, 'emailandpasswordsystemaccount',
                                                'password_md5', new_column_name='password_hash',
                                                existing_type=String(32), type_=Unicode(1024),
                                                existing_nullable=False, nullable=False)


class RemoveDeadApacheDigestColumn(Migration):
    version = '4.0.0a1'

    def schedule_upgrades(self):
        self.schedule('cleanup', op.drop_column, 'emailandpasswordsystemaccount', 'apache_digest')
