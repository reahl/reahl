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

from reahl.component.modelinterface import exposed, EmailField, Field, Event, Action, FileField, Choice, ChoiceField, IntegerField, BooleanField
from reahl.component.exceptions import DomainException
from reahl.web.fw import UserInterface
from reahl.web.ui import StaticColumn, DynamicColumn
from reahl.web.layout import PageLayout
from reahl.web.dynamic import DynamicSection
from reahl.web.bootstrap.ui import FieldSet, HTML5Page, Div, P, HTMLWidget, Alert
from reahl.web.bootstrap.files import FileUploadInput
from reahl.web.bootstrap.grid import Container, ColumnLayout, ColumnOptions, ResponsiveSize
from reahl.web.bootstrap.forms import Form, FormLayout, ButtonInput, ButtonLayout, TextInput, SelectInput, RadioButtonSelectInput, CheckboxInput, Button
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



class NewInvestorDetailsSection(Div):
    def __init__(self, form, investment):
        super(NewInvestorDetailsSection, self).__init__(form.view, css_id='new_investor_details_section')
        self.enable_refresh()
        self.use_layout(FormLayout())

        personal_info = self.add_child(FieldSet(self.view, legend_text='New investor information'))
        personal_info.use_layout(FormLayout())
        personal_info.layout.add_input(TextInput(form, investment.fields.name))
        personal_info.layout.add_input(TextInput(form, investment.fields.surname))


        document_info = self.add_child(FieldSet(self.view, legend_text='Identifying document'))
        document_info.use_layout(FormLayout())
        document_info.layout.add_input(SelectInput(form, investment.id_document.fields.document_type,  refresh_widget=self))
        document_type = investment.id_document.document_type
        if document_type == 'passport':
            document_info.layout.add_input(SelectInput(form, investment.id_document.fields.country))
            document_info.layout.add_input(TextInput(form, investment.id_document.fields.passport_number))
        elif document_type == 'rsa_id':
            document_info.layout.add_input(TextInput(form, investment.id_document.fields.id_number))
        else:
            raise Exception(investment.id_document.document_type)


        self.layout.add_input(CheckboxInput(form, investment.fields.agreed_to_terms, refresh_widget=self))
        self.add_child(InvestmentAllocationSection(form, investment))


class ExistingInvestorDetailsSection(FieldSet):
    def __init__(self, form, investment):
        super(ExistingInvestorDetailsSection, self).__init__(form.view, legend_text='Existing investor information', css_id='existing_investor_details_section')
        self.enable_refresh()
        self.use_layout(FormLayout())
        self.layout.add_input(TextInput(form, investment.fields.existing_account_number))
        self.layout.add_input(CheckboxInput(form, investment.fields.agreed_to_terms, refresh_widget=self))
        if investment.agreed_to_terms:
            self.add_child(InvestmentAllocationSection(form, investment))


class InvestmentAllocationSection(Div):
    def __init__(self, form, investment):
        super(InvestmentAllocationSection, self).__init__(form.view, css_id='investment_allocation_section')
        self.enable_refresh()
        if investment.agreed_to_terms:
            fieldset = self.add_child(FieldSet(form.view, legend_text='Investment allocation'))
            fieldset.use_layout(FormLayout())
            fieldset.layout.add_input(TextInput(form, investment.fields.amount, refresh_widget=self))
            fieldset.layout.add_input(RadioButtonSelectInput(form, investment.fields.amount_or_percentage, refresh_widget=self))
            self.add_child(AllocationDetailSection(form, investment))


class AllocationDetailSection(Div):
    def __init__(self, form, investment):
        super(AllocationDetailSection, self).__init__(form.view, css_id='investment_allocation_details')
        self.enable_refresh()
        investment.recalculate()
        def make_amount_input(view, allocation):
            if isinstance(allocation, Allocation):
                div = Div(view).use_layout(FormLayout())
                div.layout.add_input(TextInput(form, allocation.fields.amount, name='amount.%s' % allocation.fund_code, refresh_widget=self), hide_label=True)
                return div
            else:
                return P(view, text=str(allocation.amount))
        def make_percentage_input(view, allocation):
            if isinstance(allocation, Allocation):
                div = Div(view).use_layout(FormLayout())
                div.layout.add_input(TextInput(form, allocation.fields.percentage, name='percentage.%s' % allocation.fund_code, refresh_widget=self), hide_label=True)
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
        table = Table(form.view).with_data(columns, investment.allocations+[TotalsRow(investment)])
        self.add_child(table)
        self.define_event_handler(investment.events.submit)
        self.add_child(Button(form, investment.events.submit))


