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

from reahl.component.modelinterface import exposed, BooleanField

from reahl.web.bootstrap.libraries import Bootstrap4, ReahlBootstrap4Additions
from reahl.web.bootstrap.ui import Div, Form, FormLayout, P, CheckboxInput
from reahl.web.bootstrap.popups import PopupA, CheckCheckboxButton, DialogButton

class PopupAFixture(WebFixture):
    # (note that this xpath ensures that the p is the ONLY content of the dialog)
    poppedup_contents = "//div[@class='modal-body' and count(*)=1]/p[@id='contents']"

    def new_wsgi_app(self):
        return super(PopupAFixture, self).new_wsgi_app(enable_js=True,
                                                       child_factory=self.MainWidget.factory())
    def new_webconfig(self):
        web = super(PopupAFixture, self).new_webconfig()
        web.frontend_libraries.add(Bootstrap4())
        web.frontend_libraries.add(ReahlBootstrap4Additions())
        return web


class PopupAFixtureWithContent(PopupAFixture):
    def new_MainWidget(self):
        fixture = self

        class PopupTestPanel(Div):
            def __init__(self, view):
                super(PopupTestPanel, self).__init__(view)
                self.add_child(PopupA(view, view.as_bookmark(), '#contents'))
                popup_contents = self.add_child(P(view, text='this is the content of the popup'))
                popup_contents.set_id('contents')

        return PopupTestPanel

@test(PopupAFixtureWithContent)
def default_behaviour(fixture):
    """If you click on the A, a popupwindow opens with its contents the specified
       element on the target page."""

    fixture.reahl_server.set_app(fixture.wsgi_app)
    browser = fixture.driver_browser
    browser.open('/')

    # The A is rendered correctly
    browser.is_element_present("//a[@title='Home page' and text()='Home page' and @href='/']")

    # subsequent behaviour
    browser.click(XPath.link_with_text('Home page'))
    browser.wait_for_element_visible(fixture.poppedup_contents)

    browser.click(XPath.button_labelled('Close'))
    browser.wait_for_element_not_visible(fixture.poppedup_contents)


class PopupAFixtureWithCustomButtons(PopupAFixture):
    def new_MainWidget(self):
        fixture = self

        class PopupTestPanel(Div):
            def __init__(self, view):
                super(PopupTestPanel, self).__init__(view)
                popup_a = self.add_child(PopupA(view, view.as_bookmark(), '#contents'))
                popup_a.add_button(DialogButton('Butt1'))
                popup_a.add_button(DialogButton('Butt2'))
                popup_contents = self.add_child(P(view, text='this is the content of the popup'))
                popup_contents.set_id('contents')

        return PopupTestPanel


@test(PopupAFixtureWithCustomButtons)
def customising_dialog_buttons(fixture):
    """The buttons of the dialog can be customised."""

    fixture.reahl_server.set_app(fixture.wsgi_app)
    browser = fixture.driver_browser
    browser.open('/')

    button1_xpath = XPath.button_labelled('Butt1')
    button2_xpath = XPath.button_labelled('Butt2')
    fixture.driver_browser.open('/')

    browser.click(XPath.link_with_text('Home page'))
    browser.wait_for_element_visible(fixture.poppedup_contents)

    vassert( browser.is_element_present(button1_xpath) )
    vassert( browser.is_element_present(button2_xpath) )


class PopupAFixtureWithCheckBox(PopupAFixture):
    def new_MainWidget(self):
        fixture = self

        class PopupTestPanel(Div):
            @exposed
            def fields(self, fields):
                fields.field = BooleanField(label='a checkbox')

            def __init__(self, view):
                super(PopupTestPanel, self).__init__(view)
                popup_a = self.add_child(PopupA(view, view.as_bookmark(), '#contents'))
                popup_contents = self.add_child(P(view, text='this is the content of the popup'))
                popup_contents.set_id('contents')
                form = self.add_child(Form(view, 'aform')).use_layout(FormLayout())
                checkbox = form.layout.add_input(CheckboxInput(form, self.fields.field))

                popup_a.add_button(CheckCheckboxButton('Checkit', checkbox))

        return PopupTestPanel


@test(PopupAFixtureWithCheckBox)
def workings_of_check_checkbox_button(fixture):
    """A CheckCheckBoxButton checks the checkbox on the original page when clicked."""

    fixture.reahl_server.set_app(fixture.wsgi_app)
    browser = fixture.driver_browser
    browser.open('/')

    browser.click(XPath.link_with_text('Home page'))
    browser.wait_for_element_visible(fixture.poppedup_contents)

    browser.click(XPath.button_labelled('Checkit'))
    browser.wait_for_element_not_visible(fixture.poppedup_contents)

    vassert( fixture.driver_browser.is_checked(XPath.input_labelled('a checkbox')) )
