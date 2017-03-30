


from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.tofu import Fixture

from reahl.webdev.tools import Browser, XPath
from reahl.sqlalchemysupport import Session

from reahl.doc.examples.tutorial.jobsbootstrap.jobsbootstrap import AddressBookUI, Address

from reahl.web_dev.fixtures import web_fixture
from reahl.sqlalchemysupport_dev.fixtures import sql_alchemy_fixture
from reahl.domain_dev.fixtures import party_account_fixture

class JobsFixture(Fixture):
    def __init__(self, web_fixture):
        super(JobsFixture, self).__init__()
        self.web_fixture = web_fixture

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
        return self.browser.is_element_present(XPath.paragraph_containing('%s: %s%s' % (name, email_address, new)))

jobs_fixture = JobsFixture.as_pytest_fixture()


def test_add_address(web_fixture, jobs_fixture):
    """A user can add an address, after which the address is listed."""
    with web_fixture.context:
        browser = jobs_fixture.browser

        browser.open('/')
        browser.type(XPath.input_labelled('Name'), 'John')
        browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')

        browser.click(XPath.button_labelled('Save'))

        assert jobs_fixture.address_is_listed_as('John', 'johndoe@some.org', True)


def test_daily_maintenance(sql_alchemy_fixture, jobs_fixture):
    """When daily maintenance is run, all addresses are set to be old."""

    with sql_alchemy_fixture.context:
        jobs_fixture.existing_address
        Session.flush()
        assert jobs_fixture.existing_address.added_today

        sql_alchemy_fixture.context.system_control.do_daily_maintenance()

        assert not jobs_fixture.existing_address.added_today


def demo_setup(sql_alchemy_fixture):
    sql_alchemy_fixture.commit = True
    with sql_alchemy_fixture.context:
        Session.add(Address(name='John Doe', email_address='johndoe@some.org'))
        Session.add(Address(name='Jane Johnson', email_address='janejohnson@some.org'))
        Session.add(Address(name='Jack Black', email_address='jackblack@some.org'))


