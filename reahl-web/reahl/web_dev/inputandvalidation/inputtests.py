# Copyright 2009-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from webob import Request
from webob.exc import HTTPSeeOther

from nose.tools import istest
from reahl.tofu import Fixture, test, scenario
from reahl.tofu import vassert, expected
from reahl.stubble import stubclass, EmptyStub, exempt

from reahl.web.ui import Input, TextInput, Button, Form, ValidationException, \
                          LabelOverInput, CueInput, CheckboxInput, TextInput, InputLabel, ButtonInput,\
                          PasswordInput, Button, LabelledInlineInput, LabelledBlockInput, P,\
                          TextArea, SelectInput, RadioButtonInput

from reahl.web.fw import WebExecutionContext
from reahl.component.modelinterface import Field, EmailField, BooleanField,\
                             RequiredConstraint, MinLengthConstraint, PatternConstraint, RemoteConstraint,\
                             Event, Allowed, exposed, Action, Choice, ChoiceGroup, ChoiceField, IntegerField,\
                             MultiChoiceField, DateField
from reahl.component.exceptions import IsInstance
from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import WidgetTester, Browser, XPath
from reahl.component_dev.fieldtests import FieldMixin

from reahl.partymodel import Party

class InputMixin(FieldMixin):
    def new_form(self):
        return Form(self.view, u'test')

    def new_event(self, label=u'click me'):
        event = Event(label=label)
        event.bind(u'aname', None)
        self.form.define_event_handler(event)
        return event

class SimpleInputFixture(WebFixture, InputMixin):
    pass

class InputMixin2(InputMixin):
    def new_field(self, label=u'the label'):
        return Field(label=label)
    def new_model_object(self):
        fixture = self
        class ModelObject(object):
            def handle_event(self):
                pass
            @exposed
            def events(self, events):
                events.an_event = Event(label=u'click me', action=Action(self.handle_event))
            @exposed
            def fields(self, fields):
                fields.an_attribute = fixture.field
        return ModelObject()

class InputStateFixture(WebFixture, InputMixin):
    def new_field(self):
        field = EmailField(default=u'default value')
        field.bind(u'an_attribute', self.model_object)
        return field

    def new_input(self):    
        return Input(self.form, self.field)

    @scenario
    def defaulted_input_no_value_on_domain(self):
        del self.model_object.an_attribute
        self.input.prepare_input()

        self.expected_state = u'defaulted'
        self.expected_value = u'default value'

    @scenario
    def defaulted_input_value_on_domain(self):
        self.input.prepare_input()
        self.model_object.an_attribute = u'something'

        self.expected_state = u'defaulted'
        self.expected_value = u'something'

    @scenario
    def validly_entered(self):
        self.input.enter_value(u'someone@home.org')
        self.input.prepare_input()

        self.expected_state = u'validly_entered' 
        self.expected_value = u'someone@home.org'

    @scenario
    def empty_input_non_required_field(self):
        self.input.enter_value(u'')
        self.input.prepare_input()

        self.expected_state = u'validly_entered' 
        self.expected_value = u''

    @scenario
    def empty_input_required_field(self):
        self.field.make_required(u'')
        self.input.enter_value(u'')
        self.input.prepare_input()

        self.expected_state = u'invalidly_entered' 
        self.expected_value = u''

    @scenario
    def invalidly_entered(self):
        self.input.enter_value(u'not an email address')
        self.input.prepare_input()

        self.expected_state = u'invalidly_entered' 
        self.expected_value = u'not an email address'



@istest
class InputDetailsTests(object):
    @test(InputStateFixture)
    def the_states_of_an_input(self, fixture):
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



