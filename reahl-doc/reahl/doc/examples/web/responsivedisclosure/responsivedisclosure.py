# Copyright 2013-2018 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.component.modelinterface import exposed, EmailField, Field, Event, Action, FileField, Choice, ChoiceField
from reahl.web.fw import UserInterface
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.ui import FieldSet, HTML5Page, Div, P
from reahl.web.bootstrap.files import FileUploadInput
from reahl.web.bootstrap.grid import Container, ColumnLayout, ColumnOptions, ResponsiveSize
from reahl.web.bootstrap.forms import Form, FormLayout, ButtonInput, ButtonLayout, TextInput, SelectInput



class ResponsiveUI(UserInterface):
    def assemble(self):
        self.define_page(HTML5Page).use_layout(PageLayout(document_layout=Container(),
                                                          contents_layout=ColumnLayout(
                                                              ColumnOptions('main', size=ResponsiveSize(lg=6))).with_slots()))
        home = self.define_view('/', title='File upload demo')
        home.set_slot('main', IDForm.factory())


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




class IDForm(Form):
    def __init__(self, view):
        super(IDForm, self).__init__(view, 'myform')

        new_document = IDDocument()
        grouped_inputs = self.add_child(FieldSet(view, legend_text='Identifying document'))
        grouped_inputs.use_layout(FormLayout())
        trigger = grouped_inputs.layout.add_input(SelectInput(self, new_document.fields.document_type))
        grouped_inputs.add_child(IDInputsSection(self, new_document, trigger))


class IDInputsSection(Div):
    def __init__(self, form, document, trigger_input):
        self.document = document
        super(IDInputsSection, self).__init__(form.view, css_id='idinputs')
        self.enable_refresh()
        trigger_input.enable_notify_change(self.query_fields.document_type)

        if self.document.document_type == 'passport':
            self.add_child(PassportInputs(form, self.document))
        elif self.document.document_type == 'rsa_id':
            self.add_child(IDInputs(form, self.document))

    @exposed
    def query_fields(self, fields):
        fields.document_type = self.document.fields.document_type



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


        



