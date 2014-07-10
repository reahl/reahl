# Copyright 2011, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from __future__ import unicode_literals
from __future__ import print_function
from nose.tools import istest
from reahl.tofu import Fixture, test
from reahl.stubble import stubclass
from reahl.tofu import vassert

from reahl.component.modelinterface import Field, EmailField, PasswordField, BooleanField, IntegerField, \
                             ValidationConstraint, RequiredConstraint, MinLengthConstraint, \
                             MaxLengthConstraint, PatternConstraint, AllowedValuesConstraint, \
                             EqualToConstraint, RemoteConstraint, IntegerConstraint, \
                             MaxValueConstraint, MinValueConstraint, exposed
from reahl.web.ui import Input, Form, TextInput, Button
from reahl.webdev.tools import WidgetTester
from reahl.web_dev.fixtures import WebBasicsMixin
from reahl.web_dev.inputandvalidation.inputtests import InputMixin, InputMixin2


class FieldFixture(Fixture, InputMixin):
    pass

class ConstraintRenderingFixture(Fixture, WebBasicsMixin, InputMixin2):
    def new_field(self, name='an_attribute', label='the label'):
        field = super(ConstraintRenderingFixture, self).new_field(label=label)
        field.bind(name, self.model_object)
        return field

    def new_error_xpath(self):
        return '//form/label[@class="error"]'

    def is_error_text(self, text):
        return text == self.driver_browser.get_text(self.error_xpath)

    def new_input(self, field=None):
        the_input = Input(self.form, field or self.field)
        the_input.input_type = 'inputtype'
        return the_input


@istest
class FieldTests(object):
    @test(ConstraintRenderingFixture)
    def rendering_of_constraints(self, fixture):
        """The constraints of the Field of an Input are rendered in html as html attributes of an Input
           which corresponds with the name of each validation_constraint and has value the parameters of the validation_constraint.
           The error message of each validation_constraint is also put in a json object inside the class attribute.
           These measures make it possible to write constraints that are checked on the browser either by
           browser support or by a jquery validate add-on, and in case of failure to display the exact
           corresponding error message."""

        fixture.field.bind('an_attribute', fixture.model_object)
        fixture.model_object.an_attribute = 'field value'

        constraint1 = ValidationConstraint('validation_constraint 1 message')
        constraint1.name = 'one'
        @stubclass(ValidationConstraint)
        class ConstraintWithParams(ValidationConstraint):
            @property
            def parameters(self):
                return 'a parameter'
        constraint2 = ConstraintWithParams('validation_constraint 2 message with apostrophe\'s')
        constraint2.name = 'two'

        fixture.field.add_validation_constraint(constraint1)
        fixture.field.add_validation_constraint(constraint2)

        tester = WidgetTester(fixture.input)

        actual = tester.render_html()
        expected_html = '''<input name="an_attribute" data-one="" data-two="a parameter" form="test" type="inputtype" value="field value" class="{&quot;validate&quot;: {&quot;messages&quot;: {&quot;data-two&quot;: &quot;validation_constraint 2 message with apostrophe\\\\\'s&quot;, &quot;data-one&quot;: &quot;validation_constraint 1 message&quot;}}}">'''
        vassert( actual == expected_html )

    @test(ConstraintRenderingFixture)
    def remote_constraints(self, fixture):
        """Remote constraints are invoked by the browser via ajax on the server when the input loses focus."""

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
                self.add_child(Button(self, model_object.events.an_event))

        wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory('myform'), enable_js=True)
        fixture.reahl_server.set_app(wsgi_app)

        fixture.driver_browser.open('/')

        # Initially, there's no error
        fixture.driver_browser.wait_for_element_not_visible(fixture.error_xpath)

        # A failing string value causes an ajax call resulting in an error
        fixture.driver_browser.type('//input[@type="text"]', 'failing_string_value')
        fixture.driver_browser.press_tab('//input')
        fixture.driver_browser.wait_for_element_visible(fixture.error_xpath)
        error_text = fixture.driver_browser.get_text("//form/label[@class='error']")
        vassert( fixture.is_error_text('the label is invalid') )

        # A passing value causes an ajax call resulting in clearing of any previous errors
        fixture.driver_browser.type('//input[@type="text"]', 'passing value')
        fixture.driver_browser.press_tab('//input')
        fixture.driver_browser.wait_for_element_not_visible(fixture.error_xpath)

        # A failing python value causes an ajax call resulting in an error
        fixture.driver_browser.type('//input[@type="text"]', 'failing_parsed_value')
        fixture.driver_browser.press_tab('//input')
        fixture.driver_browser.wait_for_element_visible(fixture.error_xpath)
        error_text = fixture.driver_browser.get_text("//form/label[@class='error']")
        vassert( fixture.is_error_text('the label is invalid') )
        

