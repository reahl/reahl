
# To run this test do:
# nosetests -F reahl.webdev.fixtures:BrowserSetup -s --nologcapture reahl/doc_dev/tutorialtests/pagertests.py
#



from __future__ import unicode_literals
from __future__ import print_function
from reahl.tofu import test
from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import XPath
from reahl.doc.examples.tutorial.pager.pager import AddressBookUI


class PagingFixture(WebFixture):
    def new_browser(self):
        return self.driver_browser
        
    def new_wsgi_app(self):
        return super(PagingFixture, self).new_wsgi_app(site_root=AddressBookUI, enable_js=True)

    def is_email_listed(self, email):
        return self.browser.is_element_present(XPath.paragraph_containing(email))


@test(PagingFixture)
def paging(fixture):
    """Clicking on a different page in the pager changes the addresses listed without triggering a page load."""

    fixture.reahl_server.set_app(fixture.wsgi_app)
    browser = fixture.browser

    browser.open('/')
    
    assert fixture.is_email_listed('friend0@some.org')
    assert not fixture.is_email_listed('friend9@some.org')

    with browser.no_page_load_expected():
        browser.click(XPath.link_with_text('2'))

    assert not fixture.is_email_listed('friend0@some.org')
    assert fixture.is_email_listed('friend9@some.org')




