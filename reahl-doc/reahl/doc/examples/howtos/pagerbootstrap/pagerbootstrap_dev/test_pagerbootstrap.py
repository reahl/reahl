
# To run this test do:
# pytest -s --pyargs reahl.doc.examples.howtos.pagerbootstrap.pagerbootstrap_dev.test_pagerbootstrap
#

from reahl.tofu import Fixture, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.browsertools.browsertools import XPath
from reahl.doc.examples.howtos.pagerbootstrap.pagerbootstrap import AddressBookUI

from reahl.web_dev.fixtures import WebFixture


@uses(web_fixture=WebFixture)
class PagingFixture(Fixture):

    def new_browser(self):
        return self.web_fixture.driver_browser
        
    def new_wsgi_app(self):
        return self.web_fixture.new_wsgi_app(site_root=AddressBookUI, enable_js=True)

    def is_email_listed(self, email):
        return self.browser.is_element_present(XPath.paragraph().including_text(email))


@with_fixtures(WebFixture, PagingFixture)
def test_paging(web_fixture, paging_fixture):
    """Clicking on a different page in the pager changes the addresses listed without triggering a page load."""

    web_fixture.reahl_server.set_app(paging_fixture.wsgi_app)
    browser = paging_fixture.browser

    browser.open('/')

    assert paging_fixture.is_email_listed('friend0@some.org')
    assert not paging_fixture.is_email_listed('friend9@some.org')

    with browser.no_page_load_expected():
        browser.click(XPath.link().with_text('2'))

    assert not paging_fixture.is_email_listed('friend0@some.org')
    assert paging_fixture.is_email_listed('friend9@some.org')