@istest
class BasicInputTests(object):
    class Scenarios(WebFixture, InputMixin):
        @scenario
        def input_label(self):
            html_input = TextInput(self.form, self.field)
            self.widget = InputLabel(html_input)
            self.expected_html = u'<label for="an_attribute">the label</label>'
            self.field_controls_visibility = True

        @scenario
        def input_label_with_text(self):
            html_input = TextInput(self.form, self.field)
            self.widget = InputLabel(html_input, text=u'some text')
            self.expected_html = u'<label for="an_attribute">some text</label>'
            self.field_controls_visibility = True

        @scenario
        def button_input(self):
            self.widget = self.form.add_child(ButtonInput(self.form, self.event))
            self.expected_html = u'<input name="event.aname?" form="test" type="submit" value="click me">'
            self.field_controls_visibility = False

        @scenario
        def button(self):
            self.widget = self.form.add_child(Button(self.form, self.event))
            self.expected_html = u'<span class="reahl-button"><input name="event.aname?" form="test" type="submit" value="click me"></span>'
            self.field_controls_visibility = False

        @scenario
        def labelled_inline_input(self):
            self.model_object.an_attribute = u'field value'
            self.widget = self.form.add_child(LabelledInlineInput(TextInput(self.form, self.field)))
            self.expected_html = u'<span class="reahl-labelledinput">'\
                                 u'<label for="an_attribute">the label</label>' \
                                 u'<span><input name="an_attribute" form="test" type="text" value="field value" class="reahl-textinput"></span>' \
                                 u'</span>'
            self.field_controls_visibility = True

        @scenario
        def labelled_block_input(self):
            self.model_object.an_attribute = u'field value'
            self.widget = self.form.add_child(LabelledBlockInput(TextInput(self.form, self.field)))
            self.expected_html = u'<div class="reahl-labelledinput yui-g">'\
                                 u'<div class="first yui-u"><label for="an_attribute">the label</label></div>' \
                                 u'<div class="yui-u"><input name="an_attribute" form="test" type="text" value="field value" class="reahl-textinput"></div>' \
                                 u'</div>'
            self.field_controls_visibility = True

        @scenario
        def password(self):
            self.widget = self.form.add_child(PasswordInput(self.form, self.field)) 
            self.expected_html = u'<input name="an_attribute" form="test" type="password">'
            self.field_controls_visibility = True

        @scenario
        def checkbox_true(self):
            """A checkbox needs a 'checked' an_attribute if its field is True. It also renders ONLY the
                validation message for its required validation_constraint, not for all constraints"""
            self.model_object.an_attribute = True

            self.field = BooleanField(required=True, label=u'my text', required_message=u'$label is needed here')
            self.field.bind(u'an_attribute', self.model_object)

            self.widget = self.form.add_child(CheckboxInput(self.form, self.field))
            self.expected_html = u'<input name="an_attribute" checked="checked" form="test" required="*" type="checkbox" ' \
                                 u'class="{&quot;validate&quot;: {&quot;messages&quot;: {&quot;required&quot;: &quot;my text is needed here&quot;}}}">'
            self.field_controls_visibility = True

        @scenario
        def checkbox_false(self):
            self.checkbox_true()
            self.model_object.an_attribute = False
            self.expected_html = u'<input name="an_attribute" form="test" required="*" type="checkbox" '\
                                 u'class="{&quot;validate&quot;: {&quot;messages&quot;: {&quot;required&quot;: &quot;my text is needed here&quot;}}}">'
            self.field_controls_visibility = True

        @scenario
        def text_area_input(self):
            self.widget = self.form.add_child(TextArea(self.form, self.field, rows=30, columns=20))
            self.expected_html = u'<textarea name="an_attribute" cols="20" rows="30">field value</textarea>'
            self.field_controls_visibility = True

        @scenario
        def select_input(self):
            self.model_object.an_attribute = 2

            choices = [Choice(False, BooleanField(label=u'None')),
                       ChoiceGroup(u'grouped', [
                           Choice(1, IntegerField(label=u'One')), 
                           Choice(2, IntegerField(label=u'Two'))])
                      ]
            self.field = ChoiceField(choices)
            self.field.bind(u'an_attribute', self.model_object)

            self.widget = self.form.add_child(SelectInput(self.form, self.field))
            group = u'<optgroup label="grouped"><option value="1">One</option><option selected="selected" value="2">Two</option></optgroup>'
            option = u'<option value="off">None</option>'
            self.expected_html = u'<select name="an_attribute" form="test">%s%s</select>' % (option, group)
            self.field_controls_visibility = True

        @scenario
        def select_input_multi(self):
            self.model_object.an_attribute = [2]

            choices = [Choice(1, IntegerField(label=u'One')), 
                       Choice(2, IntegerField(label=u'Two'))
                      ]
            self.field = MultiChoiceField(choices)
            self.field.bind(u'an_attribute', self.model_object)

            self.widget = self.form.add_child(SelectInput(self.form, self.field)) 
            options = u'<option value="1">One</option><option selected="selected" value="2">Two</option>'
            self.expected_html = u'<select name="an_attribute" form="test" multiple="multiple">%s</select>' % (options)
            self.field_controls_visibility = True

        @scenario
        def radio_button(self):
            self.model_object.an_attribute = 2

            choices = [ Choice(1, IntegerField(label=u'One')), 
                        Choice(2, IntegerField(label=u'Two')) ]
            self.field = ChoiceField(choices)
            self.field.bind(u'an_attribute', self.model_object)

            self.widget = self.form.add_child(RadioButtonInput(self.form, self.field))

            radio_button = u'<span class="reahl-radio-button"><input name="an_attribute"%s form="test" type="radio" value="%s">%s</span>'

            outer_div = u'<div class="reahl-radio-button-input">%s</div>'
            buttons = (radio_button % (u'', u'1', u'One')) + (radio_button % (u' checked="checked"', u'2', u'Two'))
            self.expected_html = outer_div % buttons
            self.field_controls_visibility = True

    @test(Scenarios)
    def basic_rendering(self, fixture):
        """What the rendered html for a number of simple inputs look like."""
        
        tester = WidgetTester(fixture.widget)

        # Case: Normal behaviour
        actual = tester.render_html()
        vassert( actual == fixture.expected_html )

        # Case: When the Widget should not be visible
        fixture.field.access_rights.readable = Allowed(False)
        fixture.field.access_rights.writable = Allowed(False)
        actual = tester.render_html()
        if fixture.field_controls_visibility:
            vassert( actual == u'' )
        else:
            vassert( actual == fixture.expected_html )
        

    @test(SimpleInputFixture)
    def wrong_args_to_input(self, fixture):
        """Passing the wrong arguments upon constructing an Input results in an error."""
        
        with expected(IsInstance):
            Input(fixture.form, EmptyStub()) 

        with expected(IsInstance):
            Input(EmptyStub(), Field()) 


    class CheckboxFixture(WebFixture, InputMixin2):
        def new_field(self):
            return BooleanField(label=u'my text')

    @test(CheckboxFixture)
    def marshalling_of_checkbox(self, fixture):
        """When a form is submitted, the value of a checkbox is derived from
           whether the checkbox is included in the submission or not."""

        model_object = fixture.model_object
        class MyForm(Form):
            def __init__(self, view, name):
                super(MyForm, self).__init__(view, name)
                checkbox = self.add_child(CheckboxInput(self, model_object.fields.an_attribute))
                self.define_event_handler(model_object.events.an_event)
                self.add_child(Button(self, model_object.events.an_event))
                fixture.checkbox = checkbox

        wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory(u'myform'))
        fixture.reahl_server.set_app(wsgi_app)
        fixture.driver_browser.open('/')

        # Case: checkbox is submitted with form (ie checked)
        fixture.driver_browser.check(u"//input[@type='checkbox']")
        fixture.driver_browser.click(u"//input[@value='click me']")

        vassert( model_object.an_attribute )
        vassert( fixture.checkbox.value == u'on' )        

        # Case: checkbox is not submitted with form (ie unchecked)
        fixture.driver_browser.uncheck(u"//input[@type='checkbox']")
        fixture.driver_browser.click(u"//input[@value='click me']")

        vassert( not model_object.an_attribute )
        vassert( fixture.checkbox.value == u'off' )        



