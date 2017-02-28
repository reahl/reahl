# Copyright 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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

import six

from reahl.tofu import vassert, scenario, test

from reahl.webdev.tools import XPath, Browser
from reahl.webdev.tools import WidgetTester
from reahl.web_dev.fixtures import WebFixture
from reahl.component.modelinterface import exposed, Field, BooleanField, Event, Choice, ChoiceField
from reahl.web.fw import Url
from reahl.web.bootstrap.ui import A, Div
from reahl.web.bootstrap.forms import Button, FormLayout, InlineFormLayout, GridFormLayout, Form, ChoicesLayout,\
                                   TextInput, CheckboxInput, PrimitiveCheckboxInput, RadioButtonInput, ButtonLayout
from reahl.web.bootstrap.grid import ResponsiveSize




class FormLayoutScenarios(WebFixture):
    def new_widget(self):
        return Div(self.view).use_layout(self.layout)

    @scenario
    def basic_form(self):
        self.layout = FormLayout()
        self.expected_html = '<div></div>'

    @scenario
    def inline_form(self):
        self.layout = InlineFormLayout()
        self.expected_html = '<div class="form-inline"></div>'

    @scenario
    def grid_form(self):
        self.layout = GridFormLayout(ResponsiveSize(xl=4), ResponsiveSize(xl=8))
        self.expected_html = '<div></div>'


@test(FormLayoutScenarios)
def basic_form_layouts(fixture):
    """There are three basic layouts of forms in bootstrap."""
    tester = WidgetTester(fixture.widget)
    actual = tester.render_html()
    vassert( actual == fixture.expected_html )


class FormLayoutFixture(WebFixture):
    form_group_xpath = '//form/div[contains(@class, "form-group")]'
    def new_domain_object(self):
        class StubDomainObject(object):
            @exposed
            def fields(self, fields):
                fields.an_attribute = Field(label='Some input', required=True)
        return StubDomainObject()
    
    def form_contains_form_group(self, browser):
        return browser.get_xpath_count(self.form_group_xpath) == 1

    def get_form_group_children(self, browser, index=0):
        return browser.xpath( '%s[%s]/*' % (self.form_group_xpath, index+1) )

    def get_form_group(self, browser, index=0):
        form_groups = browser.xpath('%s[%s]' % (self.form_group_xpath, index+1))
        return form_groups[index]

    def get_form_group_highlight_marks(self, browser, index=0):
        form_group = self.get_form_group(browser, index=index)
        return [mark for mark in form_group.attrib['class'].split(' ')
                     if mark.startswith('has-')]
        
    def get_form_group_errors(self, browser, index=0):
        def is_error_element(element):
            return 'class' in element.attrib \
                   and 'text-help' in element.attrib['class'] \
                   and 'has-danger' in element.attrib['class'] 
        def is_visible(element):
            return not (('style' in element.attrib) and ('display: none' in element.attrib['style']))
            
        return [element for element in self.get_form_group_children(browser, index=index)
                        if is_error_element(element) and is_visible(element) ]


@test(FormLayoutFixture)
def adding_basic_input(fixture):
    """Adding an input to a FormLayout, adds it in a bootstrap form-group with Some input."""
    
    class FormWithInputAddedUsingDefaults(Form):
        def __init__(self, view):
            super(FormWithInputAddedUsingDefaults, self).__init__(view, 'aform')
            self.use_layout(FormLayout())
            self.layout.add_input(TextInput(self, fixture.domain_object.fields.an_attribute))

    browser = Browser(fixture.new_wsgi_app(child_factory=FormWithInputAddedUsingDefaults.factory()))
    browser.open('/')

    vassert( fixture.form_contains_form_group(browser) )
    
    [label, input_widget] = fixture.get_form_group_children(browser)
    
    # form-group has a label, correctly set up for bootstrap
    vassert( label.tag == 'label' )
    vassert( label.attrib['for'] == input_widget.attrib['id'] )
    vassert( label.text == 'Some input' )
    
    # form-group has an input, correctly set up for bootstrap
    vassert( input_widget.tag == 'input' )
    vassert( input_widget.attrib['name'] == 'an_attribute' )


