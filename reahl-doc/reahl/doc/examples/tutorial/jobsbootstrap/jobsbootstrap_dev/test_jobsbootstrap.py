


from reahl.tofu import Fixture, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.browsertools.browsertools import Browser, XPath
from reahl.sqlalchemysupport import Session

from reahl.doc.examples.tutorial.jobsbootstrap.jobsbootstrap import AddressBookUI, Address

from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture
from reahl.dev.fixtures import ReahlSystemFixture
from reahl.web_dev.fixtures import WebFixture


@uses(web_fixture=WebFixture)
class JobsFixture(Fixture):

    def new_wsgi_app(self):
        return self.web_fixture.new_wsgi_app(site_root=AddressBookUI)

    def new_existing_address(self):
        address = Address(name='John Doe', email_address='johndoe@some.org')
        address.save()
        return address

    def new_browser(self):
        return Browser(self.wsgi_app)

    def address_is_listed_as(self, name, email_address, is_new):
        new = ' (new)' if is_new else ''
        return self.browser.is_element_present(XPath.paragraph().including_text('%s: %s%s' % (name, email_address, new)))


@with_fixtures(WebFixture, JobsFixture)
def test_add_address(web_fixture, jobs_fixture):
    """A user can add an address, after which the address is listed."""
    browser = jobs_fixture.browser

    browser.open('/')
    browser.type(XPath.input_labelled('Name'), 'John')
    browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')

    browser.click(XPath.button_labelled('Save'))

    assert jobs_fixture.address_is_listed_as('John', 'johndoe@some.org', True)


@with_fixtures(ReahlSystemFixture, JobsFixture)
def test_daily_maintenance(reahl_system_fixture, jobs_fixture):
    """When daily maintenance is run, all addresses are set to be old."""

    
    jobs_fixture.existing_address
    Session.flush()
    assert jobs_fixture.existing_address.added_today

    reahl_system_fixture.context.system_control.do_daily_maintenance()

    assert not jobs_fixture.existing_address.added_today


@with_fixtures(SqlAlchemyFixture)
def demo_setup(sql_alchemy_fixture):
    sql_alchemy_fixture.commit = True
    
    Session.add(Address(name='John Doe', email_address='johndoe@some.org'))
    Session.add(Address(name='Jane Johnson', email_address='janejohnson@some.org'))
    Session.add(Address(name='Jack Black', email_address='jackblack@some.org'))


