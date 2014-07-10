


from __future__ import unicode_literals
from __future__ import print_function
from reahl.tofu import test

from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import Browser, XPath
from reahl.sqlalchemysupport import Session

from reahl.doc.examples.tutorial.jobs.jobs import AddressBookUI, Address


class JobsFixture(WebFixture):
    def new_wsgi_app(self):
        return super(JobsFixture, self).new_wsgi_app(site_root=AddressBookUI)
        
    def new_existing_address(self):
        address = Address(name='John Doe', email_address='johndoe@some.org')
        address.save()
        return address

    def new_browser(self):
        return Browser(self.wsgi_app)

    def address_is_listed_as(self, name, email_address, is_new):
        new = ' (new)' if is_new else ''
        return self.browser.is_element_present(XPath.paragraph_containing('%s: %s%s' % (name, email_address, new)))


@test(JobsFixture)
def add_address(fixture):
    """A user can add an address, after which the address is listed."""
    browser = fixture.browser
    
    browser.open('/')
    browser.type(XPath.input_labelled('Name'), 'John')
    browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')

    browser.click(XPath.button_labelled('Save'))
    
    assert fixture.address_is_listed_as('John', 'johndoe@some.org', True)


@test(JobsFixture)
def daily_maintenance(fixture):
    """When daily maintenance is run, all addresses are set to be old."""
    browser = fixture.browser

    fixture.existing_address
    Session.flush()
    assert fixture.existing_address.added_today

    fixture.context.system_control.do_daily_maintenance()

    assert not fixture.existing_address.added_today

