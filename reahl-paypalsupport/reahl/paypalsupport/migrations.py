# Copyright 2013-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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




from sqlalchemy import Column, String, Unicode, UnicodeText, Integer,  PrimaryKeyConstraint, UniqueConstraint
from alembic import op

from reahl.component.migration import Migration


class AdjustJsonForMySqlCompatibility(Migration):
    def schedule_upgrades(self):
        self.orm_control.assert_dialect(self, 'postgresql', 'mysql')
        self.schedule('alter', op.alter_column, 'payment_paypal_order', 
                      'json_string', type_=UnicodeText(), existing_type=Unicode()
                      )

        
class CreatePaypal(Migration):
    def schedule_upgrades(self):
        self.orm_control.assert_dialect(self, 'postgresql', 'mysql')
        self.schedule('alter', op.create_table, 'payment_paypal_order',
                      Column('id', Integer(), nullable=False),
                      Column('paypal_id', String(length=20)),
                      Column('status', String(length=10)),
                      Column('json_string', Unicode()),
                      PrimaryKeyConstraint('id', name='pk_payment_paypal_order'),
                      UniqueConstraint('paypal_id', name='uq_payment_paypal_order_paypal_id')
                      )
