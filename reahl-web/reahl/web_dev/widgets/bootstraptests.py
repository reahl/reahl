# Copyright 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.tofu import vassert, scenario, expected, test

from reahl.webdev.tools import XPath, Browser

from reahl.webdev.tools import WidgetTester
from reahl.web_dev.fixtures import WebFixture

from reahl.web.fw import UserInterface, Url
from reahl.web.ui import A, Div, P, HTML5Page, Header, Footer

from reahl.web_dev.inputandvalidation.inputtests import InputMixin

from reahl.component.exceptions import ProgrammerError, IsInstance
from reahl.component.modelinterface import exposed, Field, BooleanField, Event, Choice, ChoiceField
from reahl.web.bootstrap import ColumnLayout, ChoicesLayout, ResponsiveSize, InputGroup, Button, FormLayout, Form, TextInput, CheckboxInput, RadioButtonInput, Container, ButtonLayout


@test(WebFixture)
def containers(fixture):
    """There are two types of Bootstrap containers:  a full width container, and a responsive (fluid) container."""

    widget = Div(fixture.view).use_layout(Container())
    tester = WidgetTester(widget)
    
    css_class = tester.xpath('//div')[0].attrib['class']
    vassert( 'container' == css_class )

    widget = Div(fixture.view).use_layout(Container(fluid=True))
    tester = WidgetTester(widget)
    
    css_class = tester.xpath('//div')[0].attrib['class']
    vassert( 'container-fluid' == css_class )


@test(WebFixture)
def column_layout_basics(fixture):
    """The bootstrap.ColumnLayout adds the correct classes for Bootstrap to lay out its Widget as a row with columns."""

    layout = ColumnLayout(('column_a', ResponsiveSize(lg=4)), ('column_b', ResponsiveSize(lg=8)))
    widget = Div(fixture.view)
    
    vassert( not widget.has_attribute('class') )
    
    widget.use_layout(layout)

    vassert( widget.get_attribute('class') == 'row' )
    column_a, column_b = widget.children

    vassert( 'col-lg-4' in column_a.get_attribute('class')  )
    vassert( 'col-lg-8' in column_b.get_attribute('class')  )


@test(WebFixture)
def column_layout_sizes(fixture):
    """It is mandatory to specify sizes for all columns."""

    with expected(ProgrammerError):
        ColumnLayout('column_a')


@test(WebFixture)
def adding_columns(fixture):
    """You can add additional columns after construction."""

    widget = Div(fixture.view).use_layout(ColumnLayout())

    vassert( not widget.children )

    widget.layout.add_column(ResponsiveSize(lg=4))

    [added_column] = widget.children
    vassert( added_column.get_attribute('class') == 'col-lg-4' )


@test(WebFixture)
def allowed_sizes(fixture):
    """The device classes for which sizes can be specified."""
    size = ResponsiveSize(xs=1, sm=2, md=3, lg=4)

    vassert( size == {'xs':1, 'sm':2, 'md':3, 'lg':4} )


@test(WebFixture)
def column_offsets(fixture):
    """You can optionally specify space to leave empty (an offset) before a column at specific device sizes."""

    layout = ColumnLayout(('column_a', ResponsiveSize(lg=6).offset(xs=2, sm=4, md=6, lg=3)))
    widget = Div(fixture.view).use_layout(layout)

    [column_a] = layout.columns.values()

    vassert( 'col-lg-6' in column_a.get_attribute('class')  )
    vassert( 'col-lg-offset-3' in column_a.get_attribute('class')  )
    vassert( 'col-xs-offset-2' in column_a.get_attribute('class')  )
    vassert( 'col-sm-offset-4' in column_a.get_attribute('class')  )
    vassert( 'col-md-offset-6' in column_a.get_attribute('class')  )