class LabelOverInputFixture(WebFixture, InputMixin2):
    label_xpath = u"//form/span[@class='reahl-labelledinput reahl-labeloverinput']/label[@for='an_attribute' and text()='the label']"

@istest
class LabelOverInputTests(object):
    @test(LabelOverInputFixture)
    def label_behaviour(self, fixture):
        """The label is displayed over the input, but it disappears when selected
           or when there's a value in the input."""
        
        model_object = fixture.model_object

        class MyForm(Form):
            def __init__(self, view, name):
                super(MyForm, self).__init__(view, name)
                self.add_child(LabelOverInput(TextInput(self, model_object.fields.an_attribute)))
                self.define_event_handler(model_object.events.an_event)
                self.add_child(Button(self, model_object.events.an_event))

        wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory(u'myform'), enable_js=True)
        fixture.reahl_server.set_app(wsgi_app)

        # Case: the field is empty and does not have a default value
        # - render initially with label
        fixture.driver_browser.open('/')
        vassert( fixture.driver_browser.is_element_present(fixture.label_xpath) )
        fixture.driver_browser.wait_for_element_visible(fixture.label_xpath)
        
        # - if click, label disappears, input gets focus
        fixture.driver_browser.click(fixture.label_xpath)
        fixture.driver_browser.wait_for_element_not_visible(fixture.label_xpath)

        # - if focus lost, label appears again if nothing is entered
        fixture.driver_browser.press_tab(u'//input')
        fixture.driver_browser.wait_for_element_visible(fixture.label_xpath)
        
        # - if focus lost, label does not appear again if something is entered
        fixture.driver_browser.type(u'//input[@type="text"]', 'my@email.com')
        fixture.driver_browser.wait_for_element_not_visible(fixture.label_xpath)
        fixture.driver_browser.press_tab(u'//input')
        fixture.driver_browser.wait_for_element_not_visible(fixture.label_xpath)

        
        # Case: the field has a defaulted value
        model_object.an_attribute = 'some value'
        fixture.driver_browser.open('/')
        
        # - render initially without a label
        fixture.driver_browser.wait_for_element_not_visible(fixture.label_xpath)

        # - if value removed, and focus lost, label appears
        fixture.driver_browser.type(u'//input[@type="text"]', '')
        fixture.driver_browser.press_tab(u'//input')
        fixture.driver_browser.wait_for_element_visible(fixture.label_xpath)

    @test(LabelOverInputFixture)
    def basic_rendering(self, fixture):
        """What the html for a LabelOverInput looks like."""

        fixture.field.bind(u'an_attribute', fixture.model_object)
        label_over_input = fixture.form.add_child(LabelOverInput(TextInput(fixture.form, fixture.field))) 
        tester = WidgetTester(label_over_input)

        # Case: HTML - with a value
        #  - has CSS class reahl-labeloverinput
        #  - the label is hidden
        fixture.model_object.an_attribute = u'my value'
        actual = tester.render_html()
        expected = u'<span class="reahl-labelledinput reahl-labeloverinput">'\
                   u'<label for="an_attribute" hidden="true">the label</label>' \
                   u'<span><input name="an_attribute" form="test" type="text" value="my value" class="reahl-textinput"></span>'\
                   u'</span>'
        vassert( actual == expected )

        # Case: HTML - without a value
        #  - has CSS class reahl-labeloverinput
        #  - the label is not hidden
        del fixture.model_object.an_attribute
        actual = tester.render_html()
        expected = u'<span class="reahl-labelledinput reahl-labeloverinput">'\
                   u'<label for="an_attribute">the label</label>' \
                   u'<span><input name="an_attribute" form="test" type="text" value="" class="reahl-textinput"></span>'\
                   u'</span>'
        vassert( actual == expected )

        # Case: when the underlying input is not visible
        fixture.field.access_rights.readable = Allowed(False)
        fixture.field.access_rights.writable = Allowed(False)
        actual = tester.render_html()
        vassert( actual == u'' )

