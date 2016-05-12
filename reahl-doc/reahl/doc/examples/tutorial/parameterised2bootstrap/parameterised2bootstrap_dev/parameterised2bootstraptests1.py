
from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.tofu import test

from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import Browser, XPath

from reahl.doc.examples.tutorial.parameterised2bootstrap.parameterised2bootstrap import AddressBookUI

class AddressAppFixture(WebFixture):
    def new_browser(self):
        return Browser(self.new_wsgi_app(site_root=AddressBookUI))

    def new_webconfig(self):
        webconfig = super(AddressAppFixture, self).new_webconfig()
        webconfig.frontend_libraries.enable_experimental_bootstrap()
        return webconfig


@test(AddressAppFixture)
def adding_an_address(fixture):
    """To add a new address, a user clicks on "Add Address" link on the menu, then supplies the 
       information for the new address and clicks the Save button. Upon successful addition of the
       address, the user is returned to the home page where the new address is now listed."""

    browser = fixture.browser

    browser.open('/')
    browser.click(XPath.link_with_text('Add an address'))

    actual_title = browser.title
    assert actual_title == 'Add an address', 'Expected to be on the Add an address page'

    browser.type(XPath.input_labelled('Name'), 'John Doe')
    browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')
    
    browser.click(XPath.button_labelled('Save'))
    
    actual_title = browser.title
    assert actual_title == 'Addresses', 'Expected to be back on the home page after editing'
            
    assert browser.is_element_present(XPath.paragraph_containing('John Doe: johndoe@some.org')), \
           'Expected the newly added address to be listed on the home page'