@test(FormLayoutFixture)
def grid_form_layouts(fixture):
    """A GridFormLayout adds the Label and Input of each added input in separate columns sized like you specify"""
    class FormWithGridFormLayout(Form):
        def __init__(self, view):
            super(FormWithGridFormLayout, self).__init__(view, 'aform')
            self.use_layout(GridFormLayout(ResponsiveSize(lg=4), ResponsiveSize(lg=8)))
            self.layout.add_input(TextInput(self, fixture.domain_object.fields.an_attribute))

    browser = Browser(fixture.new_wsgi_app(child_factory=FormWithGridFormLayout.factory()))
    browser.open('/')

    [label_column, input_column] = fixture.get_form_group_children(browser)
    vassert( label_column.tag == 'div' )
    vassert( 'col-lg-4' in label_column.attrib['class'] )
    vassert( 'column-label' in label_column.attrib['class'] )

    vassert( input_column.tag == 'div' )
    vassert( 'col-lg-8' in input_column.attrib['class'] )
    vassert( 'column-input' in input_column.attrib['class'] )


@test(FormLayoutFixture)
def specifying_help_text(fixture):
    """You can optionally specify help_text when adding an input."""
    
    class FormWithInputAndHelp(Form):
        def __init__(self, view):
            super(FormWithInputAndHelp, self).__init__(view, 'aform')
            self.use_layout(FormLayout())
            self.layout.add_input(TextInput(self, fixture.domain_object.fields.an_attribute), help_text='some help')

    browser = Browser(fixture.new_wsgi_app(child_factory=FormWithInputAndHelp.factory()))
    browser.open('/')

    [label, input_widget, help_text] = fixture.get_form_group_children(browser)

    # form-group has help-text    
    vassert( help_text.tag == 'p' )
    vassert( 'text-muted' in help_text.attrib['class'] )
    vassert( help_text.text == 'some help' )
    

@test(FormLayoutFixture)
def omitting_label(fixture):
    """The label will be rendered hidden (but available to screen readers) if this is explicity requested."""
    class FormWithInputNoLabel(Form):
        def __init__(self, view):
            super(FormWithInputNoLabel, self).__init__(view, 'aform')
            self.use_layout(FormLayout())
            self.layout.add_input(TextInput(self, fixture.domain_object.fields.an_attribute), hide_label=True)

    browser = Browser(fixture.new_wsgi_app(child_factory=FormWithInputNoLabel.factory()))
    browser.open('/')

    [label, help_text] = fixture.get_form_group_children(browser)
    vassert( label.tag == 'label' )
    vassert( label.attrib['class'] == 'sr-only' )
    

@test(FormLayoutFixture)
def adding_checkboxes(fixture):
    """CheckboxInputs are added non-inlined, and by default without labels."""

    class DomainObjectWithBoolean(object):
        @exposed
        def fields(self, fields):
            fields.an_attribute = BooleanField(label='Some input', required=True)

    fixture.domain_object = DomainObjectWithBoolean()
    
    class FormWithInputWithCheckbox(Form):
        def __init__(self, view):
            super(FormWithInputWithCheckbox, self).__init__(view, 'aform')
            self.use_layout(FormLayout())
            self.layout.add_input(CheckboxInput(self, fixture.domain_object.fields.an_attribute))

    browser = Browser(fixture.new_wsgi_app(child_factory=FormWithInputWithCheckbox.factory()))
    browser.open('/')

    vassert( not any(child.tag == 'label' for child in fixture.get_form_group_children(browser)) )
    [div] = fixture.get_form_group_children(browser)
    [checkbox] = div.getchildren()
    vassert( checkbox.attrib['class'] == 'form-check' )
    

class ValidationScenarios(FormLayoutFixture):
    def new_domain_object(self):
        class ModelObject(object):
            @exposed
            def fields(self, fields):
                fields.an_attribute = Field(label='Some input', required=True)
                fields.another_attribute = Field(label='Another input', required=True)
            @exposed
            def events(self, events):
                events.submit = Event(label='Submit')
        return ModelObject()

    def new_Form(self):
        fixture = self
        class FormWithInput(Form):
            def __init__(self, view):
                super(FormWithInput, self).__init__(view, 'aform')
                self.set_attribute('novalidate','novalidate')
                self.use_layout(FormLayout())
                self.layout.add_input(TextInput(self, fixture.domain_object.fields.an_attribute))
                self.layout.add_input(TextInput(self, fixture.domain_object.fields.another_attribute))
                self.define_event_handler(fixture.domain_object.events.submit)
                self.add_child(Button(self, fixture.domain_object.events.submit))
        return FormWithInput

    @scenario
    def with_javascript(self):
        self.reahl_server.set_app(self.new_wsgi_app(child_factory=self.Form.factory(), enable_js=True))
        self.browser = self.driver_browser

    @scenario
    def without_javascript(self):
        self.browser = Browser(super(ValidationScenarios, self).new_wsgi_app(child_factory=self.Form.factory()))


