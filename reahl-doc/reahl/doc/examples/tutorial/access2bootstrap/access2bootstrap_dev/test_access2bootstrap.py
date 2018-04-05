# To run this test do:
# pytest --pyargs reahl.doc.examples.tutorial.access2bootstrap.access2bootstrap_dev.test_access2bootstrap
#
# To set up a demo database for playing with, do:
# pytest -o python_functions=demo_setup --pyargs reahl.doc.examples.tutorial.access2bootstrap.access2bootstrap_dev.test_access2bootstrap

from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.tofu import scenario, Fixture, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.sqlalchemysupport import Session

from reahl.webdev.tools import Browser, XPath

from reahl.doc.examples.tutorial.access2bootstrap.access2bootstrap import AddressBook, Address, AddressBookUI

from reahl.domain.systemaccountmodel import EmailAndPasswordSystemAccount

from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture
from reahl.web_dev.fixtures import WebFixture


@uses(web_fixture=WebFixture)
class AccessUIFixture(Fixture):

    def new_browser(self):
        return Browser(self.web_fixture.new_wsgi_app(site_root=AddressBookUI, enable_js=True))

    def is_on_address_book_page_of(self, email):
        return self.browser.title == 'Address book of %s' % email


class AccessDomainFixture(Fixture):
    password = 'topsecret'

    def new_account(self, email='johndoe@some.org'):
        account = EmailAndPasswordSystemAccount(email=email)
        Session.add(account)
        account.set_new_password(account.email, self.password)
        account.activate()
        return account

    def new_address_book(self, owner=None):
        owner = owner or self.account
        address_book = AddressBook(owner=owner)
        Session.add(address_book)
        return address_book

    def new_other_account(self):
        return self.new_account(email='other@some.org')

    def new_other_address_book(self):
        return self.new_address_book(owner=self.other_account)


@with_fixtures(SqlAlchemyFixture, AccessDomainFixture)
def demo_setup(sql_alchemy_fixture, access_domain_fixture):
    sql_alchemy_fixture.commit = True

    access_domain_fixture.address_book
    john = access_domain_fixture.account
    jane = access_domain_fixture.new_account(email='janedoe@some.org')
    jane_book = access_domain_fixture.new_address_book(owner=jane)
    someone = access_domain_fixture.new_account(email='someone@some.org')
    someone_book = access_domain_fixture.new_address_book(owner=someone)
    someone_else = access_domain_fixture.new_account(email='someoneelse@some.org')
    someone_else_book = access_domain_fixture.new_address_book(owner=someone_else)

    jane_book.allow(john, can_add_addresses=True, can_edit_addresses=True)
    someone_book.allow(john, can_add_addresses=False, can_edit_addresses=True)
    someone_else_book.allow(john, can_add_addresses=False, can_edit_addresses=False)

    Address(address_book=jane_book, email_address='friend1@some.org', name='Friend1').save()
    Address(address_book=jane_book, email_address='friend2@some.org', name='Friend2').save()
    Address(address_book=jane_book, email_address='friend3@some.org', name='Friend3').save()
    Address(address_book=jane_book, email_address='friend4@some.org', name='Friend4').save()

    Address(address_book=someone_book, email_address='friend11@some.org', name='Friend11').save()
    Address(address_book=someone_book, email_address='friend12@some.org', name='Friend12').save()
    Address(address_book=someone_book, email_address='friend13@some.org', name='Friend13').save()
    Address(address_book=someone_book, email_address='friend14@some.org', name='Friend14').save()

    Address(address_book=someone_else_book, email_address='friend21@some.org', name='Friend21').save()
    Address(address_book=someone_else_book, email_address='friend22@some.org', name='Friend22').save()
    Address(address_book=someone_else_book, email_address='friend23@some.org', name='Friend23').save()
    Address(address_book=someone_else_book, email_address='friend24@some.org', name='Friend24').save()


@with_fixtures(SqlAlchemyFixture, AccessDomainFixture)
def test_separate_address_books(sql_alchemy_fixture, access_domain_fixture):
    """An Address is created in a particular AddressBook, which is owned by a SystemAccount."""


    account = access_domain_fixture.account
    address_book = access_domain_fixture.address_book
    other_address_book = access_domain_fixture.other_address_book

    # AddressBooks are owned
    address_book.owner is account
    other_address_book.owner is access_domain_fixture.other_account

    # Addresses live in specific AddressBooks
    assert address_book.addresses == []
    assert other_address_book.addresses == []

    address1 = Address(address_book=address_book, email_address='friend1@some.org', name='Friend1')
    address2 = Address(address_book=address_book, email_address='friend2@some.org', name='Friend2')

    address3 = Address(address_book=other_address_book, email_address='friend3@some.org', name='Friend3')

    for address in [address1, address2, address3]:
        address.save()

    assert address_book.addresses == [address1, address2]
    assert other_address_book.addresses == [address3]


