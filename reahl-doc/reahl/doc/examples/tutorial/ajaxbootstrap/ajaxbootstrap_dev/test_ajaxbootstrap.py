
# To run this test do:
# pytest --pyargs reahl.doc.examples.tutorial.ajaxbootstrap.ajaxbootstrap_dev.test_ajaxbootstrap
# or
# reahl unit
#

from __future__ import print_function, unicode_literals, absolute_import, division

from reahl.tofu import Fixture
from reahl.webdev.tools import XPath
from reahl.doc.examples.tutorial.ajaxbootstrap.ajaxbootstrap import WidgetRefreshUI

from reahl.web_dev.fixtures import web_fixture
from reahl.sqlalchemysupport_dev.fixtures import sql_alchemy_fixture
from reahl.domain_dev.fixtures import party_account_fixture

class RefreshFixture(Fixture):
    def __init__(self, web_fixture):
        super(RefreshFixture, self).__init__()
        self.web_fixture = web_fixture

    def new_browser(self):
        return self.web_fixture.driver_browser
        
    def new_wsgi_app(self):
        return self.web_fixture.new_wsgi_app(site_root=WidgetRefreshUI, enable_js=True)

    def text_shows_selected(self, expected_selected):
        return self.browser.is_element_present(XPath.paragraph_containing('You selected link number %s' % expected_selected))

refresh_fixture = RefreshFixture.as_pytest_fixture()

#------ Tests

def test_refreshing_widget(web_fixture, refresh_fixture):
    """Clicking on a link, refreshes the displayed text to indicate which link 
       was clicked, without triggering a page load."""

    with web_fixture.context:
        web_fixture.reahl_server.set_app(refresh_fixture.wsgi_app)
        browser = refresh_fixture.browser

        browser.open('/')

        assert refresh_fixture.text_shows_selected(1)
        assert not refresh_fixture.text_shows_selected(3)

        with browser.no_page_load_expected():
            browser.click(XPath.link_with_text('Select 3'))

        assert not refresh_fixture.text_shows_selected(1)
        assert refresh_fixture.text_shows_selected(3)