@test(WebFixture)
def column_clearfix(fixture):
    """If a logical row spans more than one visual row for a device size, bootstrap clearfixes are
       automatically inserted to ensure cells in resultant visual rows are neatly arranged.
    """

    # Case: Adding a correct clearfix in the right place
    wrapping_layout = ColumnLayout(('column_a', ResponsiveSize(xs=8).offset(xs=2)),
                                   ('column_b', ResponsiveSize(xs=2).offset(xs=2))
    )
    widget = Div(fixture.view).use_layout(wrapping_layout)

    [column_a, clearfix, column_b] = widget.children           
    vassert( [column_a, column_b] == [i for i in wrapping_layout.columns.values()] )
    vassert( 'clearfix' in clearfix.get_attribute('class')  )
    vassert( 'visible-xs-block' in clearfix.get_attribute('class')  )

    # Case: When clearfix needs to take "implicit" sizes of smaller device classes into account
    wrapping_layout = ColumnLayout(('column_a', ResponsiveSize(xs=8).offset(xs=2)),
                                   ('column_b', ResponsiveSize(lg=2).offset(lg=2))
    )
    widget = Div(fixture.view).use_layout(wrapping_layout)

    [column_a, clearfix, column_b] = widget.children           
    vassert( [column_a, column_b] == [i for i in wrapping_layout.columns.values()] )
    vassert( 'clearfix' in clearfix.get_attribute('class')  )
    vassert( 'visible-lg-block' in clearfix.get_attribute('class')  )

    # Case: When no clearfix must be added
    non_wrapping_layout = ColumnLayout(('column_a', ResponsiveSize(xs=2).offset(xs=2)),
                                       ('column_b', ResponsiveSize(xs=2))
    )
    widget = Div(fixture.view).use_layout(non_wrapping_layout)

    [column_a, column_b] = widget.children
    vassert( [column_a, column_b] == [i for i in non_wrapping_layout.columns.values()] )  



class FormLayoutScenarios(WebFixture):
    def new_widget(self):
        return Div(self.view).use_layout(self.layout)

    @scenario
    def basic_form(self):
        self.layout = FormLayout()
        self.expected_html = '<div></div>'

    @scenario
    def inline_form(self):
        self.layout = FormLayout(inline=True)
        self.expected_html = '<div class="form-inline"></div>'

    @scenario
    def horizontal_form(self):
        self.layout = FormLayout(horizontal=True)
        self.expected_html = '<div class="form-horizontal"></div>'


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

    def get_form_group_highlight_marks(self, browser, index=0):
        form_groups = browser.xpath('%s[%s]' % (self.form_group_xpath, index+1))
        form_group = form_groups[index]
        return [mark for mark in form_group.attrib['class'].split(' ')
                     if mark.startswith('has-')]
        
    def get_form_group_errors(self, browser, index=0):
        def is_error_element(element):
            return 'help-block' in element.attrib['class'] and 'has-error' in element.attrib['class'] 
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
    
    # form-group has Some input, correctly set up for bootstrap
    vassert( label.tag == 'label' )
    vassert( label.attrib['for'] == 'an_attribute' )
    vassert( 'control-label' in label.attrib['class'] )
    vassert( label.text == 'Some input' )
    
    # form-group has an input, correctly set up for bootstrap
    vassert( input_widget.tag == 'input' )
    vassert( input_widget.attrib['name'] == 'an_attribute' )


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
    vassert( 'help-block' in help_text.attrib['class'] )
    vassert( help_text.text == 'some help' )
    

