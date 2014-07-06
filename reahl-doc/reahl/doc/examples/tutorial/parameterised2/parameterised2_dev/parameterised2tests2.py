from __future__ import unicode_literals
from __future__ import print_function
from reahl.tofu import test

from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import Browser, XPath

from reahl.doc.examples.tutorial.parameterised2.parameterised2 import AddressBookUI, Address


class AddressAppFixture(WebFixture):
    def new_browser(self):
        return Browser(self.new_wsgi_app(site_root=AddressBookUI))
        
    def new_existing_address(self):
        address = Address(name='John Doe', email_address='johndoe@some.org')
        address.save()
        return address

    def is_on_home_page(self):
        return self.browser.title == 'Addresses'
        
    def is_on_add_page(self):
        return self.browser.title == 'Add an address'

    def is_on_edit_page_for(self, address):
        return self.browser.title == 'Edit %s' % address.name

    def address_is_listed_as(self, name, email_address):
        return self.browser.is_element_present(XPath.paragraph_containing('%s: %s' % (name, email_address)))


@test(AddressAppFixture)
def adding_an_address(fixture):
    """To add a new address, a user clicks on "Add Address" link on the menu, then supplies the 
       information for the new address and clicks the Save button. Upon success addition of the
       address, the user is returned to the home page where the new address is now listed."""

    browser = fixture.browser

    browser.open('/')
    browser.click(XPath.link_with_text('Add an address'))

    assert fixture.is_on_add_page()
    browser.type(XPath.input_labelled('Name'), 'John Doe')
    browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')
    browser.click(XPath.button_labelled('Save'))
    
    assert fixture.is_on_home_page()
    assert fixture.address_is_listed_as('John Doe', 'johndoe@some.org') 

@test(AddressAppFixture)
def editing_an_address(fixture):
    """To edit an existing address, a user clicks on the "Edit" button next to the chosen Address
       on the "Addresses" page. The user is then taken to an "Edit" View for the chosen Address and 
       can change the name or email address. Upon clicking the "Update" Button, the user is sent back 
       to the "Addresses" page where the changes are visible."""

    browser = fixture.browser
    existing_address = fixture.existing_address
    
    browser.open('/')
    browser.click(XPath.button_labelled('Edit'))

    assert fixture.is_on_edit_page_for(existing_address)
    browser.type(XPath.input_labelled('Name'), 'John Doe-changed')
    browser.type(XPath.input_labelled('Email'), 'johndoe@some.changed.org')
    browser.click(XPath.button_labelled('Update'))
    
    assert fixture.is_on_home_page()
    assert fixture.address_is_listed_as('John Doe-changed', 'johndoe@some.changed.org') 
                

