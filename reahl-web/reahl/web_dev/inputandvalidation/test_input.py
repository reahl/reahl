# Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.
#-*- encoding: utf-8 -*-
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

import warnings
import re

from reahl.tofu import scenario, test, vassert, expected
from reahl.stubble import EmptyStub

from reahl.web.ui import HTMLElement, PrimitiveInput, Form, CheckboxInput, TextInput, Label, ButtonInput,\
                          PasswordInput, TextArea, SelectInput, RadioButtonInput

from reahl.component.modelinterface import Field, EmailField, BooleanField, Event, Allowed, exposed, \
    Action, Choice, ChoiceGroup, ChoiceField, IntegerField,MultiChoiceField, DateField
from reahl.component.exceptions import IsInstance
from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import WidgetTester
from reahl.webdev.tools import XPath
from reahl.component_dev.test_field import FieldMixin


class InputMixin(FieldMixin):
    def new_form(self):
        return Form(self.view, 'test')

    def new_event(self, label='click me'):
        event = Event(label=label)
        event.bind('aname', None)
        self.form.define_event_handler(event)
        return event


class SimpleInputFixture(WebFixture, InputMixin):
    pass


class InputMixin2(InputMixin):
    def new_field(self, label='the label'):
        return Field(label=label)
    def new_model_object(self):
        fixture = self
        class ModelObject(object):
            def handle_event(self):
                pass
            @exposed
            def events(self, events):
                events.an_event = Event(label='click me', action=Action(self.handle_event))
            @exposed
            def fields(self, fields):
                fields.an_attribute = fixture.field
        return ModelObject()


class InputStateFixture(WebFixture, InputMixin):
    def new_field(self):
        field = EmailField(default='default value')
        field.bind('an_attribute', self.model_object)
        return field

    def new_input(self):    
        return PrimitiveInput(self.form, self.field)

    @scenario
    def defaulted_input_no_value_on_domain(self):
        del self.model_object.an_attribute
        self.input.prepare_input()

        self.expected_state = 'defaulted'
        self.expected_value = 'default value'

    @scenario
    def defaulted_input_value_on_domain(self):
        self.input.prepare_input()
        self.model_object.an_attribute = 'something'

        self.expected_state = 'defaulted'
        self.expected_value = 'something'

    @scenario
    def validly_entered(self):
        self.input.enter_value('someone@home.org')
        self.input.prepare_input()

        self.expected_state = 'validly_entered' 
        self.expected_value = 'someone@home.org'

    @scenario
    def empty_input_non_required_field(self):
        self.input.enter_value('')
        self.input.prepare_input()

        self.expected_state = 'validly_entered' 
        self.expected_value = ''

    @scenario
    def empty_input_required_field(self):
        self.field.make_required('')
        self.input.enter_value('')
        self.input.prepare_input()

        self.expected_state = 'invalidly_entered' 
        self.expected_value = ''

    @scenario
    def invalidly_entered(self):
        self.input.enter_value('not an email address')
        self.input.prepare_input()

        self.expected_state = 'invalidly_entered' 
        self.expected_value = 'not an email address'


@test(InputStateFixture)
def the_states_of_an_input(fixture):
    """An Input can be in one of three states: defaulted, invalidly_entered or validly_entered. Depending
       on the state of the input, it will have a different value when rendering.

       The states:
         - defaulted: the user has not entered anything
           value:     the value on the model object which is bound to its Field if that object
                      has such an an_attribute, else the default value of the Field.
         - invalidly_entered: the user entered a value which failed validation
           value:             the invalid value which the user entered
         - validly_entered: the user entered a valid value
           value:           the value which the user entered even if the underlying
                            model object has a corresponding value
    """
    vassert( fixture.input.get_input_status() == fixture.expected_state )
    vassert( fixture.input.value == fixture.expected_value )


