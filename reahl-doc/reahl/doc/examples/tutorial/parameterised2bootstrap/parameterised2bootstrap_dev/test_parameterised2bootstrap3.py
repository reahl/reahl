
from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.tofu import Fixture

from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import XPath

from reahl.doc.examples.tutorial.parameterised2bootstrap.parameterised2bootstrap import AddressBookUI, Address

from reahl.web_dev.fixtures import web_fixture
from reahl.sqlalchemysupport_dev.fixtures import sql_alchemy_fixture
from reahl.domain_dev.fixtures import party_account_fixture


class AddressAppFixture(Fixture):
    def __init__(self, web_fixture):
        super(AddressAppFixture, self).__init__()
        self.web_fixture = web_fixture

    def new_wsgi_app(self):
        return self.web_fixture.new_wsgi_app(site_root=AddressBookUI, enable_js=True)

    def new_existing_address(self):
        address = Address(name='John Doe', email_address='johndoe@some.org')
        address.save()
        return address

    def error_is_displayed(self, text):
        return self.web_fixture.driver_browser.is_element_present(XPath.span_containing(text))

address_app_fixture = AddressAppFixture.as_pytest_fixture()


def test_edit_errors(web_fixture, address_app_fixture):
    """Email addresses on the Edit an address page have to be valid email addresses."""

    with web_fixture.context:
        web_fixture.reahl_server.set_app(address_app_fixture.wsgi_app)
        browser = web_fixture.driver_browser
        address_app_fixture.new_existing_address()

        browser.open('/')
        browser.click(XPath.button_labelled('Edit'))

        browser.type(XPath.input_labelled('Email'), 'invalid email address')
        browser.press_tab('//input') #tab out so that validation is triggered

        assert address_app_fixture.error_is_displayed('Email should be a valid email address')





