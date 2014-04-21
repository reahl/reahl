
from reahl.tofu import test, set_up, scenario

from reahl.sqlalchemysupport import Session, metadata

from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import Browser, XPath

from reahl.doc.examples.tutorial.access.access import AddressBookUI, AddressBook, Collaborator, Address
from reahl.systemaccountmodel import EmailAndPasswordSystemAccount


class AccessFixture(WebFixture):
    def new_browser(self):
        return Browser(self.new_wsgi_app(site_root=AddressBookUI))
        
    password = u'bobbejaan'

    def new_account(self, email=u'johndoe@some.org'):
        account = EmailAndPasswordSystemAccount(email=email)
        account.set_new_password(account.email, self.password)
        account.activate()
        return account

    def new_address_book(self, owner=None):
        owner = owner or self.account
        return AddressBook(owner=owner)

    def new_other_account(self):
        return self.new_account(email=u'other@some.org')
        
    def new_other_address_book(self):
        return self.new_address_book(owner=self.other_account)

    def is_on_address_book_page_of(self, email):
        return self.browser.title == u'Address book of %s' % email

    def do_demo_setup(self):
        DemoFixture().do_demo_setup()

#nosetests -F reahl.webdev.fixtures:BrowserSetup -s --nologcapture reahl/doc_dev/tutorialtests/accesstests.py
#nosetests -F reahl.webdev.fixtures:BrowserSetup --with-setup-fixture=reahl.doc_dev.tutorialtests.accesstests:DemoFixture -s --nologcapture

class DemoFixture(AccessFixture):
    commit=True
    @set_up
    def do_demo_setup(self):
        self.address_book
        john = self.account
        jane = self.new_account(email=u'janedoe@some.org')
        jane_book = self.new_address_book(owner=jane)
        someone = self.new_account(email=u'someone@some.org')
        someone_book = self.new_address_book(owner=someone)
        someone_else = self.new_account(email=u'someoneelse@some.org')
        someone_else_book = self.new_address_book(owner=someone_else)

        jane_book.allow(john, can_add_addresses=True, can_edit_addresses=True)
        someone_book.allow(john, can_add_addresses=False, can_edit_addresses=True)
        someone_else_book.allow(john, can_add_addresses=False, can_edit_addresses=False)
        
        Address(address_book=jane_book, email_address=u'friend1@some.org', name=u'Friend1').save()
        Address(address_book=jane_book, email_address=u'friend2@some.org', name=u'Friend2').save()
        Address(address_book=jane_book, email_address=u'friend3@some.org', name=u'Friend3').save()
        Address(address_book=jane_book, email_address=u'friend4@some.org', name=u'Friend4').save()

        Address(address_book=someone_book, email_address=u'friend11@some.org', name=u'Friend11').save()
        Address(address_book=someone_book, email_address=u'friend12@some.org', name=u'Friend12').save()
        Address(address_book=someone_book, email_address=u'friend13@some.org', name=u'Friend13').save()
        Address(address_book=someone_book, email_address=u'friend14@some.org', name=u'Friend14').save()

        Address(address_book=someone_else_book, email_address=u'friend21@some.org', name=u'Friend21').save()
        Address(address_book=someone_else_book, email_address=u'friend22@some.org', name=u'Friend22').save()
        Address(address_book=someone_else_book, email_address=u'friend23@some.org', name=u'Friend23').save()
        Address(address_book=someone_else_book, email_address=u'friend24@some.org', name=u'Friend24').save()
        Session.flush()
        Session.commit()




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

    address1 = Address(address_book=address_book, email_address=u'friend1@some.org', name=u'Friend1')
    address2 = Address(address_book=address_book, email_address=u'friend2@some.org', name=u'Friend2')

    address3 = Address(address_book=other_address_book, email_address=u'friend3@some.org', name=u'Friend3')

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

    unrelated_account = fixture.new_account(email=u'unrelated@some.org')
    unrelated_address_book = fixture.new_address_book(owner=unrelated_account)
    
    other_address_book.allow(account)
    
    # Checks to see whether an AddressBook is visible
    assert address_book.is_visible_to(account)
    assert other_address_book.is_visible_to(account)
    assert not unrelated_address_book.is_visible_to(account)

    # Getting a list of visible AddressBooks (for populating the screen)
    books = AddressBook.address_books_visible_to(account)
    assert set(books) == set([address_book, other_address_book])


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


