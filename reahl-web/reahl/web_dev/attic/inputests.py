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

import re

from reahl.tofu import scenario, test, vassert

from reahl.web.ui import Form, TextInput, P

from reahl.web.attic.layout import LabelledInlineInput, LabelledBlockInput, CueInput, Button

from reahl.component.modelinterface import Allowed, Event, Field, Action, exposed
from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import WidgetTester
from reahl.component_dev.test_field import FieldMixin

class InputMixin(FieldMixin):
    def new_form(self):
        return Form(self.view, 'test')

    def new_event(self, label='click me'):
        event = Event(label=label)
        event.bind('aname', None)
        self.form.define_event_handler(event)
        return event


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

class Scenarios(WebFixture, InputMixin):


    @scenario
    def labelled_inline_input(self):
        self.model_object.an_attribute = 'field value'
        self.widget = self.form.add_child(LabelledInlineInput(TextInput(self.form, self.field)))
        self.expected_html = r'<span class="reahl-labelledinput">'\
                             r'<label for="(.*)">the label</label>' \
                             r'<span><input name="an_attribute" id="\1" form="test" type="text" value="field value" class="reahl-textinput"></span>' \
                             r'</span>'
        self.field_controls_visibility = True

    @scenario
    def labelled_block_input(self):
        self.model_object.an_attribute = 'field value'
        self.widget = self.form.add_child(LabelledBlockInput(TextInput(self.form, self.field)))
        self.expected_html = r'<div class="pure-g reahl-labelledinput">'\
                             r'<div class="column-label pure-u-1-4"><label for="(.*)">the label</label></div>' \
                             r'<div class="column-input pure-u-3-4"><input name="an_attribute" id="\1" form="test" type="text" value="field value" class="reahl-textinput"></div>' \
                             r'</div>'
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


class CueInputFixture(WebFixture, InputMixin2):
    cue_xpath = "//div[contains(@class,'reahl-cueinput')]/div[contains(@class,'reahl-cue')]/p"

    def new_text_input(self):
        return TextInput(self.form, self.field)

    def new_cue(self):
        return P(self.view, text='this is your cue')

    def new_cue_input(self):
        return CueInput(self.text_input, self.cue)


@test(CueInputFixture)
def cue_behaviour(fixture):
    """The Cue appears when its input has focus only."""
    model_object = fixture.model_object

    class MyForm(Form):
        def __init__(self, view, name):
            super(MyForm, self).__init__(view, name)
            self.add_child(CueInput(TextInput(self, model_object.fields.an_attribute), P(view, text='this is your cue')))
            self.define_event_handler(model_object.events.an_event)
            self.add_child(Button(self, model_object.events.an_event))

    wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory('myform'), enable_js=True)
    fixture.reahl_server.set_app(wsgi_app)
    fixture.driver_browser.open('/')

    # - initially rendered without cue
    vassert( fixture.driver_browser.is_element_present(fixture.cue_xpath) )
    fixture.driver_browser.wait_for_element_not_visible(fixture.cue_xpath)

    # - if click, cue appears
    fixture.driver_browser.click('//input[@type="text"]')
    fixture.driver_browser.wait_for_element_visible(fixture.cue_xpath)

    # - if focus lost, cue disappears again
    fixture.driver_browser.press_tab('//input')
    fixture.driver_browser.wait_for_element_not_visible(fixture.cue_xpath)


class BasicRenderingCueInputScenarios(CueInputFixture):
    @scenario
    def normal(self):
        self.expected_html = r'<div class="pure-g reahl-cueinput reahl-labelledinput">'\
                r'<div class="column-label pure-u-1-4"><label for="(.*)">the label</label></div>' \
                r'<div class="column-input pure-u-1-2"><input name="an_attribute" id="\1" form="test" type="text" value="my value" class="reahl-textinput"></div>' \
                 r'<div class="column-cue pure-u-1-4 reahl-cue">' \
                 r'<p hidden="true">this is your cue</p>' \
                 r'</div>' \
               r'</div>'

    @scenario
    def not_allowed_to_be_seen(self):
        self.field.access_rights.readable = Allowed(False)
        self.field.access_rights.writable = Allowed(False)
        self.expected_html = ''


@test(BasicRenderingCueInputScenarios)
def rendering_cue_input(fixture):
    """What the html for a CueInput looks like."""
    fixture.model_object.an_attribute = 'my value'
    fixture.field.bind('an_attribute', fixture.model_object)
    cue = fixture.cue
    cue_input = fixture.cue_input
    fixture.form.add_child(cue_input)

    tester = WidgetTester(cue_input)

    actual = tester.render_html()
    vassert( re.match(fixture.expected_html, actual) )
