
from __future__ import unicode_literals
from __future__ import print_function


from reahl.tofu import test

from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import Browser, XPath

from reahl.doc.examples.tutorial.componentconfig.componentconfig import AddressBookUI, Address, AddressConfig


class ConfigFixture(WebFixture):
    def new_wsgi_app(self):
        return super(ConfigFixture, self).new_wsgi_app(site_root=AddressBookUI)
        
    def new_existing_address(self):
        address = Address(name='John Doe', email_address='johndoe@some.org')
        address.save()
        return address

    def new_browser(self):
        return Browser(self.wsgi_app)

    def address_is_listed_as(self, name, email_address):
        return self.browser.is_element_present(XPath.paragraph_containing('%s: %s' % (name, email_address)))

    def heading_is_displayed(self):
        return self.browser.is_element_present(XPath.heading_with_text(1, 'Addresses'))


@test(ConfigFixture)
def add_address(fixture):
    """A user can add an address, after which the address is listed."""
    browser = fixture.browser
    
    browser.open('/')
    browser.type(XPath.input_labelled('Name'), 'John')
    browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')

    browser.click(XPath.button_labelled('Save'))
    
    assert fixture.address_is_listed_as('John', 'johndoe@some.org')


@test(ConfigFixture)
def config_was_read_from_file(fixture):
    """The tests are run with config read from an actual config file, not the default config."""
    assert fixture.context.config.componentconfig.showheader == True


@test(ConfigFixture)
def configurable_heading(fixture):
    """Whether the heading is displayed or not, is configurable."""
    browser = fixture.browser
    
    fixture.context.config.componentconfig.showheader = False
    browser.open('/')
    assert not fixture.heading_is_displayed()
    
    fixture.context.config.componentconfig.showheader = True
    browser.open('/')
    assert fixture.heading_is_displayed()


