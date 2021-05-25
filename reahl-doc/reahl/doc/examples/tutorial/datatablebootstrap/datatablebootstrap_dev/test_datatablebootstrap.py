
from reahl.tofu import Fixture, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.browsertools.browsertools import Browser, XPath

from reahl.doc.examples.tutorial.datatablebootstrap.datatablebootstrap import AddressBookUI, Address

from reahl.web_dev.fixtures import WebFixture


@uses(web_fixture=WebFixture)
class DataTableExampleFixture(Fixture):

    def new_browser(self):
        return Browser(self.web_fixture.new_wsgi_app(site_root=AddressBookUI))

    def create_addresses(self):
        addresses = [Address(name='friend %s' % i, email_address='friend%s@some.org' % i, zip_code=i) for i in list(range(1, 201))]
        for address in addresses:
            address.save()

    def is_on_edit_page_for(self, address_name):
        return self.browser.title == 'Edit %s' % address_name

    def address_is_listed_as(self, name):
        return self.browser.is_element_present(XPath.table_cell().with_text(name))

    def number_of_rows_in_table(self):
        return len(self.browser.xpath('//table/tbody/tr'))

    def heading_link_for_column(self, column_heading):
        return '//table/thead/tr/th/a/span[text()="%s"]/..' % column_heading


@with_fixtures(WebFixture, DataTableExampleFixture)
def demo_setup(sql_alchemy_fixture, data_table_example_fixture):
    sql_alchemy_fixture.commit = True

    data_table_example_fixture.create_addresses()


@with_fixtures(WebFixture, DataTableExampleFixture)
def test_editing_an_address(web_fixture, data_table_example_fixture):
    """To edit an existing address, a user clicks on the "Edit" link next to the chosen Address
       on the "Addresses" page. The user is then taken to an "Edit" View for the chosen Address and
       can change the name or email address. Upon clicking the "Update" Button, the user is sent back
       to the "Addresses" page where the changes are visible."""


    fixture = data_table_example_fixture
    all_addresses = fixture.create_addresses()
    browser = fixture.browser

    original_address_name = 'friend 7'   #choose the seventh address to edit

    browser.open('/')
    browser.click(XPath.link().with_text('Edit').inside_of(XPath.table_row()[7]))

    assert fixture.is_on_edit_page_for(original_address_name)
    browser.type(XPath.input_labelled('Name'), 'John Doe-changed')
    browser.type(XPath.input_labelled('Email'), 'johndoe@some.changed.org')
    browser.click(XPath.button_labelled('Update'))

    assert fixture.address_is_listed_as('John Doe-changed')
    assert fixture.address_is_listed_as('johndoe@some.changed.org')
    assert not fixture.address_is_listed_as(original_address_name)


@with_fixtures(WebFixture, DataTableExampleFixture)
def test_pageable_table(web_fixture, data_table_example_fixture):
    """If there is a large dataset, the user can page through it, receiving only a managable number of items
       at a time."""


    fixture = data_table_example_fixture
    fixture.create_addresses()
    browser = fixture.browser

    browser.open('/')

    assert fixture.number_of_rows_in_table() == 10
    assert fixture.address_is_listed_as('friend 1')
    assert not fixture.address_is_listed_as('friend 11')

    browser.click(XPath.link().with_text('2'))

    assert fixture.number_of_rows_in_table() == 10
    assert fixture.address_is_listed_as('friend 11')
    assert not fixture.address_is_listed_as('friend 21')


@with_fixtures(WebFixture, DataTableExampleFixture)
def test_sorting_by_column(web_fixture, data_table_example_fixture):
    """The user can sort the table differently, by clicking on links in the heading of a sortable
       column."""

    
    fixture = data_table_example_fixture
    fixture.create_addresses()
    browser = fixture.browser

    browser.open('/')

    assert fixture.address_is_listed_as('friend 1') # Initially data is sorted in the order given
    assert fixture.address_is_listed_as('friend 2')
    assert fixture.address_is_listed_as('friend 3')
    assert fixture.address_is_listed_as('friend 4')
    assert fixture.address_is_listed_as('friend 5')
    assert fixture.address_is_listed_as('friend 6')
    assert fixture.address_is_listed_as('friend 7')
    assert fixture.address_is_listed_as('friend 8')
    assert fixture.address_is_listed_as('friend 9')
    assert fixture.address_is_listed_as('friend 10')

    browser.click(fixture.heading_link_for_column('Zip'))# Ascending sort
    browser.click(fixture.heading_link_for_column('Zip'))# Another click sorts it descending

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
    

