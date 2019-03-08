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



class ResponsiveUI(UserInterface):
    def assemble(self):
        self.define_page(HTML5Page).use_layout(PageLayout(document_layout=Container(),
                                                          contents_layout=ColumnLayout(
                                                              ColumnOptions('main', size=ResponsiveSize(lg=6))).with_slots()))
        home = self.define_view('/', title='File upload demo')
        home.set_slot('main', NewInvestmentForm.factory())


class IDDocument(object):
    @exposed
    def fields(self, fields):
        types = [Choice('passport', Field(label='Passport')),
                 Choice('rsa_id', Field(label='RSA ID'))]
        fields.document_type = ChoiceField(types, label='Type', default='rsa_id', required=True)
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


class IDForm(Form):
    def __init__(self, view):
        super(IDForm, self).__init__(view, 'myform')

        new_document = IDDocument()
        grouped_inputs = self.add_child(FieldSet(view, legend_text='Identifying document'))
        grouped_inputs.use_layout(FormLayout())
        trigger = grouped_inputs.layout.add_input(SelectInput(self, new_document.fields.document_type))
        grouped_inputs.add_child(IDInputsSection(self, new_document, trigger))


class IDInputsSection(DynamicSection):
    def __init__(self, form, document, trigger_input):
        super(IDInputsSection, self).__init__(form, 'idinputs', [trigger_input])

        document_type = document.document_type
        if document_type == 'passport':
            self.add_child(PassportInputs(form, document))
        elif document_type == 'rsa_id':
            self.add_child(IDInputs(form, document))
        else:
            raise Exception(document.document_type)


class PassportInputs(Div):
    def __init__(self, form, document):
        super(PassportInputs, self).__init__(form.view)
        self.use_layout(FormLayout())
        self.layout.add_input(SelectInput(form, document.fields.country))
        self.layout.add_input(TextInput(form, document.fields.passport_number))


class IDInputs(Div):
    def __init__(self, form, document):
        super(IDInputs, self).__init__(form.view)
        self.use_layout(FormLayout())
        self.layout.add_input(TextInput(form, document.fields.id_number))


class Investment(object):
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
        fields.type         = ChoiceField([Choice('amount', Field(label='Amount')),
                                         Choice('percentage', Field(label='Percentage'))],
                                           label='Allocate using', required=True)

    @exposed('submit')
    def events(self, events):
        events.submit = Event(label='Submit', action=Action(self.submit))

    def __init__(self):
        self.id_document = IDDocument()
        self.allocations = [Allocation(self, 'Fund A'), Allocation(self, 'Fund B')]
        self.type = 'percentage'
        self.name = None
        self.surname = None
        self.amount = None
        self.existing_account_number = None
        self.new_or_existing = None
        self.agreed_to_terms = False

    @property
    def is_in_percentage(self):
        return self.type == 'percentage'

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
        print('\tAllocations (%s)' % self.type)
        for allocation in self.allocations:
            allocation_size = allocation.percentage if self.is_in_percentage else allocation.amount
            print('\t\tFund %s(%s): %s' % (allocation.fund, allocation.fund_code, allocation_size))


class Allocation(object):
    @exposed
    def fields(self, fields):
        fields.percentage    = IntegerField(label='Percentage', required=True)
        fields.amount        = IntegerField(label='Amount', required=True)

    def __init__(self, investment, fund_name):
        self.investment = investment
        self.fund = fund_name
        self.amount = 0
        self.percentage = 0

    @property
    def fund_code(self):
        return self.fund.replace(' ', '').upper()

    @property
    def is_in_percentage(self):
        return self.investment.is_in_percentage


