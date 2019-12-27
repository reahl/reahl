# Copyright 2019 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.tofu.pytestsupport import with_fixtures
from reahl.tofu import Fixture, scenario

from reahl.webdev.tools import Browser, XPath

from reahl.web.fw import UserInterface, Url
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import P
from reahl.web.layout import PageLayout

from reahl.web_dev.fixtures import WebFixture, BasicPageLayout


@with_fixtures(WebFixture)
def test_bootstrap_default_error_page(web_fixture):
    """Bootstrap HTML5Page has a styled error page by default."""
    class CustomPage(HTML5Page):
        def __init__(self, view):
            super(CustomPage, self).__init__(view)
            self.body.add_child(P(view, 'the first paragraph on the page'))
            
    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(CustomPage)

    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser

    browser.open('/error?error_message=something+went+wrong&error_source_href=/a_page')

    error_alert = browser.find_element(XPath.div().including_class('alert'))
    assert error_alert is browser.find_element(XPath.div()['position() = 1'])

    assert None, 'TODO: the error alert is before anything else in the body'
    import pdb; pdb.set_trace()
    XPath.paragraph().containing_text('the first paragraph on the page')
    XPath.div().including_text('An error occurred:').including_class('alert')
    XPath.paragraph().containing_text('this is the header')
    XPath.any('header')


@with_fixtures(WebFixture)
def test_bootstrap_default_error_page2(web_fixture):
    """Bootstrap HTML5Page has a styled error page by default."""
    class CustomPage(HTML5Page):
        def __init__(self, view):
            super(CustomPage, self).__init__(view)
            self.use_layout(PageLayout())
            self.layout.header.add_child(P(view, 'this is the header'))
            self.layout.contents.add_child(P(view, 'the first paragraph on the page'))
            
    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(CustomPage)

    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser

    browser.open('/error?error_message=something+went+wrong&error_source_href=/a_page')

    assert None, 'TODO: the error alert is the last thing in the header'

    error_alert = browser.find_element(XPath.div().including_class('alert'))
    assert error_alert is browser.find_element(XPath.div()['position() = 1'])


    XPath.paragraph().containing_text('this is the header')
    XPath.any('header')
    import pdb; pdb.set_trace()



# If you .define_page() using a bootstrap.HTML5Page, a nicer error page is displayed, formatted with bootstrap
# scenarios:
#   - the page is layed out with a PageLayout
#   - the page does not use a PageLayout
