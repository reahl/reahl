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



from reahl.tofu import Fixture, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.browsertools.browsertools import XPath

from reahl.component.modelinterface import ExposedNames, BooleanField

from reahl.web.bootstrap.ui import Div, P
from reahl.web.bootstrap.forms import Form, FormLayout, CheckboxInput
from reahl.web.bootstrap.popups import PopupA, CheckCheckboxScript

from reahl.web_dev.fixtures import WebFixture


@uses(web_fixture=WebFixture)
class PopupAFixture(Fixture):

    # (note that this xpath ensures that the p is the ONLY content of the dialog)
    poppedup_contents = "//div[@class='modal-body' and count(*)=1]/p[@id='contents']"

    def is_popped_up(self):
        return self.web_fixture.driver_browser.is_visible(self.poppedup_contents)


@with_fixtures(WebFixture, PopupAFixture)
def test_default_behaviour(web_fixture, popup_a_fixture):
    """If you click on the A, a popupwindow opens with its contents the specified
       element on the target page."""

    class PopupTestPanel(Div):
        def __init__(self, view):
            super().__init__(view)
            self.add_child(PopupA(view, view.as_bookmark(), '#contents'))
            popup_contents = self.add_child(P(view, text='this is the content of the popup'))
            popup_contents.set_id('contents')

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=PopupTestPanel.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    # The A is rendered correctly
    assert browser.is_element_present("//a[@title='Home page' and text()='Home page' and @href='/']")

    # subsequent behaviour
    browser.click(XPath.link().with_text('Home page'))
    browser.wait_for(popup_a_fixture.is_popped_up)

    #check some bootstrap attributes
    dialog_xpath = "//div[@class='modal fade show' and @tabindex='-1']/div[@class='modal-dialog']/div[@class='modal-content']"
    assert browser.is_element_present(dialog_xpath)

    browser.click(XPath.button_labelled('Close'))
    browser.wait_for_not(popup_a_fixture.is_popped_up)


@with_fixtures(WebFixture, PopupAFixture)
def test_customising_dialog_buttons(web_fixture, popup_a_fixture):
    """The buttons of the dialog can be customised."""

    class PopupTestPanel(Div):
        def __init__(self, view):
            super().__init__(view)
            popup_a = self.add_child(PopupA(view, view.as_bookmark(), '#contents'))
            popup_a.add_js_button('Butt1')
            popup_a.add_js_button('Butt2')
            popup_contents = self.add_child(P(view, text='this is the content of the popup'))
            popup_contents.set_id('contents')

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=PopupTestPanel.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser

    button1_xpath = XPath.button_labelled('Butt1')
    button2_xpath = XPath.button_labelled('Butt2')

    browser.open('/')

    browser.click(XPath.link().with_text('Home page'))
    browser.wait_for(popup_a_fixture.is_popped_up)

    assert browser.is_element_present(button1_xpath)
    assert browser.is_element_present(button2_xpath)


@with_fixtures(WebFixture, PopupAFixture)
def test_workings_of_check_checkbox_button(web_fixture, popup_a_fixture):
    """A CheckCheckBoxButton checks the checkbox on the original page when clicked."""

    class PopupTestPanel(Div):
        fields = ExposedNames()
        fields.field = lambda i: BooleanField(label='a checkbox')

        def __init__(self, view):
            super().__init__(view)
            popup_a = self.add_child(PopupA(view, view.as_bookmark(), '#contents'))
            popup_contents = self.add_child(P(view, text='this is the content of the popup'))
            popup_contents.set_id('contents')
            form = self.add_child(Form(view, 'aform')).use_layout(FormLayout())
            checkbox = form.layout.add_input(CheckboxInput(form, self.fields.field))

            popup_a.add_js_button('Checkit', CheckCheckboxScript(checkbox))

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=PopupTestPanel.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    browser.click(XPath.link().with_text('Home page'))
    browser.wait_for(popup_a_fixture.is_popped_up)

    browser.click(XPath.button_labelled('Checkit'))
    browser.wait_for_not(popup_a_fixture.is_popped_up)

    assert browser.is_selected(XPath.input_labelled('a checkbox'))


@with_fixtures(WebFixture, PopupAFixture)
def test_centering_dialog_vertically(web_fixture, popup_a_fixture):
    """The dialog can be centered vertically."""

    class PopupTestPanel(Div):
        def __init__(self, view):
            super().__init__(view)
            self.add_child(PopupA(view, view.as_bookmark(), '#contents', center_vertically=True))
            popup_contents = self.add_child(P(view, text='this is the content of the popup'))
            popup_contents.set_id('contents')

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=PopupTestPanel.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    browser.click(XPath.link().with_text('Home page'))
    browser.wait_for(popup_a_fixture.is_popped_up)

    dialog_xpath = "//div[@class='modal fade show' and @tabindex='-1']/div[@class='modal-dialog modal-dialog-centered']/div[@class='modal-content']"
    assert browser.is_element_present(dialog_xpath)