class NewInvestorDetailsSection(FieldSet):
    def __init__(self, form, investment):
        super(NewInvestorDetailsSection, self).__init__(form.view, legend_text='New investor information')
        self.use_layout(FormLayout())
        self.layout.add_input(TextInput(form, investment.fields.name))
        self.layout.add_input(TextInput(form, investment.fields.surname))

        trigger = self.layout.add_input(SelectInput(form, investment.id_document.fields.document_type))
        self.add_child(IDInputsSection(form, investment.id_document, trigger))

        trigger = self.layout.add_input(CheckboxInput(form, investment.fields.agreed_to_terms))
        self.add_child(InvestmentAllocationSection(form, trigger, investment))


class ExistingInvestorDetailsSection(FieldSet):
    def __init__(self, form, investment):
        super(ExistingInvestorDetailsSection, self).__init__(form.view, legend_text='Existing investor information')
        self.use_layout(FormLayout())
        self.layout.add_input(TextInput(form, investment.fields.existing_account_number))
        trigger = self.layout.add_input(CheckboxInput(form, investment.fields.agreed_to_terms))
        self.add_child(InvestmentAllocationSection(form, trigger, investment))


class InvestmentAllocationSection(DynamicSection):
    def __init__(self, form, trigger_input, investment):
        super(InvestmentAllocationSection, self).__init__(form, 'investment_allocation', [trigger_input])
        if investment.agreed_to_terms:
            fieldset = self.add_child(FieldSet(form.view, legend_text='Investment allocation'))
            fieldset.use_layout(FormLayout())
            amount_input = fieldset.layout.add_input(TextInput(form, investment.fields.amount))
            type_input = fieldset.layout.add_input(RadioButtonSelectInput(form, investment.fields.type))
            self.add_child(AllocationDetailSection(form, [amount_input, type_input], investment))


class AllocationDetailSection(DynamicSection):
    def __init__(self, form, trigger_inputs, investment):
        super(AllocationDetailSection, self).__init__(form, 'investment_allocation_details', trigger_inputs)
        def make_amount_input(view, allocation):
            div = Div(view).use_layout(FormLayout())
            div.layout.add_input(TextInput(form, allocation.fields.amount, name='amount.%s' % allocation.fund_code), hide_label=True)
            return div
        def make_percentage_input(view, allocation):
            div = Div(view).use_layout(FormLayout())
            div.layout.add_input(TextInput(form, allocation.fields.percentage, name='percentage.%s' % allocation.fund_code), hide_label=True)
            return div

        columns = [StaticColumn(Field(label='Fund'), 'fund')]
        if investment.is_in_percentage:
            columns.append(DynamicColumn('Percentage', make_percentage_input))
        else:
            columns.append(DynamicColumn('Amount', make_amount_input))
        table = Table(form.view).with_data(columns, investment.allocations)
        self.add_child(table)
        self.define_event_handler(investment.events.submit)
        self.add_child(Button(form, investment.events.submit))


class NewOrExistingInvestorSection(DynamicSection):
    def __init__(self, form, trigger_input, investment):
        super(NewOrExistingInvestorSection, self).__init__(form, 'investor_details', [trigger_input])
        new_or_existing = investment.new_or_existing
        if new_or_existing == 'new':
            self.add_child(NewInvestorDetailsSection(form, investment))
        elif new_or_existing == 'existing':
            self.add_child(ExistingInvestorDetailsSection(form, investment))

            
class NewInvestmentForm(Form):
    def __init__(self, view):
        super(NewInvestmentForm, self).__init__(view, 'new_investment_form')

        if self.exception:
            self.add_child(Alert(view, str(self.exception), 'warning'))
        new_investment = Investment()
        step1 = self.add_child(FieldSet(view, legend_text='Investor information'))
        step1.use_layout(FormLayout())
#        step1.layout.add_input(RadioButtonSelectInput(self, new_investment.fields.type, name='testing1'))
#        step1.layout.add_input(TextInput(self, new_investment.fields.amount, name='testing2'))
        trigger = step1.layout.add_input(RadioButtonSelectInput(self, new_investment.fields.new_or_existing))
        self.add_child(NewOrExistingInvestorSection(self, trigger, new_investment))


