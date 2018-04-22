# Copyright 2013-2018 Reahl Software Services (Pty) Ltd. All rights reserved.
# -*- encoding: utf-8 -*-
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

from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import stubclass

from reahl.component.modelinterface import Field, ValidationConstraint, RequiredConstraint, MinLengthConstraint, \
                             MaxLengthConstraint, PatternConstraint, AllowedValuesConstraint, \
                             EqualToConstraint, RemoteConstraint, exposed
from reahl.web.ui import PrimitiveInput, HTMLInputElement, Form, TextInput, ButtonInput
from reahl.webdev.tools import WidgetTester

from reahl.web_dev.inputandvalidation.test_input import SimpleInputFixture2
from reahl.web_dev.fixtures import WebFixture


class ConstraintRenderingFixture(SimpleInputFixture2):
    def new_field(self, name='an_attribute', label='an attribute'):
        field = super(ConstraintRenderingFixture, self).new_field(label=label)
        field.bind(name, self.model_object)
        return field

    def new_error_xpath(self):
        return '//form/label[@class="error"]'

    def is_error_text(self, text):
        return text == self.web_fixture.driver_browser.get_text(self.error_xpath)

    def new_input(self, field=None):
        @stubclass(PrimitiveInput)
        class InputStub(PrimitiveInput):
            def create_html_widget(self):
                return HTMLInputElement(self, 'inputtype')

        return InputStub(self.form, field or self.field)


@with_fixtures(WebFixture, ConstraintRenderingFixture)
def test_rendering_of_constraints(web_fixture, constraint_rendering_fixture):
    """The constraints of the Field of an PrimitiveInput are rendered in html as html attributes of an Input
       which corresponds with the name of each validation_constraint and has value the parameters of the validation_constraint.
       The error message of each validation_constraint is also put in a json object inside the class attribute.
       These measures make it possible to write constraints that are checked on the browser either by
       browser support or by a jquery validate add-on, and in case of failure to display the exact
       corresponding error message."""

    fixture = constraint_rendering_fixture

    fixture.field.bind('an_attribute', fixture.model_object)
    fixture.model_object.an_attribute = 'field value'

    constraint1 = ValidationConstraint('validation_constraint 1 message')
    constraint1.name = 'one'
    @stubclass(ValidationConstraint)
    class ConstraintWithParams(ValidationConstraint):
        @property
        def parameters(self):
            return 'a parameter'

    constraint2 = ConstraintWithParams('validation_constraint 2 message with apostrophe\'s and quotes"')
    constraint2.name = 'two'

    fixture.field.add_validation_constraint(constraint1)
    fixture.field.add_validation_constraint(constraint2)

    tester = WidgetTester(fixture.input)

    actual = tester.render_html()
    expected_html = '''<input name="an_attribute" data-msg-one="validation_constraint 1 message" data-msg-two="validation_constraint 2 message with apostrophe&#x27;s and quotes&quot;" data-rule-one="true" data-rule-two="a parameter" form="test" type="inputtype" value="field value">'''
    assert actual == expected_html


