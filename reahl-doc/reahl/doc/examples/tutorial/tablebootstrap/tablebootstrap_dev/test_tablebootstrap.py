

from reahl.tofu import Fixture, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.browsertools.browsertools import Browser, XPath

from reahl.doc.examples.tutorial.tablebootstrap.tablebootstrap import AddressBookUI, Address

from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture
from reahl.web_dev.fixtures import WebFixture


@uses(web_fixture=WebFixture)
class TableExampleFixture(Fixture):

    def new_browser(self):
        return Browser(self.web_fixture.new_wsgi_app(site_root=AddressBookUI))

    def create_addresses(self):
        addresses = [Address(name='friend %s' % i, email_address='friend%s@some.org' % i) for i in list(range(1, 21))]
        for address in addresses:
            address.save()
        return addresses

    def is_on_edit_page_for(self, address_name):
        return self.browser.title == 'Edit %s' % address_name

    def is_on_home_page(self):
        return self.browser.title == 'Addresses'

    def address_is_listed_as(self, name):
        return self.browser.is_element_present(XPath.table_cell().with_text(name))


@with_fixtures(SqlAlchemyFixture, TableExampleFixture)
def demo_setup(sql_alchemy_fixture, fixture):
    sql_alchemy_fixture.commit = True

    fixture.create_addresses()


@with_fixtures(WebFixture, TableExampleFixture)
def test_editing_an_address(web_fixture, fixture):
    """To edit an existing address, a user clicks on the "Edit" link next to the chosen Address
       on the "Addresses" page. The user is then taken to an "Edit" View for the chosen Address and
       can change the name or email address. Upon clicking the "Update" Button, the user is sent back
       to the "Addresses" page where the changes are visible."""

    all_addresses = fixture.create_addresses()    #create some data to play with

    original_address_name = 'friend 7'   #choose the seventh address to edit

    fixture.browser.open('/')
    fixture.browser.click(XPath.link().with_text('Edit').inside_of(XPath.table_row()[7]))

    assert fixture.is_on_edit_page_for(original_address_name)
    fixture.browser.type(XPath.input_labelled('Name'), 'John Doe-changed')
    fixture.browser.type(XPath.input_labelled('Email'), 'johndoe@some.changed.org')
    fixture.browser.click(XPath.button_labelled('Update'))

    assert fixture.is_on_home_page()
    assert fixture.address_is_listed_as('John Doe-changed')
    assert fixture.address_is_listed_as('johndoe@some.changed.org')
    assert not fixture.address_is_listed_as(original_address_name)


@with_fixtures(WebFixture, TableExampleFixture)
def test_deleting_several_address(web_fixture, fixture):
    """To delete several address, a user "checks" the box next to each of the Addresses
       on the "Addresses" page she wants to delete. Upon clicking the "Delete Selected" Button, the page
       refreshes, and the remaining addresses appear."""

    fixture.create_addresses()    #create some data to play with


    web_fixture.reahl_server.set_app(web_fixture.new_wsgi_app(site_root=AddressBookUI))

    fixture.browser = web_fixture.driver_browser
    fixture.browser.open('/')

    name_of_address_1 = 'friend 1'
    name_of_address_13 = 'friend 13'
    name_of_address_20 = 'friend 20'

    assert fixture.address_is_listed_as(name_of_address_1)
    assert fixture.address_is_listed_as(name_of_address_13)
    assert fixture.address_is_listed_as(name_of_address_20)
   
    fixture.browser.click(XPath.checkbox().inside_of(XPath.table_row()[1].inside_of(XPath.table_body())))
    fixture.browser.click(XPath.checkbox().inside_of(XPath.table_row()[13].inside_of(XPath.table_body())))
    fixture.browser.click(XPath.checkbox().inside_of(XPath.table_row()[20].inside_of(XPath.table_body())))
    fixture.browser.click(XPath.button_labelled('Delete Selected'))

    assert fixture.is_on_home_page()
    assert not fixture.address_is_listed_as(name_of_address_1)
    assert not fixture.address_is_listed_as(name_of_address_13)
    assert not fixture.address_is_listed_as(name_of_address_20)
