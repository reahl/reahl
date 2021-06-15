# Copyright 2019, 2020, 2021 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from reahl.tofu.pytestsupport import with_fixtures
from reahl.tofu import Fixture, scenario

from reahl.browsertools.browsertools import XPath

from reahl.web.fw import UserInterface, Url
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import P
from reahl.web.layout import PageLayout

from reahl.web_dev.fixtures import WebFixture



class ErrorPlacementFixture(Fixture):
    def new_MainUI(self):
        fixture = self
        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(fixture.CustomPage)
        return MainUI

    @scenario
    def without_layout(self):
        """The error is inserted as the very first element on the page"""
        class CustomPage(HTML5Page):
            def __init__(self, view):
                super().__init__(view)
                self.body.add_child(P(view, 'the first paragraph on the page'))
        self.CustomPage = CustomPage
        self.expected_alert = XPath('div')[1].including_class('alert').inside_of(XPath.any('body'))

    @scenario
    def with_layout(self):
        """The error is inserted as the very last element in the header of the page"""
        class CustomPage(HTML5Page):
            def __init__(self, view):
                super().__init__(view)
                self.use_layout(PageLayout())
                self.layout.header.add_child(P(view, 'this is the header'))
                self.layout.contents.add_child(P(view, 'the first paragraph on the page'))
        self.CustomPage = CustomPage
        self.expected_alert = XPath('div')['last()'].including_class('alert').inside_of(XPath.any('header'))


@with_fixtures(WebFixture, ErrorPlacementFixture)
def test_bootstrap_default_error_page(web_fixture, fixture):
    """Bootstrap HTML5Page has a styled error page by default, placed depending on the layout"""

    wsgi_app = web_fixture.new_wsgi_app(site_root=fixture.MainUI)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser

    browser.open('/error?error_message=something+went+wrong&error_source_href=/a_page')

    assert browser.is_element_present(fixture.expected_alert)

    error_message = XPath.paragraph().including_text('something went wrong').inside_of(fixture.expected_alert)
    assert browser.is_element_present(error_message)

    ok_button = XPath.link().including_text('Ok').inside_of(fixture.expected_alert)
    assert browser.is_element_present(ok_button)
    assert Url(browser.find_element(ok_button).get_attribute('href')).path == '/a_page'