@test(ValidationScenarios)
def input_validation_cues(fixture):
    """Visible cues are inserted to indicate the current validation state
       and possible validation error messages to a user. """

    browser = fixture.browser
    browser.open('/')

    vassert( not fixture.get_form_group_highlight_marks(browser, index=0) )
    vassert( not fixture.get_form_group_errors(browser, index=0) )

    browser.type(XPath.input_labelled('Some input'), '')
    browser.click(XPath.button_labelled('Submit'))

    vassert( ['has-danger'] == fixture.get_form_group_highlight_marks(browser, index=0) )
    [error] = fixture.get_form_group_errors(browser, index=0)
    vassert( error.text == 'Some input is required' )

    browser.type(XPath.input_labelled('Some input'), 'valid value')
    browser.click(XPath.button_labelled('Submit'))

    vassert( ['has-success'] == fixture.get_form_group_highlight_marks(browser, index=0) )
    vassert( not fixture.get_form_group_errors(browser, index=0) )

    browser.type(XPath.input_labelled('Another input'), 'valid value')
    browser.click(XPath.button_labelled('Submit'))

    vassert( not fixture.get_form_group_highlight_marks(browser, index=0) )
    vassert( not fixture.get_form_group_errors(browser, index=0) )

@test(ValidationScenarios.with_javascript)
def input_validation_cues_javascript_interaction(fixture):
    """The visual cues rendered server-side can subsequently be manipulated via javascript."""
    fixture.reahl_server.set_app(fixture.new_wsgi_app(child_factory=fixture.Form.factory(), enable_js=False))

    browser = fixture.browser
    browser.open('/')
    browser.type(XPath.input_labelled('Some input'), '')
    browser.click(XPath.button_labelled('Submit'))

    vassert( ['has-danger'] == fixture.get_form_group_highlight_marks(browser, index=0) )
    [error] = fixture.get_form_group_errors(browser, index=0)
    vassert( error.text == 'Some input is required' )

    fixture.reahl_server.set_app(fixture.new_wsgi_app(child_factory=fixture.Form.factory(), enable_js=True))
    browser.open('/')

    browser.click(XPath.button_labelled('Submit'))

    vassert( ['has-danger'] == fixture.get_form_group_highlight_marks(browser, index=0) )
    [error] = fixture.get_form_group_errors(browser, index=0)
    vassert( error.text == 'Some input is required' )

    browser.type(XPath.input_labelled('Some input'), 'valid value')
    browser.press_tab(XPath.input_labelled('Some input'))

    def form_group_is_marked_success(index):
        return ['has-success'] == fixture.get_form_group_highlight_marks(browser, index=index)
    vassert( fixture.driver_browser.wait_for(form_group_is_marked_success, 0) )
    vassert( not fixture.get_form_group_errors(browser, index=0) )


class DisabledScenarios(WebFixture):
    @scenario
    def disabled_input(self):
        self.field = Field(writable=lambda field: False)
        self.expects_disabled_class = True

    @scenario
    def enabled_input(self):
        self.field = Field(writable=lambda field: True)
        self.expects_disabled_class = False


@test(DisabledScenarios)
def disabled_state(fixture):
    """Visible cues are inserted to indicate that inputs are disabled. """
    form = Form(fixture.view, 'test').use_layout(FormLayout())
    field = fixture.field
    field.bind('field', fixture)

    form.layout.add_input(TextInput(form, field))
    
    tester = WidgetTester(form)
    
    [form_group] = tester.xpath(FormLayoutFixture.form_group_xpath)
    if fixture.expects_disabled_class:
        vassert( 'disabled ' in form_group.attrib['class'] )
    else:
        vassert( 'disabled' not in form_group.attrib['class'] )