@with_fixtures(WebFixture, ConstraintRenderingFixture)
def test_remote_constraints(web_fixture, constraint_rendering_fixture):
    """Remote constraints are invoked by the browser via ajax on the server when the input loses focus."""

    fixture = constraint_rendering_fixture

    class MyRemoteConstraint(RemoteConstraint):
        def validate_input(self, unparsed_input):
            if unparsed_input == 'failing_string_value':
                raise self

        def validate_parsed_value(self, parsed_value):
            if parsed_value == 'failing_parsed_value':
                raise self

    model_object = fixture.model_object
    model_object.fields.an_attribute.add_validation_constraint(MyRemoteConstraint(error_message='$label is invalid'))

    class MyForm(Form):
        def __init__(self, view, name):
            super(MyForm, self).__init__(view, name)
            field = model_object.fields.an_attribute
            self.add_child(TextInput(self, model_object.fields.an_attribute))
            self.define_event_handler(model_object.events.an_event)
            self.add_child(ButtonInput(self, model_object.events.an_event))

    wsgi_app = web_fixture.new_wsgi_app(child_factory=MyForm.factory('myform'), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)

    web_fixture.driver_browser.open('/')

    # Initially, there's no error
    web_fixture.driver_browser.wait_for_element_not_visible(fixture.error_xpath)

    # A failing string value causes an ajax call resulting in an error
    web_fixture.driver_browser.type('//input[@type="text"]', 'failing_string_value')
    web_fixture.driver_browser.press_tab()
    web_fixture.driver_browser.wait_for_element_visible(fixture.error_xpath)
    assert fixture.is_error_text('an attribute is invalid')

    # A passing value causes an ajax call resulting in clearing of any previous errors
    web_fixture.driver_browser.type('//input[@type="text"]', 'passing value')

    web_fixture.driver_browser.press_tab()
    web_fixture.driver_browser.wait_for_element_not_visible(fixture.error_xpath)

    # A failing python value causes an ajax call resulting in an error
    web_fixture.driver_browser.type('//input[@type="text"]', 'failing_parsed_value')
    web_fixture.driver_browser.press_tab()
    web_fixture.driver_browser.wait_for_element_visible(fixture.error_xpath)
    assert fixture.is_error_text('an attribute is invalid')


@with_fixtures(WebFixture, ConstraintRenderingFixture)
def test_required_constraint_js(web_fixture, constraint_rendering_fixture):
    fixture = constraint_rendering_fixture

    constraint = RequiredConstraint()

    class MyForm(Form):
        def __init__(self, view, name):
            super(MyForm, self).__init__(view, name)
            field = fixture.model_object.fields.an_attribute.with_validation_constraint(constraint)
            self.add_child(TextInput(self, field))
    wsgi_app = web_fixture.new_wsgi_app(child_factory=MyForm.factory('myform'), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)

    web_fixture.driver_browser.open('/')

    web_fixture.driver_browser.type('//input[@type="text"]', 'something')
    web_fixture.driver_browser.press_tab()
    web_fixture.driver_browser.wait_for_element_not_visible(fixture.error_xpath)

    web_fixture.driver_browser.type('//input[@type="text"]', '')
    web_fixture.driver_browser.press_backspace('//input')  # To trigger validation on the field

    web_fixture.driver_browser.wait_for_element_visible(fixture.error_xpath)


@with_fixtures(WebFixture, ConstraintRenderingFixture)
def test_min_length_constraint_js(web_fixture, constraint_rendering_fixture):
    fixture = constraint_rendering_fixture

    min_required_length = 5
    constraint = MinLengthConstraint(min_length=min_required_length)
    class MyForm(Form):
        def __init__(self, view, name):
            super(MyForm, self).__init__(view, name)
            field = fixture.model_object.fields.an_attribute.with_validation_constraint(constraint)
            self.add_child(TextInput(self, field))

    wsgi_app = web_fixture.new_wsgi_app(child_factory=MyForm.factory('myform'), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)

    web_fixture.driver_browser.open('/')

    web_fixture.driver_browser.type('//input[@type="text"]', '1234')
    web_fixture.driver_browser.press_tab()
    web_fixture.driver_browser.wait_for_element_visible(fixture.error_xpath)


@with_fixtures(WebFixture, ConstraintRenderingFixture)
def test_max_length_constraint_js(web_fixture, constraint_rendering_fixture):
    fixture = constraint_rendering_fixture

    max_allowed_length = 5
    constraint = MaxLengthConstraint(max_length=max_allowed_length)
    class MyForm(Form):
        def __init__(self, view, name):
            super(MyForm, self).__init__(view, name)
            field = fixture.model_object.fields.an_attribute.with_validation_constraint(constraint)
            self.add_child(TextInput(self, field))

    wsgi_app = web_fixture.new_wsgi_app(child_factory=MyForm.factory('myform'), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)

    web_fixture.driver_browser.open('/')

    web_fixture.driver_browser.type('//input[@type="text"]', '123456')
    accepted_value = web_fixture.driver_browser.get_value('//input[@type="text"]')
    assert accepted_value == '12345'


