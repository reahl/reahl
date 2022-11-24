# Copyright 2016-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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



from reahl.tofu import Fixture
from reahl.tofu.pytestsupport import with_fixtures

from reahl.browsertools.browsertools import XPath

from reahl.component.modelinterface import ExposedNames, Field

from reahl.web.bootstrap.ui import P
from reahl.web.bootstrap.forms import Form, FormLayout, CueInput, TextInput

from reahl.web_dev.fixtures import WebFixture


class CueInputFixture(Fixture):
    cue_element_xpath = "//p"

    def new_domain_object(self):
        class DomainObject:
            fields = ExposedNames()
            fields.field = lambda i: Field(label='MyField')
        return DomainObject()


@with_fixtures(WebFixture, CueInputFixture)
def test_cue_input_display_basics(web_fixture, cue_input_fixture):
    """A CueInput displays a given cue when its wrapped Input has focus and hides the cue otherwise."""
    fixture = cue_input_fixture

    class FormWithCueInput(Form):
            def __init__(self, view):
                super().__init__(view, 'test')
                self.use_layout(FormLayout())
                cue_input = CueInput(TextInput(self, fixture.domain_object.fields.field), P(view, 'this is your cue'))
                self.layout.add_input(cue_input)


    wsgi_app = web_fixture.new_wsgi_app(child_factory=FormWithCueInput.factory(), enable_js=True)

    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    #initially the cue is not visible
    browser.wait_for_element_not_visible(fixture.cue_element_xpath)
    #tabbing to the input reveals the cue
    browser.focus_on(XPath.input_labelled('MyField'))
    browser.wait_for_element_visible(fixture.cue_element_xpath)

    #moving focus to another input causes the cue to be hidden
    browser.press_tab()
    browser.wait_for_element_not_visible(fixture.cue_element_xpath)


@with_fixtures(WebFixture, CueInputFixture)
def test_cue_is_visible_when_js_disabled(web_fixture, cue_input_fixture):
    """A CueInput degrades without JS to always display its cue."""
    fixture = cue_input_fixture

    class FormWithCueInput(Form):
            def __init__(self, view):
                super().__init__(view, 'test')
                self.use_layout(FormLayout())
                cue_input = CueInput(TextInput(self, fixture.domain_object.fields.field), P(view, 'this is your cue'))
                self.layout.add_input(cue_input)


    wsgi_app = web_fixture.new_wsgi_app(child_factory=FormWithCueInput.factory(), enable_js=False)

    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')
    browser.refresh() # To prevent flipper we don't understand

    #the cue is visible when JS is disbled
    browser.wait_for_element_visible(fixture.cue_element_xpath)