class ChoicesLayoutFixture(WebFixture):
    def new_form(self):
        return Form(self.view, 'test')

    def new_field(self):
        field = BooleanField()
        field.bind('field', self)
        return field

    def input_is_wrapped_in_label(self, tester):
        return len(tester.xpath('//label/input')) > 0

    def main_element(self, tester):
        return tester.xpath('//div/*')[0]
        

@test(ChoicesLayoutFixture)
def choices_layout(fixture):
    """A ChoicesLayout can be used to add a PrimitiveCheckboxInput inlined or stacked."""
    stacked_container = Div(fixture.view).use_layout(ChoicesLayout())
    stacked_container.layout.add_choice(PrimitiveCheckboxInput(fixture.form, fixture.field))

    tester = WidgetTester(stacked_container)
    vassert( fixture.input_is_wrapped_in_label(tester) )
    vassert( fixture.main_element(tester).tag == 'div' )
    vassert( fixture.main_element(tester).attrib['class'] == 'form-check' )

    inlined_container = Div(fixture.view).use_layout(ChoicesLayout(inline=True))
    inlined_container.layout.add_choice(PrimitiveCheckboxInput(fixture.form, fixture.field))

    tester = WidgetTester(inlined_container)
    vassert( fixture.input_is_wrapped_in_label(tester) )
    vassert( fixture.main_element(tester).tag == 'div' )
    vassert( fixture.main_element(tester).attrib['class'] == 'form-check form-check-inline' )


class RadioButtonFixture(ChoicesLayoutFixture):
    def new_field(self):
        choices = [Choice(1, Field(label='One')),
                   Choice(2, Field(label='Two'))
                  ]
        field = ChoiceField(choices)
        field.bind('field', self)
        return field


@test(RadioButtonFixture)
def layout_of_radio_button_input(fixture):
    """The PrimitiveRadioButtonInputs inside a RadioButtonInput are also laid out using a ChoicesLayout."""
    stacked_radio = RadioButtonInput(fixture.form, fixture.field)

    tester = WidgetTester(stacked_radio)
    vassert( fixture.input_is_wrapped_in_label(tester) )
    vassert( fixture.main_element(tester).tag == 'div' )
    vassert( fixture.main_element(tester).attrib['class'] == 'form-check' )

    inlined_radio = RadioButtonInput(fixture.form, fixture.field, button_layout=ChoicesLayout(inline=True))

    tester = WidgetTester(inlined_radio)
    vassert( fixture.input_is_wrapped_in_label(tester) )
    vassert( fixture.main_element(tester).tag == 'div' )
    vassert( fixture.main_element(tester).attrib['class'] == 'form-check form-check-inline' )



@test(WebFixture)
def button_layouts(fixture):
    """A ButtonLayout can be be used on a Button to customise various visual effects."""

    event = Event(label='click me')
    event.bind('event', fixture)
    form = Form(fixture.view, 'test')
    form.define_event_handler(event)

    # Case: the defaults
    button = Button(form, event).use_layout(ButtonLayout())
    
    tester = WidgetTester(button)
    [button] = tester.xpath(XPath.button_labelled('click me'))
    vassert( button.attrib['class'] == 'btn' )

    # Case: possible effects
    button = Button(form, event).use_layout(ButtonLayout(style='default', size='sm', active=True, wide=True))
    
    tester = WidgetTester(button)
    [button] = tester.xpath(XPath.button_labelled('click me'))
    vassert( button.attrib['class'] == 'active btn btn-block btn-default btn-sm' )


@test(WebFixture)
def button_layouts_on_anchors(fixture):
    """A ButtonLayout can also be used to make an A (anchor) look like a button."""

    anchor = A(fixture.view, href=Url('/an/href'), description='link text').use_layout(ButtonLayout())
    tester = WidgetTester(anchor)
    [rendered_anchor] = tester.xpath(XPath.link_with_text('link text'))
    vassert( rendered_anchor.attrib['class'] == 'btn' )


@test(WebFixture)
def button_layouts_on_disabled_anchors(fixture):
    """Disabled A's are marked with a class so Bootstap can style them appropriately."""
    def can_write():
        return False
    anchor = A(fixture.view, href=Url('/an/href'), description='link text', write_check=can_write).use_layout(ButtonLayout())
    tester = WidgetTester(anchor)
    [rendered_anchor] = tester.xpath(XPath.link_with_text('link text'))
    vassert( rendered_anchor.attrib['class'] == 'btn disabled' )






