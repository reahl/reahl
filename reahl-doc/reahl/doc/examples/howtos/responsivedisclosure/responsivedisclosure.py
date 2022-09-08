# Copyright 2018-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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



from reahl.component.modelinterface import ExposedNames, Field, Event, Action, Choice, ChoiceField, IntegerField, BooleanField
from reahl.component.exceptions import DomainException
from reahl.web.fw import UserInterface
from reahl.web.ui import StaticColumn, DynamicColumn
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import FieldSet, Div, P
from reahl.web.bootstrap.grid import Container, ColumnLayout, ColumnOptions, ResponsiveSize
from reahl.web.bootstrap.forms import Form, FormLayout, TextInput, SelectInput, RadioButtonSelectInput, CheckboxInput, Button
from reahl.web.bootstrap.tables import Table

from sqlalchemy import Column, Integer, UnicodeText, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from reahl.sqlalchemysupport import Base, Session, session_scoped



class ResponsiveUI(UserInterface):
    def assemble(self):
        self.define_page(HTML5Page).use_layout(PageLayout(document_layout=Container(),
                                                          contents_layout=ColumnLayout(
                                                              ColumnOptions('main', size=ResponsiveSize(lg=6))).with_slots()))
        home = self.define_view('/', title='Responsive disclosure demo')
        home.set_slot('main', NewInvestmentForm.factory())


class NewInvestmentForm(Form):
    def __init__(self, view):
        super().__init__(view, 'new_investment_form')
        self.enable_refresh()
        self.use_layout(FormLayout())

        if self.exception:
            self.layout.add_alert_for_domain_exception(self.exception)

        investment_order = InvestmentOrder.for_current_session()
        type_of_investor = self.add_child(FieldSet(view, legend_text='Introduction'))
        type_of_investor.use_layout(FormLayout())

        new_or_existing_radio = RadioButtonSelectInput(self, investment_order.fields.new_or_existing, refresh_widget=self)
        type_of_investor.layout.add_input(new_or_existing_radio)

        if investment_order.new_or_existing:
            self.add_child(InvestorDetailsSection(self, investment_order))


class InvestorDetailsSection(Div):
    def __init__(self, form, investment_order):
        super().__init__(form.view, css_id='investor_details_section')
        self.enable_refresh()
        self.use_layout(FormLayout())

        investor_info = self.add_child(FieldSet(self.view, legend_text='Investor information'))
        investor_info.use_layout(FormLayout())

        if investment_order.new_or_existing == 'new':
            investor_info.layout.add_input(TextInput(form, investment_order.fields.name))
            investor_info.layout.add_input(TextInput(form, investment_order.fields.surname))
            self.add_child(IDDocumentSection(form, investment_order.id_document))

        elif investment_order.new_or_existing == 'existing':
            investor_info.layout.add_input(TextInput(form, investment_order.fields.existing_account_number))

        self.layout.add_input(CheckboxInput(form, investment_order.fields.agreed_to_terms, refresh_widget=self))
        if investment_order.agreed_to_terms:
            self.add_child(AllocationDetailSection(form, investment_order))


class IDDocumentSection(FieldSet):
    def __init__(self, form, id_document):
        super().__init__(form.view, legend_text='New investor information', css_id='id_document_section')
        self.enable_refresh()
        self.use_layout(FormLayout())

        self.layout.add_input(SelectInput(form, id_document.fields.document_type,  refresh_widget=self))
        document_type = id_document.document_type
        if document_type == 'passport':
            self.layout.add_input(SelectInput(form, id_document.fields.country))
            self.layout.add_input(TextInput(form, id_document.fields.passport_number))
        elif document_type == 'id_card':
            self.layout.add_input(TextInput(form, id_document.fields.id_card_number))
        else:
            raise Exception(id_document.document_type)


class AllocationDetailSection(Div):
    def __init__(self, form, investment_order):
        super().__init__(form.view, css_id='investment_allocation_details')
        self.form = form
        self.use_layout(FormLayout())

        self.investment_order = investment_order    
        self.enable_refresh(on_refresh=self.investment_order.events.allocation_changed)

        self.add_allocation_controls()
        self.add_allocation_table()

        self.define_event_handler(self.investment_order.events.submit)
        self.add_child(Button(self.form, self.investment_order.events.submit))

    def add_allocation_controls(self):
        allocation_controls = self.add_child(FieldSet(self.view, legend_text='Investment allocation'))
        allocation_controls.use_layout(FormLayout())

        if self.form.exception:
            self.layout.add_alert_for_domain_exception(self.form.exception, form=self.form, unique_name='details_section')
        
        total_amount_input = TextInput(self.form, self.investment_order.fields.amount, refresh_widget=self)
        allocation_controls.layout.add_input(total_amount_input)

        amount_or_percentage_radio = RadioButtonSelectInput(self.form, self.investment_order.fields.amount_or_percentage, refresh_widget=self)
        allocation_controls.layout.add_input(amount_or_percentage_radio)

    def make_allocation_input(self, allocation, field):
        div = Div(self.view).use_layout(FormLayout())
        div.layout.add_input(TextInput(self.form, field.with_discriminator(allocation.fund_code), refresh_widget=self), hide_label=True)
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

        columns = [StaticColumn(Field(label='Fund'), 'fund', footer_label='Totals'),
                   DynamicColumn('Percentage', make_percentage_input, make_footer_widget=make_percentage_total),
                   DynamicColumn('Amount', make_amount_input, make_footer_widget=make_amount_total)]
        table = Table(self.view).with_data(columns, self.investment_order.allocations,
                                           footer_items=[self.investment_order])
        self.add_child(table)


