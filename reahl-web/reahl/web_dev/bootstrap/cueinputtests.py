# Copyright 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.webdev.tools import XPath
from reahl.web_dev.fixtures import WebFixture

from reahl.component.modelinterface import exposed, Field

from reahl.web.bootstrap.ui import Form, FormLayout, CueInput, TextInput, P


class CueInputFixture(WebFixture):
    cue_element_xpath = "//p"

    def new_webconfig(self):
        webconfig = super(CueInputFixture, self).new_webconfig()
        webconfig.frontend_libraries.enable_experimental_bootstrap()
        return webconfig

    def new_domain_object(self):
        class DomainObject(object):
            @exposed
            def fields(self, fields):
                fields.field = Field(label='MyField')
        return DomainObject()


@test(CueInputFixture)
def cue_input_display_basics(fixture):
    """A CueInput displays a given cue when its wrapped Input has focus and hides the cue otherwise."""

    class FormWithCueInput(Form):
            def __init__(self, view):
                super(FormWithCueInput, self).__init__(view, 'test')
                self.use_layout(FormLayout())
                cue_input = CueInput(TextInput(self, fixture.domain_object.fields.field), P(view, 'this is your cue'))
                self.layout.add_input(cue_input)

    wsgi_app = fixture.new_wsgi_app(child_factory=FormWithCueInput.factory(), enable_js=True)

    fixture.reahl_server.set_app(wsgi_app)
    browser = fixture.driver_browser
    browser.open('/')

    #initially the cue is not visible
    browser.wait_for_element_not_visible(fixture.cue_element_xpath)
    #tabbing to the input reveals the cue
    browser.focus_on(XPath.input_labelled('MyField'))
    browser.wait_for_element_visible(fixture.cue_element_xpath)

    #moving focus to another input causes the cue to be hidden
    browser.press_tab(XPath.input_labelled('MyField'))
    browser.wait_for_element_not_visible(fixture.cue_element_xpath)


@test(CueInputFixture)
def cue_is_visible_when_js_disabled(fixture):
    """A CueInput degrades without JS to always display its cue."""

    class FormWithCueInput(Form):
            def __init__(self, view):
                super(FormWithCueInput, self).__init__(view, 'test')
                self.use_layout(FormLayout())
                cue_input = CueInput(TextInput(self, fixture.domain_object.fields.field), P(view, 'this is your cue'))
                self.layout.add_input(cue_input)

    wsgi_app = fixture.new_wsgi_app(child_factory=FormWithCueInput.factory(), enable_js=False)

    fixture.reahl_server.set_app(wsgi_app)
    browser = fixture.driver_browser
    browser.open('/')
    browser.refresh() # To prevent flipper we don't understand

    #the cue is visible when JS is disbled
    browser.wait_for_element_visible(fixture.cue_element_xpath)
