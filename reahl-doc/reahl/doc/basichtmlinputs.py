# Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from reahl.web.fw import UserInterface
from reahl.web.ui import TwoColumnPage, Panel, Form, TextInput, Button, Form, \
                          LabelOverInput, CueInput, CheckboxInput, TextInput, \
                          PasswordInput, Button, LabelledInlineInput, LabelledBlockInput, P,\
                          TextArea, SelectInput, RadioButtonInput

from reahl.component.modelinterface import exposed, Field, BooleanField, ChoiceField, Choice, ChoiceGroup, \
                                           IntegerField, Event, MultiChoiceField, Action, DateField

class BasicHTMLInputsUI(UserInterface):
    def assemble(self):
        self.define_page(TwoColumnPage, style=u'basic')  

        home = self.define_view(u'/', title=u'Basic HTML Inputs demo')
        home.set_slot(u'main', ExampleForm.factory(u'myform'))


class ModelObject(object):
    multi_choice_field = [1, 3]
    choice_field = 2
    @exposed
    def fields(self, fields):
        fields.text_input_field = Field(label=u'A TextInput')
        fields.password_field = Field(label=u'A PasswordInput')
        fields.text_area_field = Field(label=u'A TextArea')
        fields.label_over_field = Field(label=u'A TextInput in a LabelOverInput')
        fields.labelled_inline_field = Field(label=u'A TextInput in a LabelledInlineInput')
        fields.cue_field = Field(label=u'A TextInput in a CueInput')
        fields.choice_field = ChoiceField([Choice(False, BooleanField(label=u'None selected')),
                                           ChoiceGroup(u'Numbers', [Choice(1, IntegerField(label=u'One')), 
                                                                    Choice(2, IntegerField(label=u'Two')), 
                                                                    Choice(3, IntegerField(label=u'Three'))]),
                                           ChoiceGroup(u'Colours', [Choice(u'r', Field(label=u'Red')),
                                                                    Choice(u'g', Field(label=u'Green'))])
                                          ], label=u'A SelectInput')
        fields.multi_choice_field = MultiChoiceField([Choice(1, IntegerField(label=u'One')), 
                                                      Choice(2, IntegerField(label=u'Two')), 
                                                      Choice(3, IntegerField(label=u'Three'))], 
                                                      label=u'A SelectInput allowing multiple choices')
        fields.boolean_field = BooleanField(label=u'A CheckboxInput')
        fields.radio_choice_field = ChoiceField([Choice(1, IntegerField(label=u'One')), 
                                                 Choice(2, IntegerField(label=u'Two')), 
                                                 Choice(3, IntegerField(label=u'Three'))],
                                                label=u'A RadioButtonInput')
        fields.fuzzy_date_field = DateField(label=u'A fuzzy TextInput for a Date')
        
    @exposed
    def events(self, events):
        events.do_something = Event(label=u'A Button')
    

class ExampleForm(Form):
    def __init__(self, view, event_channel_name):
        super(ExampleForm, self).__init__(view, event_channel_name)
        
        model_object = ModelObject()
        self.add_child(LabelledBlockInput(TextInput(self, model_object.fields.text_input_field)))
        self.add_child(LabelledBlockInput(CheckboxInput(self, model_object.fields.boolean_field)))
        self.add_child(LabelledBlockInput(PasswordInput(self, model_object.fields.password_field)))
        self.add_child(LabelledBlockInput(TextArea(self, model_object.fields.text_area_field, rows=5, columns=60)))
        self.add_child(LabelledBlockInput(SelectInput(self, model_object.fields.choice_field)))
        self.add_child(LabelledBlockInput(SelectInput(self, model_object.fields.multi_choice_field)))
        self.add_child(LabelledBlockInput(RadioButtonInput(self, model_object.fields.radio_choice_field)))
        self.add_child(LabelledBlockInput(TextInput(self, model_object.fields.fuzzy_date_field, fuzzy=True)))

        self.add_child(LabelOverInput(TextInput(self, model_object.fields.label_over_field)))
        self.add_child(LabelledInlineInput(TextInput(self, model_object.fields.labelled_inline_field)))
        self.add_child(CueInput(TextInput(self, model_object.fields.cue_field), P(view, text=u'This is a cue')))


        self.define_event_handler(model_object.events.do_something)
        self.add_child(Button(self, model_object.events.do_something))
        
