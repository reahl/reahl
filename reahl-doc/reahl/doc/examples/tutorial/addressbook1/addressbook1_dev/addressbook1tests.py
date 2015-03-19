
from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.tofu import test, set_up, scenario

from reahl.sqlalchemysupport import Session

from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import Browser

from reahl.doc.examples.tutorial.addressbook1.addressbook1 import Address

# To set up a demo database for playing with, do:
# nosetests -F reahl.webdev.fixtures:BrowserSetup --with-setup-fixture=reahl.doc.examples.tutorial.addressbook1.addressbook1_dev.addressbook1tests:DemoFixture -s --nologcapture
# or
# reahl demosetup


class AddressFixture(WebFixture):
    def new_browser(self):
        return Browser(self.new_wsgi_app(site_root=AddressBookUI))
        
    def do_demo_setup(self):
        DemoFixture().do_demo_setup()


class DemoFixture(AddressFixture):
    commit=True
    @set_up
    def do_demo_setup(self):

        Address(email_address='friend1@some.org', name='Friend1').save()
        Address(email_address='friend2@some.org', name='Friend2').save()
        Address(email_address='friend3@some.org', name='Friend3').save()
        Address(email_address='friend4@some.org', name='Friend4').save()

        Session.flush()
        Session.commit()