@test(AccessFixture)
def logging_in(fixture):
    """A user first sees only a login screen on the home page; after logging in, 
       all the address books visible to the user appear."""
    browser = fixture.browser
    account = fixture.account
    address_book = fixture.address_book

    other_address_book = fixture.other_address_book
    other_address_book.allow(account)

    browser.open(u'/')
    browser.type(XPath.input_labelled(u'Email'), u'johndoe@some.org')
    browser.type(XPath.input_labelled(u'Password'), fixture.password)
    browser.click(XPath.button_labelled(u'Log in'))
    
    assert browser.is_element_present(XPath.link_with_text(u'Address book of johndoe@some.org'))
    assert browser.is_element_present(XPath.link_with_text(u'Address book of other@some.org'))


@test(AccessFixture)
def edit_and_add_own(fixture):
    """The owner of an AddressBook can add and edit Addresses to the owned AddressBook."""
    browser = fixture.browser
    account = fixture.account
    address_book = fixture.address_book

    fixture.log_in(browser=browser, system_account=account)
    browser.open(u'/')
    
    browser.click(XPath.link_with_text(u'Address book of johndoe@some.org'))
    
    # add
    browser.click(XPath.link_with_text(u'Add address'))
    browser.type(XPath.input_labelled(u'Name'), u'Someone')
    browser.type(XPath.input_labelled(u'Email'), u'someone@some.org')
    browser.click(XPath.button_labelled(u'Save'))

    assert browser.is_element_present(XPath.paragraph_containing(u'Someone: someone@some.org'))

    # edit
    browser.click(XPath.button_labelled(u'Edit'))
    browser.type(XPath.input_labelled(u'Name'), u'Else')
    browser.type(XPath.input_labelled(u'Email'), u'else@some.org')
    browser.click(XPath.button_labelled(u'Update'))

    assert browser.is_element_present(XPath.paragraph_containing(u'Else: else@some.org'))
    

# ------- Tests added for access control

@test(AccessFixture)
def see_other(fixture):
    """If allowed, an account may see another account's AddressBook, and could edit or add Addresses, 
       depending on the allowed rights."""
    browser = fixture.browser
    account = fixture.account
    address_book = fixture.address_book

    other_address_book = fixture.other_address_book
    other_address_book.allow(account)
    Address(address_book=other_address_book, email_address=u'friend@some.org', name=u'Friend').save()

    fixture.log_in(browser=browser, system_account=account)
    browser.open(u'/')

    browser.click(XPath.link_with_text(u'Address book of other@some.org'))

    assert browser.is_element_present(XPath.paragraph_containing(u'Friend: friend@some.org'))

    # Case: can only see
    assert not browser.is_element_enabled(XPath.link_with_text(u'Add address'))
    assert not browser.is_element_enabled(XPath.button_labelled(u'Edit'))

    # Case: can edit only
    other_address_book.allow(account, can_edit_addresses=True, can_add_addresses=False)
    browser.refresh()
    assert not browser.is_element_enabled(XPath.link_with_text(u'Add address'))
    assert browser.is_element_enabled(XPath.button_labelled(u'Edit'))

    # Case: can add, and therefor also edit
    other_address_book.allow(account, can_add_addresses=True)
    browser.refresh()
    assert browser.is_element_enabled(XPath.link_with_text(u'Add address'))
    assert browser.is_element_enabled(XPath.button_labelled(u'Edit'))
    
    browser.click(XPath.button_labelled(u'Edit'))
    browser.type(XPath.input_labelled(u'Name'), u'Else')
    browser.type(XPath.input_labelled(u'Email'), u'else@some.org')
    browser.click(XPath.button_labelled(u'Update'))

    assert browser.is_element_present(XPath.paragraph_containing(u'Else: else@some.org'))


