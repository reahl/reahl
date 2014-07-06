from __future__ import unicode_literals
from __future__ import print_function
from reahl.tofu import test

from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import XPath

from reahl.doc.examples.tutorial.parameterised2.parameterised2 import AddressBookUI, Address


class AddressAppErrorFixture(WebFixture):
    def new_wsgi_app(self):
        return super(AddressAppErrorFixture, self).new_wsgi_app(site_root=AddressBookUI, enable_js=True)
        
    def new_existing_address(self):
        address = Address(name='John Doe', email_address='johndoe@some.org')
        address.save()
        return address

    def error_is_displayed(self, text):
        return self.driver_browser.is_element_present(XPath.error_label_containing(text))


@test(AddressAppErrorFixture)
def edit_errors(fixture):
    """Email addresses on the Edit an address page have to be valid email addresses."""
    fixture.reahl_server.set_app(fixture.wsgi_app)
    browser = fixture.driver_browser
    existing_address = fixture.existing_address # Doing this just creates the Address in the database
    
    browser.open('/')
    browser.click(XPath.button_labelled('Edit'))
    
    browser.type(XPath.input_labelled('Email'), 'invalid email address')

    assert fixture.error_is_displayed('Email should be a valid email address')





