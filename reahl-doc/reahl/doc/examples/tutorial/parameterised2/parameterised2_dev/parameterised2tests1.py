from reahl.tofu import test

from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import Browser, XPath

from reahl.doc.examples.tutorial.parameterised2.parameterised2 import AddressBookUI, Address


@test(WebFixture)
def adding_an_address(fixture):
    """To add a new address, a user clicks on "Add Address" link on the menu, then supplies the 
       information for the new address and clicks the Save button. Upon successful addition of the
       address, the user is returned to the home page where the new address is now listed."""

    browser = Browser(fixture.new_wsgi_app(site_root=AddressBookUI))

    browser.open(u'/')
    browser.click(XPath.link_with_text(u'Add an address'))

    actual_title = browser.title
    assert actual_title == u'Add an address', u'Expected to be on the Add an address page'

    browser.type(XPath.input_labelled(u'Name'), u'John Doe')
    browser.type(XPath.input_labelled(u'Email'), u'johndoe@some.org')
    
    browser.click(XPath.button_labelled(u'Save'))
    
    actual_title = browser.title
    assert actual_title == u'Addresses', u'Expected to be back on the home page after editing'
            
    assert browser.is_element_present(XPath.paragraph_containing(u'John Doe: johndoe@some.org')), \
           u'Expected the newly added address to be listed on the home page'