@session_scoped
class InvestmentOrder(Base):
    __tablename__ = 'rspnsv_disc_investment_order'

    id              = Column(Integer, primary_key=True)
    agreed_to_terms = Column(Boolean)
    new_or_existing = Column(UnicodeText)
    existing_account_number = Column(Integer)
    name            = Column(UnicodeText)
    surname         = Column(UnicodeText)
    amount          = Column(Integer)
    amount_or_percentage = Column(UnicodeText)
    allocations     = relationship('reahl.doc.examples.howtos.responsivedisclosure.responsivedisclosure.Allocation',
                                   back_populates='investment_order', lazy='immediate', cascade="all, delete-orphan")
    id_document     = relationship('reahl.doc.examples.howtos.responsivedisclosure.responsivedisclosure.IDDocument',
                                   uselist=False, back_populates='investment_order', cascade="all, delete-orphan")

    fields = ExposedNames()
    fields.agreed_to_terms = lambda i: BooleanField(label='I agree to the terms and conditions')
    fields.new_or_existing = lambda i: ChoiceField([Choice('new', Field(label='New')),
                                                    Choice('existing', Field(label='Existing'))],
                                                   label='Are you a new or existing investor?')
    fields.existing_account_number = lambda i: IntegerField(label='Existing account number', required=True)
    fields.name         = lambda i: Field(label='Name', required=True)
    fields.surname      = lambda i: Field(label='Surname', required=True)
    fields.amount       = lambda i: IntegerField(label='Total amount', required=True)
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
        self.name = None
        self.surname = None
        self.amount = 0
        self.existing_account_number = None
        self.new_or_existing = None
        self.agreed_to_terms = False
        self.allocations = [
            Allocation(self, 'Fund A'),
            Allocation(self, 'Fund B')
        ]
        self.id_document = IDDocument(investment_order=self)

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

        if self.new_or_existing == 'new':
            print('\tName: %s' % self.name)
            print('\tSurname: %s' % self.surname)
            print('\t%s' % str(self.id_document))
        else:
            print('\tExisting account number: %s' % self.existing_account_number)
        print('\tAgreed to terms: %s' % self.agreed_to_terms)
        print('\tAmount: %s' % self.amount)
        print('\tAllocations (%s)' % self.amount_or_percentage)
        for allocation in self.allocations:
            allocation_size = allocation.percentage if self.is_in_percentage else allocation.amount
            print('\t\tFund %s(%s): %s (%s)' % (allocation.fund, allocation.fund_code, allocation_size, allocation.amount))

        self.clear()


class Allocation(Base):
    __tablename__ = 'rspnsv_disc_allocation'

    id         = Column(Integer, primary_key=True)
    percentage = Column(Integer)
    amount     = Column(Integer)
    fund       = Column(UnicodeText)
    investment_id = Column(Integer, ForeignKey(InvestmentOrder.id))
    investment_order  = relationship('reahl.doc.examples.howtos.responsivedisclosure.responsivedisclosure.InvestmentOrder', back_populates='allocations')

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


class IDDocument(Base):
    __tablename__ = 'rspnsv_disc_iddoc'

    id         = Column(Integer, primary_key=True)
    
    document_type = Column(UnicodeText)
    id_card_number     = Column(UnicodeText)
    passport_number = Column(UnicodeText)
    country = Column(UnicodeText)
    investment_id = Column(Integer, ForeignKey(InvestmentOrder.id))
    investment_order  = relationship('reahl.doc.examples.howtos.responsivedisclosure.responsivedisclosure.InvestmentOrder', back_populates='id_document')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.document_type = 'id_card'

    fields = ExposedNames()
    fields.document_type = lambda i: ChoiceField([Choice('passport', Field(label='Passport')),
                                                  Choice('id_card', Field(label='National ID Card'))],
                                                 label='Type', required=True)
    fields.id_card_number  = lambda i: Field(label='ID card number', required=True)
    fields.passport_number = lambda i: Field(label='Passport number', required=True)
    fields.country = lambda i: ChoiceField([
        Choice('Australia', Field(label='Australia')),
        Choice('Chile', Field(label='Chile')),
        Choice('China', Field(label='China')),
        Choice('France', Field(label='France')),
        Choice('Germany', Field(label='Germany')),
        Choice('Ghana', Field(label='Ghana')),
        Choice('India', Field(label='India')),
        Choice('Japan', Field(label='Japan')),
        Choice('Kenya', Field(label='Kenya')),
        Choice('Namibia', Field(label='Namibia')),
        Choice('Nigeria', Field(label='Nigeria')),
        Choice('South Africa', Field(label='South Africa')),
        Choice('United States', Field(label='United States of America')),
        Choice('United Kingdom', Field(label='United Kingdom')),
        Choice('Zimbabwe', Field(label='Zimbabwe'))
    ], label='Country', required=True)

    def __str__(self):
        if self.document_type == 'id_card':
            return 'ID Card: %s' % self.id_card_number
        else:
            return 'Passport (%s): %s' % (self.country, self.passport_number)


