


from reahl.tofu import test

from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import Browser, XPath

from reahl.doc.examples.tutorial.migrationexample.migrationexample import AddressBookUI, Address


class MigrateFixture(WebFixture):
    def new_wsgi_app(self):
        return super(MigrateFixture, self).new_wsgi_app(site_root=AddressBookUI)
        
    def new_existing_address(self):
        address = Address(name=u'John Doe', email_address=u'johndoe@some.org')
        address.save()
        return address

    def new_browser(self):
        return Browser(self.wsgi_app)

    def address_is_listed_as(self, name, email_address):
        return self.browser.is_element_present(XPath.paragraph_containing(u'%s: %s' % (name, email_address)))


@test(MigrateFixture)
def add_address(fixture):
    """A user can add an address, after which the address is listed."""
    browser = fixture.browser
    
    browser.open(u'/')
    browser.type(XPath.input_labelled(u'Name'), u'John')
    browser.type(XPath.input_labelled(u'Email'), u'johndoe@some.org')

    browser.click(XPath.button_labelled(u'Save'))
    
    assert fixture.address_is_listed_as(u'John', u'johndoe@some.org')



