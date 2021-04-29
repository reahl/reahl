
from reahl.tofu import Fixture, uses
from reahl.tofu.pytestsupport import with_fixtures
from reahl.browsertools.browsertools import XPath
from reahl.doc.examples.tutorial.parameterised2.parameterised2 import AddressBookUI, Address
from reahl.web_dev.fixtures import WebFixture


@uses(web_fixture=WebFixture)
class AddressAppFixture(Fixture):

    def new_wsgi_app(self):
        return self.web_fixture.new_wsgi_app(site_root=AddressBookUI, enable_js=True)

    def new_existing_address(self):
        address = Address(name='John Doe', email_address='johndoe@some.org')
        address.save()
        return address

    def error_is_displayed(self, text):
        return self.web_fixture.driver_browser.is_element_present(XPath.span().including_text(text))


@with_fixtures(WebFixture, AddressAppFixture)
def test_edit_errors(web_fixture, address_app_fixture):
    """Email addresses on the Edit an address page have to be valid email addresses."""

    web_fixture.reahl_server.set_app(address_app_fixture.wsgi_app)
    browser = web_fixture.driver_browser
    address_app_fixture.new_existing_address()

    browser.open('/')
    browser.click(XPath.button_labelled('Edit'))

    browser.type(XPath.input_labelled('Email'), 'invalid email address')

    assert address_app_fixture.error_is_displayed('Email should be a valid email address')