@with_fixtures(SqlAlchemyFixture, AccessDomainFixture)
def test_collaborators(sql_alchemy_fixture, access_domain_fixture):
    """A particular SystemAccount can see its own AddressBooks as well as all the AddressBooks
       it is explicitly allowed to see, but no other AddressBooks."""


    account = access_domain_fixture.account
    address_book = access_domain_fixture.address_book
    other_address_book = access_domain_fixture.other_address_book

    unrelated_account = access_domain_fixture.new_account(email='unrelated@some.org')
    unrelated_address_book = access_domain_fixture.new_address_book(owner=unrelated_account)

    other_address_book.allow(account)

    # Checks to see whether an AddressBook is visible
    assert address_book.is_visible_to(account)
    assert other_address_book.is_visible_to(account)
    assert not unrelated_address_book.is_visible_to(account)

    # Getting a list of visible AddressBooks (for populating the screen)
    books = AddressBook.address_books_visible_to(account)
    assert set(books) == {address_book, other_address_book}


@with_fixtures(SqlAlchemyFixture, AccessDomainFixture)
def test_collaborator_rights(sql_alchemy_fixture, access_domain_fixture):
    """When allowing an account to see another's AddressBook, the rights it has to the AddressBook are specified."""


    account = access_domain_fixture.account
    address_book = access_domain_fixture.address_book
    other_address_book = access_domain_fixture.other_address_book

    # Case: defaults
    other_address_book.allow(account)
    assert not other_address_book.can_be_edited_by(account)
    assert not other_address_book.can_be_added_to_by(account)

    # Case: rights specified
    other_address_book.allow(account, can_edit_addresses=True, can_add_addresses=True)
    assert other_address_book.can_be_edited_by(account)
    assert other_address_book.can_be_added_to_by(account)


@with_fixtures(SqlAlchemyFixture, AccessDomainFixture)
def test_adding_collaborators(sql_alchemy_fixture, access_domain_fixture):
    """The owner of an AddressBook may add collaborators to it."""


    account = access_domain_fixture.account
    address_book = access_domain_fixture.address_book
    other_address_book = access_domain_fixture.other_address_book

    assert address_book.collaborators_can_be_added_by(account)
    assert not other_address_book.collaborators_can_be_added_by(account)


@with_fixtures(WebFixture, AccessDomainFixture, AccessUIFixture)
def test_logging_in(web_fixture, access_domain_fixture, access_ui_fixture):
    """A user first sees only a login screen on the home page; after logging in,
       all the address books visible to the user appear."""


    browser = access_ui_fixture.browser
    account = access_domain_fixture.account
    address_book = access_domain_fixture.address_book

    other_address_book = access_domain_fixture.other_address_book
    other_address_book.allow(account)

    browser.open('/')
    browser.type(XPath.input_labelled('Email'), 'johndoe@some.org')
    browser.type(XPath.input_labelled('Password'), access_domain_fixture.password)
    browser.click(XPath.button_labelled('Log in'))

    assert browser.is_element_present(XPath.link_with_text('Address book of johndoe@some.org'))
    assert browser.is_element_present(XPath.link_with_text('Address book of other@some.org'))


@with_fixtures(WebFixture, AccessDomainFixture, AccessUIFixture)
def test_edit_and_add_own(web_fixture, access_domain_fixture, access_ui_fixture):
    """The owner of an AddressBook can add and edit Addresses to the owned AddressBook."""


    browser = access_ui_fixture.browser
    fixture = access_domain_fixture
    account = fixture.account
    address_book = fixture.address_book

    web_fixture.log_in(browser=browser, system_account=account)
    browser.open('/')

    browser.click(XPath.link_with_text('Address book of johndoe@some.org'))

    # add
    browser.click(XPath.link_with_text('Add address'))
    browser.type(XPath.input_labelled('Name'), 'Someone')
    browser.type(XPath.input_labelled('Email'), 'someone@some.org')
    browser.click(XPath.button_labelled('Save'))

    assert browser.is_element_present(XPath.paragraph_containing('Someone: someone@some.org'))

    # edit
    browser.click(XPath.button_labelled('Edit'))
    browser.type(XPath.input_labelled('Name'), 'Else')
    browser.type(XPath.input_labelled('Email'), 'else@some.org')
    browser.click(XPath.button_labelled('Update'))

    assert browser.is_element_present(XPath.paragraph_containing('Else: else@some.org'))


# ------- Tests added for access control

@with_fixtures(WebFixture, AccessDomainFixture, AccessUIFixture)
def test_add_collaborator(web_fixture, access_domain_fixture, access_ui_fixture):
    """A user may add other users as collaborators to his address book, specifying the privileges in the process."""


    browser = access_ui_fixture.browser
    address_book = access_domain_fixture.address_book
    account = access_domain_fixture.account

    other_address_book = access_domain_fixture.other_address_book
    other_account = access_domain_fixture.other_account

    web_fixture.log_in(browser=browser, system_account=account)
    browser.open('/')

    assert address_book not in AddressBook.address_books_visible_to(other_account)
    assert not address_book.can_be_edited_by(other_account)
    assert not address_book.can_be_added_to_by(other_account)

    browser.click(XPath.link_with_text('Address book of johndoe@some.org'))
    browser.click(XPath.link_with_text('Add collaborator'))

    browser.select(XPath.select_labelled('Choose collaborator'), 'other@some.org')
    browser.click(XPath.input_labelled('May add new addresses'))
    browser.click(XPath.input_labelled('May edit existing addresses'))

    browser.click(XPath.button_labelled('Share'))

    assert access_ui_fixture.is_on_address_book_page_of('johndoe@some.org')

    assert address_book in AddressBook.address_books_visible_to(other_account)
    assert address_book.can_be_edited_by(other_account)
    assert address_book.can_be_added_to_by(other_account)