@test(FormLayoutFixture)
def omitting_label(fixture):
    """The label will be omitted if this is explicity requested."""
    class FormWithInputNoLabel(Form):
        def __init__(self, view):
            super(FormWithInputNoLabel, self).__init__(view, 'aform')
            self.use_layout(FormLayout())
            self.layout.add_input(TextInput(self, fixture.domain_object.fields.an_attribute), render_label=False)

    browser = Browser(fixture.new_wsgi_app(child_factory=FormWithInputNoLabel.factory()))
    browser.open('/')

    vassert( not any(child.tag == 'label' for child in fixture.get_form_group_children(browser)) )
    

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
    [checkbox] = fixture.get_form_group_children(browser)
    vassert( checkbox.attrib['class'] == 'checkbox' )
    

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

    vassert( ['has-error'] == fixture.get_form_group_highlight_marks(browser, index=0) )
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

    vassert( ['has-error'] == fixture.get_form_group_highlight_marks(browser, index=0) )
    [error] = fixture.get_form_group_errors(browser, index=0)
    vassert( error.text == 'Some input is required' )

    fixture.reahl_server.set_app(fixture.new_wsgi_app(child_factory=fixture.Form.factory(), enable_js=True))
    browser.open('/')

    vassert( ['has-error'] == fixture.get_form_group_highlight_marks(browser, index=0) )
    [error] = fixture.get_form_group_errors(browser, index=0)
    vassert( error.text == 'Some input is required' )

    browser.type(XPath.input_labelled('Some input'), 'valid value')
    browser.press_tab(XPath.input_labelled('Some input'))

    vassert( ['has-success'] == fixture.get_form_group_highlight_marks(browser, index=0) )
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
    """A ChoicesLayout can be used to add a CheckboxInput inlined or stacked."""
    stacked_container = Div(fixture.view).use_layout(ChoicesLayout())
    stacked_container.layout.add_choice(CheckboxInput(fixture.form, fixture.field))

    tester = WidgetTester(stacked_container)
    vassert( fixture.input_is_wrapped_in_label(tester) )
    vassert( fixture.main_element(tester).tag == 'div' )
    vassert( fixture.main_element(tester).attrib['class'] == 'checkbox' )

    inlined_container = Div(fixture.view).use_layout(ChoicesLayout(inline=True))
    inlined_container.layout.add_choice(CheckboxInput(fixture.form, fixture.field))

    tester = WidgetTester(inlined_container)
    vassert( fixture.input_is_wrapped_in_label(tester) )
    vassert( fixture.main_element(tester).tag == 'label' )
    vassert( fixture.main_element(tester).attrib['class'] == 'checkbox-inline' )


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
    """The SingleRadioButtons inside a RadioButtonInput are also laid out using a ChoicesLayout."""
    stacked_radio = RadioButtonInput(fixture.form, fixture.field)

    tester = WidgetTester(stacked_radio)
    vassert( fixture.input_is_wrapped_in_label(tester) )
    vassert( fixture.main_element(tester).tag == 'div' )
    vassert( fixture.main_element(tester).attrib['class'] == 'radio' )

    inlined_radio = RadioButtonInput(fixture.form, fixture.field, button_layout=ChoicesLayout(inline=True))

    tester = WidgetTester(inlined_radio)
    vassert( fixture.input_is_wrapped_in_label(tester) )
    vassert( fixture.main_element(tester).tag == 'label' )
    vassert( fixture.main_element(tester).attrib['class'] == 'radio-inline' )


class InputGroupFixture(WebFixture, InputMixin):
    def new_an_input(self):
        return TextInput(self.form, self.field)

    @scenario
    def plain_text(self):
        self.input_group = InputGroup('before text', self.an_input, 'after text')
        self.expects_before_html = '<span class="input-group-addon">before text</span>'
        self.expects_after_html = '<span class="input-group-addon">after text</span>'

    @scenario
    def none_specified(self):
        self.input_group = InputGroup(None, self.an_input, None)
        self.expects_before_html = ''
        self.expects_after_html = ''

    @scenario
    def widgets(self):
        self.input_group = InputGroup(P(self.view, text='before widget'), 
                                      self.an_input, 
                                      P(self.view, text='after widget'))
        self.expects_before_html = '<span class="input-group-addon"><p>before widget</p></span>'
        self.expects_after_html = '<span class="input-group-addon"><p>after widget</p></span>'


@test(InputGroupFixture)
def input_group(fixture):
    """An InputGroup is a composition of an input with some text or Widget before and/or after an input."""
    tester = WidgetTester(fixture.input_group)
    
    [outer_div] = tester.xpath('//div')
    vassert( outer_div.attrib['class'] == 'input-group' )
    
    if fixture.expects_before_html:
        rendered_html = tester.get_html_for('//div/input/preceding-sibling::span')
        vassert( rendered_html == fixture.expects_before_html )
    else:
        vassert( not tester.is_element_present('//div/input/preceding-sibling::span') )

    children = outer_div.getchildren()
    the_input = children[1] if fixture.expects_before_html else children[0]
    vassert( the_input.tag == 'input' )
    vassert( the_input.name == 'an_attribute' )

    if fixture.expects_after_html:
        rendered_html = tester.get_html_for('//div/input/following-sibling::span')
        vassert( rendered_html == fixture.expects_after_html )
    else:
        vassert( not tester.is_element_present('//div/input/following-sibling::span') )


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






