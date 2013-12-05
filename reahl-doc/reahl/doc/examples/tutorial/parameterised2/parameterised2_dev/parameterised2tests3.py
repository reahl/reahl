from reahl.tofu import test

from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import XPath

from reahl.doc.examples.tutorial.parameterised2.parameterised2 import AddressBookApp, Address


class AddressAppErrorFixture(WebFixture):
    def new_webapp(self):
        return super(AddressAppErrorFixture, self).new_webapp(site_root=AddressBookApp, enable_js=True)
        
    def new_existing_address(self):
        address = Address(name=u'John Doe', email_address=u'johndoe@some.org')
        address.save()
        return address

    def error_is_displayed(self, text):
        return self.driver_browser.is_element_present(XPath.error_label_containing(text))


@test(AddressAppErrorFixture)
def edit_errors(fixture):
    """Email addresses on the Edit an address page have to be valid email addresses."""
    fixture.reahl_server.set_app(fixture.webapp)
    browser = fixture.driver_browser
    existing_address = fixture.existing_address # Doing this just creates the Address in the database
    
    browser.open(u'/')
    browser.click(XPath.button_labelled(u'Edit'))
    
    browser.type(XPath.input_labelled(u'Email'), u'invalid email address')

    assert fixture.error_is_displayed(u'Email should be a valid email address')





