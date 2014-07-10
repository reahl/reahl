
# To run this test do:
# nosetests -F reahl.webdev.fixtures:BrowserSetup -s --nologcapture reahl/doc_dev/tutorialtests/accesstests1.py


from __future__ import unicode_literals
from __future__ import print_function
from reahl.tofu import test
from reahl.web_dev.fixtures import WebFixture
from reahl.systemaccountmodel import EmailAndPasswordSystemAccount

from reahl.doc.examples.tutorial.access1.access1 import AddressBook, Address


class AccessFixture(WebFixture):
    password = 'bobbejaan'

    def new_account(self, email='johndoe@some.org'):
        account = EmailAndPasswordSystemAccount(email=email)
        account.set_new_password(account.email, self.password)
        account.activate()
        return account

    def new_address_book(self, owner=None):
        owner = owner or self.account
        return AddressBook(owner=owner)

    def new_other_account(self):
        return self.new_account(email='other@some.org')
        
    def new_other_address_book(self):
        return self.new_address_book(owner=self.other_account)



@test(AccessFixture)
def separate_address_books(fixture):
    """An Address is created in a particular AddressBook, which is owned by a SystemAccount."""
    
    account = fixture.account
    address_book = fixture.address_book
    other_address_book = fixture.other_address_book

    # AddressBooks are owned
    address_book.owner is account
    other_address_book.owner is fixture.other_account

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


@test(AccessFixture)
def collaborators(fixture):
    """A particular SystemAccount can see its own AddressBooks as well as all the AddressBooks
       it is explicitly allowed to see, but no other AddressBooks."""
    
    account = fixture.account
    address_book = fixture.address_book
    other_address_book = fixture.other_address_book

    unrelated_account = fixture.new_account(email='unrelated@some.org')
    unrelated_address_book = fixture.new_address_book(owner=unrelated_account)
    
    other_address_book.allow(account)
    
    # Checks to see whether an AddressBook is visible
    assert address_book.is_visible_to(account)
    assert other_address_book.is_visible_to(account)
    assert not unrelated_address_book.is_visible_to(account)

    # Getting a list of visible AddressBooks (for populating the screen)
    books = AddressBook.address_books_visible_to(account)
    assert set(books) == {address_book, other_address_book}


@test(AccessFixture)
def collaborator_rights(fixture):
    """When allowing an account to see another's AddressBook, the rights it has to the AddressBook are specified."""

    account = fixture.account
    address_book = fixture.address_book
    other_address_book = fixture.other_address_book

    # Case: defaults
    other_address_book.allow(account)
    assert not other_address_book.can_be_edited_by(account)
    assert not other_address_book.can_be_added_to_by(account)

    # Case: rights specified
    other_address_book.allow(account, can_edit_addresses=True, can_add_addresses=True)
    assert other_address_book.can_be_edited_by(account)
    assert other_address_book.can_be_added_to_by(account)


@test(AccessFixture)
def adding_collaborators(fixture):
    """The owner of an AddressBook may add collaborators to it."""

    account = fixture.account
    address_book = fixture.address_book
    other_address_book = fixture.other_address_book

    assert address_book.collaborators_can_be_added_by(account)
    assert not other_address_book.collaborators_can_be_added_by(account)



