from __future__ import unicode_literals
from __future__ import print_function
from reahl.tofu import test

from reahl.web_dev.fixtures import WebFixture

from reahl.webdev.tools import Browser, XPath

from datatable import AddressBookUI, Address


class DataTableExampleFixture(WebFixture):

    def new_browser(self):
        return Browser(self.new_wsgi_app(site_root=AddressBookUI, enable_js=False))

    def new_addresses(self):
        addresses = [Address(name=u'friend %s' % i, email_address=u'friend%s@some.org' % i, zip_code=i) for i in range(1,201)]
        for address in addresses:
            address.save()
        return addresses

    def is_on_edit_page_for(self, address_name):
        return self.browser.title == 'Edit %s' % address_name

    def address_is_listed_as(self, name):
        return self.browser.is_element_present(XPath.table_cell_with_text(name))


class DemoSetup(DataTableExampleFixture):
    commit = True
    def set_up(self):
        super(DemoSetup, self).set_up()
        self.addresses
        self.system_control.commit()


@test(DataTableExampleFixture)
def editing_an_address(fixture):
    """To edit an existing address, a user clicks on the "Edit" link next to the chosen Address
       on the "Addresses" page. The user is then taken to an "Edit" View for the chosen Address and
       can change the name or email address. Upon clicking the "Update" Button, the user is sent back
       to the "Addresses" page where the changes are visible."""

    all_addresses = fixture.addresses    #create some data to play with

    original_address_name = 'friend 104'   #choose the seventh address to edit

    fixture.browser.open('/')
    fixture.browser.click(XPath.link_with_text('Edit', nth=7))

    assert fixture.is_on_edit_page_for(original_address_name)
    fixture.browser.type(XPath.input_labelled('Name'), 'John Doe-changed')
    fixture.browser.type(XPath.input_labelled('Email'), 'johndoe@some.changed.org')
    fixture.browser.click(XPath.button_labelled('Update'))

    assert fixture.address_is_listed_as('John Doe-changed')
    assert fixture.address_is_listed_as('johndoe@some.changed.org')
    assert not fixture.address_is_listed_as(original_address_name)


@test(DataTableExampleFixture)
def deleting_several_address(fixture):
    """To delete several address, a user "checks" the box next to each of the Addresses
       on the "Addresses" page she wants to delete. Upon clicking the "Delete Selected" Button, the page
       refreshes, and the remaining addresses appear."""

    fixture.addresses    #create some data to play with

    fixture.browser.open('/?current_page_number=2')

    # import pdb;pdb.set_trace()
    # fixture.browser.click(XPath.link_with_text('2'))#go to second page

    name_of_address_108 = 'friend 108'
    name_of_address_11  = 'friend 11'
    name_of_address_116 = 'friend 116'

    assert fixture.address_is_listed_as(name_of_address_108)
    assert fixture.address_is_listed_as(name_of_address_11)
    assert fixture.address_is_listed_as(name_of_address_116)

    fixture.browser.click(XPath.checkbox_in_table_row(1))
    fixture.browser.click(XPath.checkbox_in_table_row(3))
    fixture.browser.click(XPath.checkbox_in_table_row(10))
    fixture.browser.click(XPath.button_labelled('Delete Selected'))

    assert not fixture.address_is_listed_as(name_of_address_108)
    assert not fixture.address_is_listed_as(name_of_address_11)
    assert not fixture.address_is_listed_as(name_of_address_116)

    assert fixture.address_is_listed_as('friend 109')
    assert fixture.address_is_listed_as('friend 110')
    assert fixture.address_is_listed_as('friend 111')
    assert fixture.address_is_listed_as('friend 112')
    assert fixture.address_is_listed_as('friend 113')
    assert fixture.address_is_listed_as('friend 114')
    assert fixture.address_is_listed_as('friend 115')
    assert fixture.address_is_listed_as('friend 117')
    assert fixture.address_is_listed_as('friend 118')
    assert fixture.address_is_listed_as('friend 119')


@test(DataTableExampleFixture)
def sorting_by_column(fixture):
    """..."""

    fixture.addresses    #create some data to play with

    fixture.browser.open('/')

    assert fixture.address_is_listed_as('friend 1')
    assert fixture.address_is_listed_as('friend 10')
    assert fixture.address_is_listed_as('friend 100')
    assert fixture.address_is_listed_as('friend 101')
    assert fixture.address_is_listed_as('friend 102')
    assert fixture.address_is_listed_as('friend 103')
    assert fixture.address_is_listed_as('friend 104')
    assert fixture.address_is_listed_as('friend 105')
    assert fixture.address_is_listed_as('friend 106')
    assert fixture.address_is_listed_as('friend 107')

    #fixture.browser.click(XPath.sort_descending_link_for_column('Zip'))
    fixture.browser.open('/?sort_descending=on&sort_column_number=2')

    assert fixture.address_is_listed_as('friend 200')
    assert fixture.address_is_listed_as('friend 199')
    assert fixture.address_is_listed_as('friend 198')
    assert fixture.address_is_listed_as('friend 197')
    assert fixture.address_is_listed_as('friend 196')
    assert fixture.address_is_listed_as('friend 195')
    assert fixture.address_is_listed_as('friend 194')
    assert fixture.address_is_listed_as('friend 193')
    assert fixture.address_is_listed_as('friend 192')
    assert fixture.address_is_listed_as('friend 191')