@istest
class SpecificConstraintTests(object):
    @test(ConstraintRenderingFixture)
    def required_constraint_js(self, fixture):
        constraint = RequiredConstraint()
        class MyForm(Form):
            def __init__(self, view, name):
                super(MyForm, self).__init__(view, name)
                field = fixture.model_object.fields.an_attribute
                field.add_validation_constraint(constraint)
                self.add_child(TextInput(self, field))
        wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory('myform'), enable_js=True)
        fixture.reahl_server.set_app(wsgi_app)

        fixture.driver_browser.open('/')

        fixture.driver_browser.type('//input[@type="text"]', 'something')
        fixture.driver_browser.press_tab('//input')
        fixture.driver_browser.wait_for_element_not_visible(fixture.error_xpath)

        fixture.driver_browser.type('//input[@type="text"]', '')
        fixture.driver_browser.press_backspace('//input')  # To trigger validation on the field
        
        fixture.driver_browser.wait_for_element_visible(fixture.error_xpath)
        

    @test(ConstraintRenderingFixture)
    def min_length_constraint_js(self, fixture):
        min_required_length = 5
        constraint = MinLengthConstraint(min_length=min_required_length)
        class MyForm(Form):
            def __init__(self, view, name):
                super(MyForm, self).__init__(view, name)
                field = fixture.model_object.fields.an_attribute
                field.add_validation_constraint(constraint)
                self.add_child(TextInput(self, field))

        wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory('myform'), enable_js=True)
        fixture.reahl_server.set_app(wsgi_app)

        fixture.driver_browser.open('/')

        fixture.driver_browser.type('//input[@type="text"]', '1234')
        fixture.driver_browser.press_tab('//input')
        fixture.driver_browser.wait_for_element_visible(fixture.error_xpath)

    @test(ConstraintRenderingFixture)
    def max_length_constraint_js(self, fixture):
        max_allowed_length = 5
        constraint = MaxLengthConstraint(max_length=max_allowed_length)
        class MyForm(Form):
            def __init__(self, view, name):
                super(MyForm, self).__init__(view, name)
                field = fixture.model_object.fields.an_attribute
                field.add_validation_constraint(constraint)
                self.add_child(TextInput(self, field))

        wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory('myform'), enable_js=True)
        fixture.reahl_server.set_app(wsgi_app)

        fixture.driver_browser.open('/')

        fixture.driver_browser.type('//input[@type="text"]', '123456')
        accepted_value = fixture.driver_browser.get_value('//input[@type="text"]')
        vassert( accepted_value == '12345' )

    @test(ConstraintRenderingFixture)
    def pattern_constraint_js(self, fixture):
        allow_pattern = '(ab)+'
        constraint = PatternConstraint(pattern=allow_pattern)
        
        class MyForm(Form):
            def __init__(self, view, name):
                super(MyForm, self).__init__(view, name)
                field = fixture.model_object.fields.an_attribute
                field.add_validation_constraint(constraint)
                self.add_child(TextInput(self, field))

        wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory('myform'), enable_js=True)
        fixture.reahl_server.set_app(wsgi_app)

        fixture.driver_browser.open('/')

        fixture.driver_browser.type('//input[@type="text"]', 'aba')
        fixture.driver_browser.press_tab('//input')
        fixture.driver_browser.wait_for_element_visible(fixture.error_xpath)

        fixture.driver_browser.type('//input[@type="text"]', 'ababab')
        fixture.driver_browser.press_tab('//input')
        fixture.driver_browser.wait_for_element_not_visible(fixture.error_xpath)
        
    @test(ConstraintRenderingFixture)
    def allowed_values_constraint_js(self, fixture):
        allowed_values=['a','b']
        constraint = AllowedValuesConstraint(allowed_values=allowed_values)

        class MyForm(Form):
            def __init__(self, view, name):
                super(MyForm, self).__init__(view, name)
                field = fixture.model_object.fields.an_attribute
                field.add_validation_constraint(constraint)
                self.add_child(TextInput(self, field))

        wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory('myform'), enable_js=True)
        fixture.reahl_server.set_app(wsgi_app)
        fixture.driver_browser.open('/')

        fixture.driver_browser.type('//input[@type="text"]', 'ba')
        fixture.driver_browser.press_tab('//input')
        fixture.driver_browser.wait_for_element_visible(fixture.error_xpath)

    @test(ConstraintRenderingFixture)
    def equal_to_constraint_js(self, fixture):
        class ModelObject(object):
            @exposed
            def fields(self, fields):
                fields.an_attribute = Field(label='the label')
                fields.other = Field(label='other label')

        model_object = ModelObject()
        other_field = model_object.fields.other
        constraint = EqualToConstraint(other_field, '$label, $other_label')

        class MyForm(Form):
            def __init__(self, view, name):
                super(MyForm, self).__init__(view, name)
                field = model_object.fields.an_attribute
                field.add_validation_constraint(constraint)
                other_input = self.add_child(TextInput(self, model_object.fields.other))
                other_input.set_id('other')
                one_input = self.add_child(TextInput(self, field))
                one_input.set_id('one')

        wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory('myform'), enable_js=True)
        fixture.reahl_server.set_app(wsgi_app)

        fixture.driver_browser.open('/')

        fixture.driver_browser.type('//input[@id="one"]', 'something else')
        fixture.driver_browser.type('//input[@id="other"]', 'something')
        fixture.driver_browser.press_tab('//input[@id="one"]')
        fixture.driver_browser.wait_for_element_visible(fixture.error_xpath)
        vassert( fixture.is_error_text('the label, other label') )

        fixture.driver_browser.type('//input[@id="one"]', 'something')
        fixture.driver_browser.press_tab('//input[@id="one"]')
        fixture.driver_browser.wait_for_element_not_visible(fixture.error_xpath)