@with_fixtures(WebFixture, ConstraintRenderingFixture)
def test_pattern_constraint_js(web_fixture, constraint_rendering_fixture):
    fixture = constraint_rendering_fixture

    allow_pattern = '(ab)+'
    constraint = PatternConstraint(pattern=allow_pattern)

    class MyForm(Form):
        def __init__(self, view, name):
            super(MyForm, self).__init__(view, name)
            field = fixture.model_object.fields.an_attribute.with_validation_constraint(constraint)
            self.add_child(TextInput(self, field))

    wsgi_app = web_fixture.new_wsgi_app(child_factory=MyForm.factory('myform'), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)

    web_fixture.driver_browser.open('/')

    web_fixture.driver_browser.type('//input[@type="text"]', 'aba')
    web_fixture.driver_browser.press_tab()
    web_fixture.driver_browser.wait_for_element_visible(fixture.error_xpath)

    web_fixture.driver_browser.type('//input[@type="text"]', 'ababab')
    web_fixture.driver_browser.press_tab()
    web_fixture.driver_browser.wait_for_element_not_visible(fixture.error_xpath)


@with_fixtures(WebFixture, ConstraintRenderingFixture)
def test_allowed_values_constraint_js(web_fixture, constraint_rendering_fixture):
    fixture = constraint_rendering_fixture

    allowed_values=['a','b']
    constraint = AllowedValuesConstraint(allowed_values=allowed_values)

    class MyForm(Form):
        def __init__(self, view, name):
            super(MyForm, self).__init__(view, name)
            field = fixture.model_object.fields.an_attribute.with_validation_constraint(constraint)
            self.add_child(TextInput(self, field))

    wsgi_app = web_fixture.new_wsgi_app(child_factory=MyForm.factory('myform'), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)
    web_fixture.driver_browser.open('/')

    web_fixture.driver_browser.type('//input[@type="text"]', 'ba')
    web_fixture.driver_browser.press_tab()
    web_fixture.driver_browser.wait_for_element_visible(fixture.error_xpath)


@with_fixtures(WebFixture, ConstraintRenderingFixture)
def test_equal_to_constraint_js(web_fixture, constraint_rendering_fixture):
    fixture = constraint_rendering_fixture

    class ModelObject(object):
        @exposed
        def fields(self, fields):
            fields.an_attribute = Field(label='an attribute')
            fields.other = Field(label='other attribute')

    model_object = ModelObject()
    other_field = model_object.fields.other
    constraint = EqualToConstraint(other_field, '$label, $other_label')

    class MyForm(Form):
        def __init__(self, view, name):
            super(MyForm, self).__init__(view, name)
            field = fixture.model_object.fields.an_attribute.with_validation_constraint(constraint)
            other_input = self.add_child(TextInput(self, model_object.fields.other))
            other_input.set_id('other')
            one_input = self.add_child(TextInput(self, field))
            one_input.set_id('one')

    wsgi_app = web_fixture.new_wsgi_app(child_factory=MyForm.factory('myform'), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)

    web_fixture.driver_browser.open('/')

    web_fixture.driver_browser.type('//input[@id="other"]', 'something')
    web_fixture.driver_browser.type('//input[@id="one"]', 'something else')
    web_fixture.driver_browser.press_tab()
    web_fixture.driver_browser.wait_for_element_visible(fixture.error_xpath)
    assert fixture.is_error_text('an attribute, other attribute')

    web_fixture.driver_browser.type('//input[@id="one"]', 'something')
    web_fixture.driver_browser.press_tab()
    web_fixture.driver_browser.wait_for_element_not_visible(fixture.error_xpath)
