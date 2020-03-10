# Copyright 2018 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.component.modelinterface import exposed, Field, Event, Action, Choice, ChoiceField, IntegerField
from reahl.component.exceptions import DomainException
from reahl.web.fw import UserInterface
from reahl.web.ui import StaticColumn, DynamicColumn
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.ui import FieldSet, HTML5Page, Div, P
from reahl.web.bootstrap.grid import Container, ColumnLayout, ColumnOptions, ResponsiveSize
from reahl.web.bootstrap.forms import Form, FormLayout, TextInput, RadioButtonSelectInput, Button
from reahl.web.bootstrap.tables import Table

from sqlalchemy import Column, Integer, UnicodeText, ForeignKey
from sqlalchemy.orm import relationship
from reahl.sqlalchemysupport import Base, Session, session_scoped



class DynamicUI(UserInterface):
    def assemble(self):
        self.define_page(HTML5Page).use_layout(PageLayout(document_layout=Container(),
                                                          contents_layout=ColumnLayout(
                                                              ColumnOptions('main', size=ResponsiveSize(lg=6))).with_slots()))
        home = self.define_view('/', title='Dynamic content demo')
        home.set_slot('main', AllocationDetailForm.factory())


class AllocationDetailForm(Form):
    def __init__(self, view):
        super(AllocationDetailForm, self).__init__(view, css_id='investment_allocation_details')
        investment = Investment.for_current_session()
        self.enable_refresh(on_refresh=investment.events.allocation_changed)
        self.use_layout(FormLayout())

        allocation_controls = self.add_child(FieldSet(self.view, legend_text='Investment allocation'))
        allocation_controls.use_layout(FormLayout())

        allocation_controls.layout.add_input(TextInput(self, investment.fields.amount, refresh_widget=self))
        allocation_controls.layout.add_input(RadioButtonSelectInput(self, investment.fields.amount_or_percentage, refresh_widget=self))


        def make_amount_input(view, allocation):
            if isinstance(allocation, Allocation):
                div = Div(view).use_layout(FormLayout())
                div.layout.add_input(TextInput(self, allocation.fields.amount, name='amount.%s' % allocation.fund_code, refresh_widget=self), hide_label=True)
                return div
            else:
                return P(view, text=str(allocation.amount))
        def make_percentage_input(view, allocation):
            if isinstance(allocation, Allocation):
                div = Div(view).use_layout(FormLayout())
                div.layout.add_input(TextInput(self, allocation.fields.percentage, name='percentage.%s' % allocation.fund_code, refresh_widget=self), hide_label=True)
                return div
            else:
                return P(view, text=str(allocation.percentage))

        class TotalsRow(object):
            def __init__(self, investment):
                self.investment = investment
                self.fund = 'Totals'
                self.amount = sum([i.amount for i in investment.allocations])
                self.percentage = sum([i.percentage for i in investment.allocations])

        columns = [StaticColumn(Field(label='Fund'), 'fund')]
        columns.append(DynamicColumn('Percentage', make_percentage_input))
        columns.append(DynamicColumn('Amount', make_amount_input))
        table = Table(self.view).with_data(columns, investment.allocations+[TotalsRow(investment)])
        self.add_child(table)
        self.define_event_handler(investment.events.submit)
        self.add_child(Button(self, investment.events.submit))




@session_scoped
class Investment(Base):
    __tablename__ = 'dynamic_content_investment'

    id              = Column(Integer, primary_key=True)
    amount          = Column(Integer)
    amount_or_percentage = Column(UnicodeText)
    allocations     = relationship('Allocation', back_populates='investment', lazy='immediate')

    @exposed
    def fields(self, fields):
        fields.amount       = IntegerField(label='Total amount', required=True)
        fields.amount_or_percentage  = ChoiceField([Choice('amount', Field(label='Amount')),
                                                    Choice('percentage', Field(label='Percentage'))],
                                                   label='Allocate using', required=True)

    @exposed('submit')
    def events(self, events):
        events.submit = Event(label='Submit', action=Action(self.submit))
        events.allocation_changed = Event(action=Action(self.recalculate))

    def __init__(self, **kwargs):
        super(Investment, self).__init__(**kwargs)
        self.amount_or_percentage = 'percentage'
        self.amount = 0
        if not self.allocations:
            Allocation(self, 'Fund A')
            Allocation(self, 'Fund B')

    @property
    def is_in_percentage(self):
        return self.amount_or_percentage == 'percentage'

    def recalculate(self):
        for allocation in self.allocations:
            allocation.recalculate(self.amount)

    def validate_allocations(self):
        if self.is_in_percentage:
            total_percentage = sum([a.percentage for a in self.allocations])
            if total_percentage != 100:
                raise DomainException(message='Please ensure allocation percentages add up to 100')
        else:
            total_amount = sum([a.amount for a in self.allocations])
            if total_amount != self.amount:
                raise DomainException(message='Please ensure allocation amounts add up to your total amount (%s)' % self.amount)

    def submit(self):
        print('Submitting investment')
        self.recalculate()
        self.validate_allocations()

        print('\tAmount: %s' % self.amount)
        print('\tAllocations (%s)' % self.amount_or_percentage)
        for allocation in self.allocations:
            allocation_size = allocation.percentage if self.is_in_percentage else allocation.amount
            print('\t\tFund %s(%s): %s (%s)' % (allocation.fund, allocation.fund_code, allocation_size, allocation.amount))

        Session.delete(self)


class Allocation(Base):
    __tablename__ = 'dynamic_content_allocation'

    id         = Column(Integer, primary_key=True)
    percentage = Column(Integer)
    amount     = Column(Integer)
    fund       = Column(UnicodeText)
    investment_id = Column(Integer, ForeignKey(Investment.id))
    investment  = relationship('Investment', back_populates='allocations')

    @exposed
    def fields(self, fields):
        fields.percentage    = IntegerField(label='Percentage', required=True, writable=lambda field: self.is_in_percentage)
        fields.amount        = IntegerField(label='Amount', required=True, writable=lambda field: self.is_in_amount)

    def __init__(self, investment, fund_name):
        super(Allocation, self).__init__(investment=investment)
        self.fund = fund_name
        self.amount = 0
        self.percentage = 0

    @property
    def fund_code(self):
        return self.fund.replace(' ', '').upper()

    @property
    def is_in_percentage(self):
        return self.investment.is_in_percentage

    @property
    def is_in_amount(self):
        return not self.is_in_percentage

    def recalculate(self, total):
        if self.is_in_amount:
            if total == 0:
                self.percentage = 0
            else:
                self.percentage = int(round(self.amount / total * 100))
        else:
            self.amount = int(round(self.percentage / 100 * total))


