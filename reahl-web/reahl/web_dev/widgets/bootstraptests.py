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

from reahl.web.fw import UserInterface
from reahl.web.ui import Div, P, HTML5Page, Header, Footer

from reahl.component.exceptions import ProgrammerError, IsInstance
from reahl.component.modelinterface import exposed, Field, BooleanField, Event
from reahl.web.bootstrap import ColumnLayout, ResponsiveSize, InputGroup, Button, FormLayout, Form, TextInput, CheckboxInput



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



# FormLayout
#DONE Form can be vertical/horizontal/the other stuff?
# Adding an input using a form layout adds the input (optionally with Some input, help text)
# - add form-group with label and help-text
# - form-group reacts to valid/invalidly entered input
#    - both in js and also on the server
#    - js can clear what server rendered
# - label is rendered by default, except for checkboxes when its not
# ChoiceLayout
# SingleRadioButtons and Checkboxes can be laid out inlined or not using ChoiceLayout
# - single radio buttons in a radiobuttoninput is laid out inline or not
# - checkbox is added to form-group not inlined
# InputGroup:
#  - An InputGroup is a composition of an input with some text before and/or after it
#  - An InputGroup can also include Widgets in its composition
#  - An InputGroup can also be added as Input to a form 
# Using FormLayout, you can lay out a form as horizontal, x or y
# Each of the PrimitiveInputs renders like X (bootstrap classes & no error labels - just plain html inputs)
# ContainerLayout makes its widget a bootstrap container


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
    


@test(FormLayoutFixture)
def input_validation_cues(fixture):
    """Visible cues are inserted to indicate the current validation state and possible validation error messages to a user. """
    class FormWithInput(Form):
        def __init__(self, view):
            super(FormWithInput, self).__init__(view, 'aform')
            self.use_layout(FormLayout())
            self.layout.add_input(TextInput(self, fixture.domain_object.fields.an_attribute))

    fixture.reahl_server.set_app(fixture.new_wsgi_app(child_factory=FormWithInput.factory(), enable_js=True))
    browser = fixture.driver_browser
    browser.open('/')

    vassert( not fixture.get_form_group_highlight_marks(browser) )
    vassert( not fixture.get_form_group_errors(browser) )

    vassert( ['has-error'] == fixture.get_form_group_highlight_marks(browser) )
    [error] = fixture.get_form_group_errors(browser)
    vassert( error.text == 'Some input is required' )

    browser.type(XPath.input_labelled('Some input'), 'valid value')
    vassert( ['has-success'] == fixture.get_form_group_highlight_marks(browser) )
    vassert( not fixture.get_form_group_errors(browser) )


class ServerSideValidationScenarios(FormLayoutFixture):
    @scenario
    def invalidly_entered(self):
        pass

@test(FormLayoutFixture)
def server_side_input_validation_cues(fixture):
    """. """
    class ModelObject(object):
        @exposed
        def fields(self, fields):
            fields.an_attribute = Field(label='Some input', required=True)
            fields.another_attribute = Field(label='Another input', required=True)
        @exposed
        def events(self, events):
            events.submit = Event(label='Submit')
            
    fixture.domain_object = ModelObject()

    class FormWithInput(Form):
        def __init__(self, view):
            super(FormWithInput, self).__init__(view, 'aform')
            self.use_layout(FormLayout())
            self.layout.add_input(TextInput(self, fixture.domain_object.fields.an_attribute))
            self.layout.add_input(TextInput(self, fixture.domain_object.fields.another_attribute))
            self.define_event_handler(fixture.domain_object.events.submit)
            self.add_child(Button(self, fixture.domain_object.events.submit))
            

    browser = Browser(fixture.new_wsgi_app(child_factory=FormWithInput.factory()))
    browser.open('/')

    vassert( not fixture.get_form_group_highlight_marks(browser, index=0) )
    vassert( not fixture.get_form_group_errors(browser, index=0) )

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


# server-side renders correct error/success? classes and error messages
# js can clear/manipulate server-side rendered classes/error messages
# disabled?


