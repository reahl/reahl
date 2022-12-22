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



from reahl.component.modelinterface import ExposedNames, Field, BooleanField, ChoiceField, Choice, ChoiceGroup, \
    IntegerField, Event, MultiChoiceField, DateField
from reahl.web.fw import UserInterface
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import P
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.grid import ColumnLayout, ColumnOptions, Container, ResponsiveSize
from reahl.web.bootstrap.forms import Form, FormLayout, ButtonInput, CueInput, TextArea, SelectInput, \
    RadioButtonSelectInput, CheckboxInput, TextInput, PasswordInput, ChoicesLayout


class BasicHTMLInputsUI(UserInterface):
    def assemble(self):
        self.define_page(HTML5Page).use_layout(PageLayout(document_layout=Container(),
                                                          contents_layout=ColumnLayout(
                                                              ColumnOptions('main', size=ResponsiveSize(lg=6))).with_slots()))
        home = self.define_view('/', title='Basic HTML Inputs demo')
        home.set_slot('main', ExampleForm.factory('myform'))


class ModelObject:
    multi_choice_field = [1, 3]
    choice_field = 2
    fields = ExposedNames()
    fields.text_input_field = lambda i: Field(label='A TextInput')
    fields.password_field = lambda i: Field(label='A PasswordInput')
    fields.text_area_field = lambda i: Field(label='A TextArea')
    fields.text_input_without_label = lambda i: Field(label='A TextInput without a label')
    fields.cue_field = lambda i: Field(label='A TextInput in a CueInput')
    fields.choice_field = lambda i: ChoiceField([Choice(False, BooleanField(label='None selected')),
                                                 ChoiceGroup('Numbers', [Choice(1, IntegerField(label='One')), 
                                                                         Choice(2, IntegerField(label='Two')),
                                                                         Choice(3, IntegerField(label='Three'))]),
                                                 ChoiceGroup('Colours', [Choice('r', Field(label='Red')),
                                                                         Choice('g', Field(label='Green'))])
                                                ],
                                                label='A SelectInput')
    fields.multi_choice_field = lambda i: MultiChoiceField([Choice(1, IntegerField(label='One')), 
                                                            Choice(2, IntegerField(label='Two')), 
                                                            Choice(3, IntegerField(label='Three'))], 
                                                           label='A SelectInput allowing multiple choices')
    fields.another_multi_choice_field = lambda i: MultiChoiceField([Choice('a', Field(label='Newton')),
                                                                    Choice('b', Field(label='Archimedes')),
                                                                    Choice('c', Field(label='Einstein')),
                                                                   ],
                                                                   default=['a', 'c'],
                                                                   label='A CheckboxInput allowing multiple choices')
    fields.boolean_field = lambda i: BooleanField(label='A CheckboxInput to toggle')
    fields.radio_choice_field = lambda i: ChoiceField([Choice(1, IntegerField(label='One')), 
                                                       Choice(2, IntegerField(label='Two')), 
                                                       Choice(3, IntegerField(label='Three'))],
                                                      label='A RadioButtonSelectInput')
    fields.fuzzy_date_field = lambda i: DateField(label='A fuzzy TextInput for a Date')
        
    events = ExposedNames()
    events.do_something = lambda i: Event(label='A Button')
    

class ExampleForm(Form):
    def __init__(self, view, event_channel_name):
        super().__init__(view, event_channel_name)
        self.use_layout(FormLayout())
        model_object = ModelObject()
        self.layout.add_input(TextInput(self, model_object.fields.text_input_field))
        self.layout.add_input(CheckboxInput(self, model_object.fields.boolean_field))
        self.layout.add_input(PasswordInput(self, model_object.fields.password_field))
        self.layout.add_input(TextArea(self, model_object.fields.text_area_field, rows=5, columns=60))
        self.layout.add_input(SelectInput(self, model_object.fields.choice_field))
        self.layout.add_input(SelectInput(self, model_object.fields.multi_choice_field))
        self.layout.add_input(CheckboxInput(self, model_object.fields.another_multi_choice_field))
        self.layout.add_input(RadioButtonSelectInput(self, model_object.fields.radio_choice_field,
                                                     contents_layout=ChoicesLayout(inline=True)))
        self.layout.add_input(TextInput(self, model_object.fields.fuzzy_date_field, fuzzy=True))
        self.layout.add_input(TextInput(self, model_object.fields.text_input_without_label, placeholder=True),
                              hide_label=True)
        self.layout.add_input(CueInput(TextInput(self, model_object.fields.cue_field), P(view, text='This is a cue')))
        self.define_event_handler(model_object.events.do_something)

        self.add_child(ButtonInput(self, model_object.events.do_something, style='primary'))

