# Copyright 2019, 2020, 2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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



from reahl.component.modelinterface import ExposedNames, Field, Event, Action, Choice, ChoiceField, IntegerField
from reahl.component.exceptions import DomainException
from reahl.web.fw import UserInterface
from reahl.web.ui import StaticColumn, DynamicColumn
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import FieldSet, Div, P
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
        super().__init__(view, 'investment_order_allocation_details_form')
        self.use_layout(FormLayout())

        self.investment_order = InvestmentOrder.for_current_session()
        self.enable_refresh(on_refresh=self.investment_order.events.allocation_changed)

        self.add_allocation_controls()
        self.add_allocation_table()

        self.define_event_handler(self.investment_order.events.submit)
        self.add_child(Button(self, self.investment_order.events.submit))

    def add_allocation_controls(self):
        allocation_controls = self.add_child(FieldSet(self.view, legend_text='Investment allocation'))
        allocation_controls.use_layout(FormLayout())

        if self.exception:
            self.layout.add_alert_for_domain_exception(self.exception)
        
        total_amount_input = TextInput(self, self.investment_order.fields.amount, refresh_widget=self)
        allocation_controls.layout.add_input(total_amount_input)

        amount_or_percentage_radio = RadioButtonSelectInput(self, self.investment_order.fields.amount_or_percentage, refresh_widget=self)
        allocation_controls.layout.add_input(amount_or_percentage_radio)

    def make_allocation_input(self, allocation, field):
        div = Div(self.view).use_layout(FormLayout())
        div.layout.add_input(TextInput(self, field.with_discriminator(allocation.fund_code), refresh_widget=self), hide_label=True)
        return div

    def make_total_widget(self, total_value):
        return P(self.view, text=str(total_value))

    def add_allocation_table(self):
        def make_amount_input(view, allocation):
            return self.make_allocation_input(allocation, allocation.fields.amount)

        def make_percentage_input(view, allocation):
            return self.make_allocation_input(allocation, allocation.fields.percentage)

        def make_percentage_total(view, investment_order):
            return self.make_total_widget(investment_order.total_allocation_percentage)

        def make_amount_total(view, investment_order):
            return self.make_total_widget(investment_order.total_allocation_amount)

        columns = [StaticColumn(Field(label='Fund'), 'fund', footer_label='Totals')]
        columns.append(DynamicColumn('Percentage', make_percentage_input, make_footer_widget=make_percentage_total))
        columns.append(DynamicColumn('Amount', make_amount_input, make_footer_widget=make_amount_total))
        table = Table(self.view).with_data(columns, self.investment_order.allocations,
                                           footer_items=[self.investment_order])
        self.add_child(table)


@session_scoped
class InvestmentOrder(Base):
    __tablename__ = 'dynamic_content_investment_order'

    id              = Column(Integer, primary_key=True)
    amount          = Column(Integer)
    amount_or_percentage = Column(UnicodeText)
    allocations     = relationship('reahl.doc.examples.tutorial.dynamiccontent.dynamiccontent.Allocation',
                                   back_populates='investment_order', lazy='immediate', cascade="all, delete-orphan")

    fields = ExposedNames()
    fields.amount                = lambda i: IntegerField(label='Total amount', required=True)
    fields.amount_or_percentage  = lambda i: ChoiceField([Choice('amount', Field(label='Amount')),
                                                          Choice('percentage', Field(label='Percentage'))],
                                                         label='Allocate using', required=True)

    events = ExposedNames()
    events.submit = lambda i: Event(label='Submit', action=Action(i.submit))
    events.allocation_changed = lambda i: Event(action=Action(i.recalculate))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.clear()

    def clear(self):
        self.amount_or_percentage = 'percentage'
        self.amount = 0
        self.allocations = [
            Allocation(self, 'Fund A'),
            Allocation(self, 'Fund B')]

    @property
    def is_in_percentage(self):
        return self.amount_or_percentage == 'percentage'

    def recalculate(self):
        for allocation in self.allocations:
            allocation.recalculate(self.amount)

    @property
    def total_allocation_amount(self):
       return sum([i.amount for i in self.allocations])

    @property
    def total_allocation_percentage(self):
        return sum([i.percentage for i in self.allocations])

    def validate_allocations(self):
        if self.is_in_percentage:
            if self.total_allocation_percentage != 100:
                raise DomainException(message='Please ensure allocation percentages add up to 100')
        else:
            if self.total_allocation_amount != self.amount:
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

        self.clear()


class Allocation(Base):
    __tablename__ = 'dynamic_content_allocation'

    id         = Column(Integer, primary_key=True)
    percentage = Column(Integer)
    amount     = Column(Integer)
    fund       = Column(UnicodeText)
    investment_order_id = Column(Integer, ForeignKey(InvestmentOrder.id))
    investment_order  = relationship('reahl.doc.examples.tutorial.dynamiccontent.dynamiccontent.InvestmentOrder', back_populates='allocations')

    fields = ExposedNames()
    fields.percentage    = lambda i: IntegerField(label='Percentage', required=True, writable=lambda field: i.is_in_percentage)
    fields.amount        = lambda i: IntegerField(label='Amount', required=True, writable=lambda field: i.is_in_amount)

    def __init__(self, investment_order, fund_name):
        super().__init__(investment_order=investment_order)
        self.fund = fund_name
        self.amount = 0
        self.percentage = 0

    @property
    def fund_code(self):
        return self.fund.replace(' ', '').upper()

    @property
    def is_in_percentage(self):
        return self.investment_order.is_in_percentage

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

