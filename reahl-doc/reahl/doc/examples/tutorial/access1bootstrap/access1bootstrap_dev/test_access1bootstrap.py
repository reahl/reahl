
# To run this test do:
# pytest --pyargs reahl.doc.examples.tutorial.access1bootstrap.access1bootstrap_dev.test_access1bootstrap
#
# To set up a demo database for playing with, do:
# pytest -o python_functions=demo_setup --pyargs reahl.doc.examples.tutorial.access1bootstrap.access1bootstrap_dev.test_access1bootstrap

from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.tofu import scenario, Fixture, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.sqlalchemysupport import Session


from reahl.doc.examples.tutorial.access1bootstrap.access1bootstrap import AddressBook, Address
from reahl.domain.systemaccountmodel import EmailAndPasswordSystemAccount

from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture
from reahl.web_dev.fixtures import WebFixture2

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
    with sql_alchemy_fixture.context:
        access_domain_fixture.address_book
        access_domain_fixture.account
        access_domain_fixture.other_account
        access_domain_fixture.other_address_book


@with_fixtures(SqlAlchemyFixture, AccessDomainFixture)
def test_separate_address_books(sql_alchemy_fixture, access_domain_fixture):
    """An Address is created in a particular AddressBook, which is owned by a SystemAccount."""

    with sql_alchemy_fixture.context:
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

    with sql_alchemy_fixture.context:
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

    with sql_alchemy_fixture.context:
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

    with sql_alchemy_fixture.context:
        account = access_domain_fixture.account
        address_book = access_domain_fixture.address_book
        other_address_book = access_domain_fixture.other_address_book

        assert address_book.collaborators_can_be_added_by(account)
        assert not other_address_book.collaborators_can_be_added_by(account)