class NewInvestmentForm(Form):
    def __init__(self, view):
        super(NewInvestmentForm, self).__init__(view, 'new_investment_form')
        self.enable_refresh()

        if self.exception:
            self.add_child(Alert(view, str(self.exception), 'warning'))

        investment = Investment.for_current_session()
        step1 = self.add_child(FieldSet(view, legend_text='Investor information'))
        step1.use_layout(FormLayout())

        step1.layout.add_input(RadioButtonSelectInput(self, investment.fields.new_or_existing, refresh_widget=self))

        new_or_existing = investment.new_or_existing
        if new_or_existing == 'new':
            self.add_child(NewInvestorDetailsSection(self, investment))
        elif new_or_existing == 'existing':
            self.add_child(ExistingInvestorDetailsSection(self, investment))


@session_scoped
class Investment(Base):
    __tablename__ = 'responsive_disclosure_investment'

    id              = Column(Integer, primary_key=True)
    agreed_to_terms = Column(Boolean)
    new_or_existing = Column(UnicodeText)
    existing_account_number = Column(Integer)
    name            = Column(UnicodeText)
    surname         = Column(UnicodeText)
    amount          = Column(Integer)
    amount_or_percentage = Column(UnicodeText)
    allocations     = relationship('Allocation', back_populates='investment')
    id_document     = relationship('IDDocument', uselist=False, back_populates='investment')

    @exposed
    def fields(self, fields):
        fields.agreed_to_terms = BooleanField(label='I agree to the terms and conditions')
        fields.new_or_existing = ChoiceField([Choice('new', Field(label='New')),
                                              Choice('existing', Field(label='Existing'))],
                                             label='Are you a new or existing investor?')
        fields.existing_account_number = IntegerField(label='Existing account number', required=True)
        fields.name         = Field(label='Name', required=True)
        fields.surname      = Field(label='Surname', required=True)
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
        self.name = None
        self.surname = None
        self.amount = 0
        self.existing_account_number = None
        self.new_or_existing = None
        self.agreed_to_terms = False
        if not self.allocations:
            self.allocations.append(Allocation(self, 'Fund A'))
            self.allocations.append(Allocation(self, 'Fund B'))
        if not self.id_document:
            self.id_document = IDDocument(investment=self)

    @property
    def is_in_percentage(self):
        return self.amount_or_percentage == 'percentage'

    def recalculate(self):
        for allocation in self.allocations:
            allocation.recalculate(self.amount)

    def submit(self):
        print('Submitting investment')
        if self.amount == 666:
            raise DomainException(message='hahaha')
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
            print('\t\tFund %s(%s): %s' % (allocation.fund, allocation.fund_code, allocation_size))


class Allocation(Base):
    __tablename__ = 'responsive_disclosure_allocation'

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
        print('Updated %s: amount(%s) percentage(%s)' % (self.fund, self.amount, self.percentage))


class IDDocument(Base):
    __tablename__ = 'responsive_disclosure_iddocument'

    id         = Column(Integer, primary_key=True)
    
    document_type = Column(UnicodeText, default='rsa_id')
    id_number     = Column(UnicodeText)
    passport_number = Column(UnicodeText)
    country = Column(UnicodeText)
    investment_id = Column(Integer, ForeignKey(Investment.id))
    investment  = relationship('Investment', back_populates='id_document')


    @exposed
    def fields(self, fields):
        types = [Choice('passport', Field(label='Passport')),
                 Choice('rsa_id', Field(label='RSA ID'))]
        fields.document_type = ChoiceField(types, label='Type', required=True)
        fields.id_number     = Field(label='ID number', required=True)
        fields.passport_number = Field(label='Passport number', required=True)
        countries = [Choice('Ghana', Field(label='Ghana')),
                     Choice('South Africa', Field(label='South Africa')),
                     Choice('Nigeria', Field(label='Nigeria')),
                     Choice('Namibia', Field(label='Namibia')),
                     Choice('Zimbabwe', Field(label='Zimbabwe')),
                     Choice('Kenya', Field(label='Kenya'))
                     ]
        fields.country = ChoiceField(countries, label='Country', required=True)

    def __str__(self):
        if self.document_type == 'rsa_id':
            return 'RSA ID: %s' % self.id_number
        else:
            return 'Passport (%s): %s' % (self.country, self.passport_number)