class CueInputFixture(WebFixture, InputMixin2):
    cue_xpath = u"//div[@class='reahl-cueinput reahl-labelledinput yui-g']/div/div[@class='reahl-cue yui-u']/p"

    def new_text_input(self):
        return TextInput(self.form, self.field)

    def new_cue(self):
        return P(self.view, text=u'this is your cue')

    def new_cue_input(self):
        return CueInput(self.text_input, self.cue)

        
@istest
class CueInputTests(object):
    @test(CueInputFixture)
    def cue_behaviour(self, fixture):
        """The Cue appears when its input has focus only."""
        model_object = fixture.model_object

        class MyForm(Form):
            def __init__(self, view, name):
                super(MyForm, self).__init__(view, name)
                self.add_child(CueInput(TextInput(self, model_object.fields.an_attribute), P(view, text=u'this is your cue')))
                self.define_event_handler(model_object.events.an_event)
                self.add_child(Button(self, model_object.events.an_event))

        wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory(u'myform'), enable_js=True)
        fixture.reahl_server.set_app(wsgi_app)
        fixture.driver_browser.open('/')

        # - initially rendered without cue
        vassert( fixture.driver_browser.is_element_present(fixture.cue_xpath) )
        fixture.driver_browser.wait_for_element_not_visible(fixture.cue_xpath)
        
        # - if click, cue appears
        fixture.driver_browser.click(u'//input[@type="text"]')
        fixture.driver_browser.wait_for_element_visible(fixture.cue_xpath)

        # - if focus lost, cue disappears again 
        fixture.driver_browser.press_tab('//input')
        fixture.driver_browser.wait_for_element_not_visible(fixture.cue_xpath)

    @test(CueInputFixture)
    def basic_rendering(self, fixture):
        """What the html for a CueInput looks like."""
        fixture.field.bind(u'an_attribute', fixture.model_object)
        cue = fixture.cue
        cue_input = fixture.cue_input
        fixture.form.add_child(cue_input) 
        fixture.model_object.an_attribute = u'my value'
 
        tester = WidgetTester(cue_input)

        # Case: normal behaviour
        actual = tester.render_html()
        expected = u'<div class="reahl-cueinput reahl-labelledinput yui-g">'\
                    u'<div class="first yui-u"><label for="an_attribute">the label</label></div>' \
                    u'<div class="yui-g">' \
                     u'<div class="first yui-u"><input name="an_attribute" form="test" type="text" value="my value" class="reahl-textinput"></div>' \
                     u'<div class="reahl-cue yui-u">' \
                      u'<p hidden="true">this is your cue</p>' \
                     u'</div>' \
                    u'</div>' \
                   u'</div>'
        vassert( actual == expected )

        # Case: when the underlying input is not visible
        fixture.field.access_rights.readable = Allowed(False)
        fixture.field.access_rights.writable = Allowed(False)
        actual = tester.render_html()
        vassert( actual == u'' )


class FuzzyTextInputFixture(WebFixture, InputMixin2):
    def new_field(self, label=u'the label'):
        return DateField(label=label)



@istest
class TextInputTests(object):
    @test(FuzzyTextInputFixture)
    def fuzzy(self, fixture):
        """A TextInput can be created as fuzzy=True. Doing this results in the possibly imprecise
           input that was typed by the user to be interpreted server-side and changed to the
           more exact representation in the client browser.  This happens upon the input losing focus."""
        model_object = fixture.model_object
        class MyForm(Form):
            def __init__(self, view, name):
                super(MyForm, self).__init__(view, name)
                self.add_child(LabelledBlockInput(TextInput(self, model_object.fields.an_attribute, fuzzy=True)))
                self.define_event_handler(model_object.events.an_event)
                self.add_child(Button(self, model_object.events.an_event))

        wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory(u'myform'), enable_js=True)
        fixture.reahl_server.set_app(wsgi_app)
        browser = fixture.driver_browser
        browser.open('/')

        browser.type(XPath.input_labelled(u'the label'), u'20 November 2012')
        browser.press_tab(XPath.input_labelled(u'the label'))
        browser.wait_for(browser.is_element_value, XPath.input_labelled(u'the label'), u'20 Nov 2012')





