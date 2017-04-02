
# To run this test do:
# pytest -s --pyargs reahl.doc.examples.tutorial.pagerbootstrap.pagerbootstrap_dev.test_pagerbootstrap
#

from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.tofu import Fixture

from reahl.webdev.tools import XPath
from reahl.doc.examples.tutorial.pagerbootstrap.pagerbootstrap import AddressBookUI

from reahl.web_dev.fixtures import web_fixture
from reahl.sqlalchemysupport_dev.fixtures import sql_alchemy_fixture
from reahl.domain_dev.fixtures import party_account_fixture


class PagingFixture(Fixture):
    def __init__(self, web_fixture):
        super(PagingFixture, self).__init__()
        self.web_fixture = web_fixture
        
    def new_browser(self):
        return self.web_fixture.driver_browser
        
    def new_wsgi_app(self):
        return self.web_fixture.new_wsgi_app(site_root=AddressBookUI, enable_js=True)

    def is_email_listed(self, email):
        return self.browser.is_element_present(XPath.paragraph_containing(email))

paging_fixture = PagingFixture.as_pytest_fixture()


def test_paging(web_fixture, paging_fixture):
    """Clicking on a different page in the pager changes the addresses listed without triggering a page load."""

    with web_fixture.context:
        web_fixture.reahl_server.set_app(paging_fixture.wsgi_app)
        browser = paging_fixture.browser

        browser.open('/')

        assert paging_fixture.is_email_listed('friend0@some.org')
        assert not paging_fixture.is_email_listed('friend9@some.org')

        with browser.no_page_load_expected():
            browser.click(XPath.link_with_text('2'))

        assert not paging_fixture.is_email_listed('friend0@some.org')
        assert paging_fixture.is_email_listed('friend9@some.org')




