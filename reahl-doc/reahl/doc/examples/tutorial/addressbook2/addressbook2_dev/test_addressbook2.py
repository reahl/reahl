# To run this test do:
# pytest --pyargs reahl.doc.examples.tutorial.addressbook2.addressbook2_dev.test_addressbook2
# or
# reahl unit
#
# To set up a demo database for playing with, do:
# pytest -o python_functions=demo_setup --pyargs reahl.doc.examples.tutorial.addressbook2.addressbook2_dev.test_addressbook2
# or
# reahl demosetup

from __future__ import print_function, unicode_literals, absolute_import, division

from reahl.tofu import Fixture
from reahl.sqlalchemysupport import Session
from reahl.webdev.tools import Browser

from reahl.doc.examples.tutorial.addressbook2.addressbook2 import Address

from reahl.sqlalchemysupport_dev.fixtures import sql_alchemy_fixture


def demo_setup(sql_alchemy_fixture):
    sql_alchemy_fixture.commit = True
    with sql_alchemy_fixture.context:
        Address(email_address='friend1@some.org', name='Friend1').save()
        Address(email_address='friend2@some.org', name='Friend2').save()
        Address(email_address='friend3@some.org', name='Friend3').save()
        Address(email_address='friend4@some.org', name='Friend4').save()
