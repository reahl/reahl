
# To run this test do:
# pytest --pyargs reahl.doc.examples.howtos.ajaxbootstrap.ajaxbootstrap_dev.test_ajaxbootstrap
# or
# reahl unit
#


from reahl.tofu import Fixture, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.browsertools.browsertools import XPath
from reahl.doc.examples.howtos.ajaxbootstrap.ajaxbootstrap import WidgetRefreshUI

from reahl.web_dev.fixtures import WebFixture


@uses(web_fixture=WebFixture)
class RefreshFixture(Fixture):

    def new_browser(self):
        return self.web_fixture.driver_browser
        
    def new_wsgi_app(self):
        return self.web_fixture.new_wsgi_app(site_root=WidgetRefreshUI, enable_js=True)

    def text_shows_selected(self, expected_selected):
        return self.browser.is_element_present(XPath.paragraph().including_text('You selected link number %s' % expected_selected))


#------ Tests

@with_fixtures(WebFixture, RefreshFixture)
def test_refreshing_widget(web_fixture, refresh_fixture):
    """Clicking on a link, refreshes the displayed text to indicate which link 
       was clicked, without triggering a page load."""


    web_fixture.reahl_server.set_app(refresh_fixture.wsgi_app)
    browser = refresh_fixture.browser

    browser.open('/')

    assert refresh_fixture.text_shows_selected(1)
    assert not refresh_fixture.text_shows_selected(3)

    with browser.no_page_load_expected():
        browser.click(XPath.link().with_text('Select 3'))

    assert not refresh_fixture.text_shows_selected(1)
    assert refresh_fixture.text_shows_selected(3)
