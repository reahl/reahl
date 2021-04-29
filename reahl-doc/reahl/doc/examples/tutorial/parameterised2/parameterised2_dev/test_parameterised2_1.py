
from reahl.tofu.pytestsupport import with_fixtures
from reahl.browsertools.browsertools import Browser, XPath
from reahl.doc.examples.tutorial.parameterised2.parameterised2 import AddressBookUI
from reahl.web_dev.fixtures import WebFixture


@with_fixtures(WebFixture)
def test_adding_an_address(web_fixture):
    """To add a new address, a user clicks on "Add Address" link on the menu, then supplies the 
       information for the new address and clicks the Save button. Upon successful addition of the
       address, the user is returned to the home page where the new address is now listed."""

    browser = Browser(web_fixture.new_wsgi_app(site_root=AddressBookUI))

    browser.open('/')
    browser.click(XPath.link().with_text('Add'))

    actual_title = browser.title
    assert actual_title == 'Add', 'Expected to be on the Add an address page'

    browser.type(XPath.input_labelled('Name'), 'John Doe')
    browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')

    browser.click(XPath.button_labelled('Save'))

    actual_title = browser.title
    assert actual_title == 'Show', 'Expected to be back on the home page after editing'

    assert browser.is_element_present(XPath.paragraph().including_text('John Doe: johndoe@some.org')), \
           'Expected the newly added address to be listed on the home page'