@test(AccessFixture)
def edit_other(fixture):
    """If you may only edit (not add) an address, then you may only edit the email address, not the name."""   
    browser = fixture.browser
    account = fixture.account
    address_book = fixture.address_book

    other_address_book = fixture.other_address_book
    other_address_book.allow(account, can_edit_addresses=True, can_add_addresses=True)
    Address(address_book=other_address_book, email_address=u'friend@some.org', name=u'Friend').save()

    fixture.log_in(browser=browser, system_account=account)
    browser.open(u'/')

    browser.click(XPath.link_with_text(u'Address book of other@some.org'))
    browser.click(XPath.button_labelled(u'Edit'))

    # Case: may edit name
    assert browser.is_element_enabled(XPath.input_labelled(u'Name'))
    assert browser.is_element_enabled(XPath.input_labelled(u'Email'))

    # Case: may not edit name
    other_address_book.allow(account, can_edit_addresses=True, can_add_addresses=False  )
    browser.refresh()
    assert not browser.is_element_enabled(XPath.input_labelled(u'Name'))
    assert browser.is_element_enabled(XPath.input_labelled(u'Email'))

    browser.type(XPath.input_labelled(u'Email'), u'else@some.org')
    browser.click(XPath.button_labelled(u'Update'))

    assert browser.is_element_present(XPath.paragraph_containing(u'Friend: else@some.org'))
    

@test(AccessFixture)
def add_collaborator(fixture):
    """A user may add other users as collaborators to his address book, specifying the privileges in the process."""   
    browser = fixture.browser
    account = fixture.account
    address_book = fixture.address_book

    other_address_book = fixture.other_address_book
    other_account = fixture.other_account

    fixture.log_in(browser=browser, system_account=account)
    browser.open(u'/')

    assert address_book not in AddressBook.address_books_visible_to(other_account)
    assert not address_book.can_be_edited_by(other_account)
    assert not address_book.can_be_added_to_by(other_account)

    browser.click(XPath.link_with_text(u'Address book of johndoe@some.org'))
    browser.click(XPath.link_with_text(u'Add collaborator'))

    browser.select(XPath.select_labelled(u'Choose collaborator'), u'other@some.org')
    browser.click(XPath.input_labelled(u'May add new addresses'))
    browser.click(XPath.input_labelled(u'May edit existing addresses'))

    browser.click(XPath.button_labelled(u'Share'))

    assert fixture.is_on_address_book_page_of(u'johndoe@some.org')

    assert address_book in AddressBook.address_books_visible_to(other_account)
    assert address_book.can_be_edited_by(other_account)
    assert address_book.can_be_added_to_by(other_account)


class ViewScenarios(AccessFixture):
    @scenario
    def viewing_other_address_book(self):
        self.other_address_book; Session.flush()
        self.url = u'/address_book/%s' % self.other_address_book.id
        self.get = True

    @scenario
    def add_address_to_other_address_book(self):
        self.other_address_book; Session.flush()
        self.url = u'/add_address/%s' % self.other_address_book.id
        self.get = False

    @scenario
    def edit_address_in_other_address_book(self):
        address = Address(address_book=self.other_address_book, email_address=u'somefriend@some.org', name=u'Friend')
        address.save()
        Session.flush()
        self.url = u'/edit_address/%s' % address.id
        self.get = True

    @scenario
    def add_collaborator_to_other_address_book(self):
        self.other_address_book; Session.flush()
        self.url = u'/add_collaborator/%s' % self.other_address_book.id
        self.get = True


@test(ViewScenarios)
def view_permissions(fixture):
    browser = fixture.browser
    account = fixture.account

    fixture.log_in(browser=browser, system_account=account)
    if fixture.get:
        browser.open(fixture.url, status=403)
    else:
        browser.post(fixture.url, {}, status=403)