class Scenarios(WebFixture, InputMixin):
    @scenario
    def text_input(self):
        self.widget = TextInput(self.form, self.field)
        self.expected_html = r'<input name="an_attribute" form="test" type="text" value="field value" class="reahl-textinput">'
        self.field_controls_visibility = True

    @scenario
    def text_input_placeholder_default(self):
        self.widget = TextInput(self.form, self.field, placeholder=True)
        self.expected_html = r'<input name="an_attribute" form="test" placeholder="the label" type="text" value="field value" class="reahl-textinput">'
        self.field_controls_visibility = True

    @scenario
    def text_input_placeholder_specified(self):
        self.widget = TextInput(self.form, self.field, placeholder="some text")
        self.expected_html = r'<input name="an_attribute" form="test" placeholder="some text" type="text" value="field value" class="reahl-textinput">'
        self.field_controls_visibility = True

    @scenario
    def input_label(self):
        html_input = TextInput(self.form, self.field)
        self.widget = Label(self.view, for_input=html_input)
        self.expected_html = r'<label for="%s">the label</label>' % html_input.css_id
        self.field_controls_visibility = True

    @scenario
    def input_label_with_text(self):
        html_input = TextInput(self.form, self.field)
        self.widget = Label(self.view, for_input=html_input, text='some text')
        self.expected_html = r'<label for="%s">some text</label>' % html_input.css_id
        self.field_controls_visibility = True

    @scenario
    def button_input(self):
        self.widget = self.form.add_child(ButtonInput(self.form, self.event))
        self.expected_html = r'<input name="event.aname\?" form="test" type="submit" value="click me">'
        self.field_controls_visibility = False

    @scenario
    def password(self):
        self.widget = self.form.add_child(PasswordInput(self.form, self.field))
        self.expected_html = r'<input name="an_attribute" form="test" type="password">'
        self.field_controls_visibility = True

    def setup_checkbox_scenario(self, boolean_value):
        self.model_object.an_attribute = boolean_value

        self.field = BooleanField(required=True, label='my text', required_message='$label is needed here')
        self.field.bind('an_attribute', self.model_object)

        self.widget = self.form.add_child(CheckboxInput(self.form, self.field))
        self.field_controls_visibility = True

    @scenario
    def checkbox_true(self):
        """A checkbox needs a 'checked' an_attribute if its field is True. It also renders ONLY the
            validation message for its required validation_constraint, not for all constraints"""
        self.setup_checkbox_scenario(True)
        self.expected_html = r'<input name="an_attribute" checked="checked" data-msg-required="my text is needed here" form="test" required="\*" type="checkbox">'

    @scenario
    def checkbox_false(self):
        self.setup_checkbox_scenario(False)
        self.expected_html = r'<input name="an_attribute" data-msg-required="my text is needed here" form="test" required="\*" type="checkbox">'

    @scenario
    def text_area_input(self):
        self.widget = self.form.add_child(TextArea(self.form, self.field, rows=30, columns=20))
        self.expected_html = r'<textarea name="an_attribute" cols="20" rows="30">field value</textarea>'
        self.field_controls_visibility = True

    @scenario
    def select_input(self):
        self.model_object.an_attribute = 2

        choices = [Choice(False, BooleanField(label='None')),
                   ChoiceGroup('grouped', [
                       Choice(1, IntegerField(label='One')),
                       Choice(2, IntegerField(label='Two'))])
                  ]
        self.field = ChoiceField(choices)
        self.field.bind('an_attribute', self.model_object)

        self.widget = self.form.add_child(SelectInput(self.form, self.field))
        group = r'<optgroup label="grouped"><option value="1">One</option><option selected="selected" value="2">Two</option></optgroup>'
        option = r'<option value="off">None</option>'
        self.expected_html = r'<select name="an_attribute" form="test">%s%s</select>' % (option, group)
        self.field_controls_visibility = True

    @scenario
    def select_input_multi(self):
        self.model_object.an_attribute = [2]

        choices = [Choice(1, IntegerField(label='One')),
                   Choice(2, IntegerField(label='Two'))
                  ]
        self.field = MultiChoiceField(choices)
        self.field.bind('an_attribute', self.model_object)

        self.widget = self.form.add_child(SelectInput(self.form, self.field))
        options = r'<option value="1">One</option><option selected="selected" value="2">Two</option>'
        self.expected_html = r'<select name="an_attribute" form="test" multiple="multiple">%s</select>' % (options)
        self.field_controls_visibility = True

    @scenario
    def radio_button(self):
        self.model_object.an_attribute = 2

        choices = [ Choice(1, IntegerField(label='One')),
                    Choice(2, IntegerField(label='Two')) ]
        self.field = ChoiceField(choices)
        self.field.bind('an_attribute', self.model_object)

        self.widget = self.form.add_child(RadioButtonInput(self.form, self.field))

        radio_button = r'<span class="reahl-radio-button">'\
                       r'<input name="an_attribute"%s '\
                              r'data-msg-pattern="an_attribute should be one of the following: 1|2" '\
                              r'form="test" pattern="\(1\|2\)" '\
                              r'title="an_attribute should be one of the following: 1\|2" '\
                              r'type="radio" value="%s">%s'\
                       r'</span>'

        outer_div = r'<div class="reahl-radio-button-input">%s</div>'
        buttons = (radio_button % ('', '1', 'One')) +\
                  (radio_button % (' checked="checked"', '2', 'Two'))
        self.expected_html = outer_div % buttons
        self.field_controls_visibility = True


@test(Scenarios)
def basic_rendering(fixture):
    """What the rendered html for a number of simple inputs look like."""

    tester = WidgetTester(fixture.widget)
    actual = tester.render_html()
    vassert( re.match(fixture.expected_html, actual) )


