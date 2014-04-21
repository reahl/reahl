


from reahl.tofu import test

from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import Browser, XPath
from reahl.sqlalchemysupport import Session

from reahl.doc.examples.tutorial.jobs.jobs import AddressBookUI, Address


class JobsFixture(WebFixture):
    def new_wsgi_app(self):
        return super(JobsFixture, self).new_wsgi_app(site_root=AddressBookUI)
        
    def new_existing_address(self):
        address = Address(name=u'John Doe', email_address=u'johndoe@some.org')
        address.save()
        return address

    def new_browser(self):
        return Browser(self.wsgi_app)

    def address_is_listed_as(self, name, email_address, is_new):
        new = u' (new)' if is_new else u''
        return self.browser.is_element_present(XPath.paragraph_containing(u'%s: %s%s' % (name, email_address, new)))


@test(JobsFixture)
def add_address(fixture):
    """A user can add an address, after which the address is listed."""
    browser = fixture.browser
    
    browser.open(u'/')
    browser.type(XPath.input_labelled(u'Name'), u'John')
    browser.type(XPath.input_labelled(u'Email'), u'johndoe@some.org')

    browser.click(XPath.button_labelled(u'Save'))
    
    assert fixture.address_is_listed_as(u'John', u'johndoe@some.org', True)


@test(JobsFixture)
def daily_maintenance(fixture):
    """When daily maintenance is run, all addresses are set to be old."""
    browser = fixture.browser

    fixture.existing_address
    Session.flush()
    assert fixture.existing_address.added_today

    fixture.context.system_control.do_daily_maintenance()

    assert not fixture.existing_address.added_today