@test(Scenarios)
def rendering_when_not_allowed(fixture):
    """When not allowed to see the Widget, it is not rendered."""
    tester = WidgetTester(fixture.widget)

    fixture.field.access_rights.readable = Allowed(False)
    fixture.field.access_rights.writable = Allowed(False)
    actual = tester.render_html()
    if fixture.field_controls_visibility:
        vassert( actual == '' )
    else:
        vassert( re.match(fixture.expected_html, actual) )


@test(SimpleInputFixture)
def backwards_compatibility(fixture):
    """We still support overriding create_html_input for backwards compatibility."""

    # Case when old interface is overridden
    class OldInput(TextInput):
        def create_html_input(self):
            return super(OldInput, self).create_html_widget()

    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter('always')
        html_input = OldInput(fixture.form, fixture.field)

    vassert( caught_warnings )
    tester = WidgetTester(html_input)

    actual = tester.render_html()
    vassert( actual ) # Something was rendered.

    # Case when new interface is used
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter('always')
        html_input = TextInput(fixture.form, fixture.field)
    vassert( not caught_warnings )


@test(SimpleInputFixture)
def input_wrapped_widgets(fixture):
    """An Input is an empty Widget; its contents are supplied by overriding its 
       .create_html_widget() method. Several methods for setting HTML-things, like 
       css id are delegated to this Widget which represents the Input in HTML.
    """
    class MyInput(PrimitiveInput):
        def create_html_widget(self):
            return HTMLElement(self.view, 'x')

    test_input = MyInput(fixture.form, fixture.field)
    tester = WidgetTester(test_input)

    rendered = tester.render_html()
    vassert( rendered == '<x>' )

    test_input.set_id('myid')
    test_input.set_title('mytitle')
    test_input.add_to_attribute('list-attribute', ['one', 'two'])
    test_input.set_attribute('an-attribute', 'a value')

    rendered = tester.render_html()
    vassert( rendered == '<x id="myid" an-attribute="a value" list-attribute="one two" title="mytitle">' )


@test(SimpleInputFixture)
def wrong_args_to_input(fixture):
    """Passing the wrong arguments upon constructing an Input results in an error."""

    with expected(IsInstance):
        PrimitiveInput(fixture.form, EmptyStub())

    with expected(IsInstance):
        PrimitiveInput(EmptyStub(), Field())


class CheckboxFixture(WebFixture, InputMixin2):
    def new_field(self):
        return BooleanField(label='my text')


@test(CheckboxFixture)
def marshalling_of_checkbox(fixture):
    """When a form is submitted, the value of a checkbox is derived from
       whether the checkbox is included in the submission or not."""

    model_object = fixture.model_object
    class MyForm(Form):
        def __init__(self, view, name):
            super(MyForm, self).__init__(view, name)
            checkbox = self.add_child(CheckboxInput(self, model_object.fields.an_attribute))
            self.define_event_handler(model_object.events.an_event)
            self.add_child(ButtonInput(self, model_object.events.an_event))
            fixture.checkbox = checkbox

    wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory('myform'))
    fixture.reahl_server.set_app(wsgi_app)
    fixture.driver_browser.open('/')

    # Case: checkbox is submitted with form (ie checked)
    fixture.driver_browser.check("//input[@type='checkbox']")
    fixture.driver_browser.click("//input[@value='click me']")

    vassert( model_object.an_attribute )
    vassert( fixture.checkbox.value == 'on' )

    # Case: checkbox is not submitted with form (ie unchecked)
    fixture.driver_browser.uncheck("//input[@type='checkbox']")
    fixture.driver_browser.click("//input[@value='click me']")

    vassert( not model_object.an_attribute )
    vassert( fixture.checkbox.value == 'off' )


class FuzzyTextInputFixture(WebFixture, InputMixin2):
    def new_field(self, label='the label'):
        return DateField(label=label)


@test(FuzzyTextInputFixture)
def fuzzy(fixture):
    """A TextInput can be created as fuzzy=True. Doing this results in the possibly imprecise
       input that was typed by the user to be interpreted server-side and changed to the
       more exact representation in the client browser.  This happens upon the input losing focus."""
    model_object = fixture.model_object
    class MyForm(Form):
        def __init__(self, view, name):
            super(MyForm, self).__init__(view, name)
            self.add_child(TextInput(self, model_object.fields.an_attribute, fuzzy=True))
            self.define_event_handler(model_object.events.an_event)
            self.add_child(ButtonInput(self, model_object.events.an_event))

    wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory('myform'), enable_js=True)
    fixture.reahl_server.set_app(wsgi_app)
    browser = fixture.driver_browser
    browser.open('/')

    browser.type(XPath.input_named('an_attribute'), '20 November 2012')
    browser.press_tab(XPath.input_named('an_attribute'))
    browser.wait_for(browser.is_element_value, XPath.input_named('an_attribute'), '20 Nov 2012')





