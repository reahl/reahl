


from sqlalchemy import Column, ForeignKey, Integer, UnicodeText, Boolean
from sqlalchemy.orm import relationship

from reahl.sqlalchemysupport import Session, Base

from reahl.web.fw import UserInterface, UrlBoundView, CannotCreate, Widget, ProgrammerError
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.navs import Nav, TabLayout
from reahl.web.bootstrap.grid import ColumnLayout, ColumnOptions, ResponsiveSize, Container
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import Div, P, H, A
from reahl.web.bootstrap.forms import Form, TextInput, Button, PasswordInput, SelectInput, CheckboxInput, \
                         FormLayout, FieldSet
from reahl.domain.systemaccountmodel import AccountManagementInterface, EmailAndPasswordSystemAccount, LoginSession
from reahl.component.modelinterface import ExposedNames, IntegerField, BooleanField, Field, EmailField, Event, Action, Choice, ChoiceField


class Address(Base):
    __tablename__ = 'access_address'

    id              = Column(Integer, primary_key=True)
    address_book_id = Column(Integer, ForeignKey('access_address_book.id'))
    address_book    = relationship('reahl.doc.examples.tutorial.accessbootstrap.accessbootstrap.AddressBook')
    email_address   = Column(UnicodeText)
    name            = Column(UnicodeText)

    @classmethod
    def by_id(cls, address_id, exception_to_raise):
        addresses = Session.query(cls).filter_by(id=address_id)
        if addresses.count() != 1:
            raise exception_to_raise
        return addresses.one()

    fields = ExposedNames()
    fields.name = lambda i: Field(label='Name', required=i.can_be_added(), writable=Action(i.can_be_added))
    fields.email_address = lambda i: EmailField(label='Email', required=True, writable=Action(i.can_be_edited))

    events = ExposedNames()
    events.save = lambda i: Event(label='Save', action=Action(i.save))
    events.update = lambda i: Event(label='Update')
    events.edit = lambda i: Event(label='Edit', writable=Action(i.can_be_edited))

    def save(self):
        Session.add(self)

    def can_be_edited(self):
        current_account = LoginSession.for_current_session().account
        return self.address_book.can_be_edited_by(current_account)

    def can_be_added(self):
        current_account = LoginSession.for_current_session().account
        return self.address_book.can_be_added_to_by(current_account)


class AddressBook(Base):
    __tablename__ = 'access_address_book'

    id              = Column(Integer, primary_key=True)

    owner_id   = Column(Integer, ForeignKey(EmailAndPasswordSystemAccount.id), nullable=False)
    owner      = relationship(EmailAndPasswordSystemAccount)
    collaborators = relationship('reahl.doc.examples.tutorial.accessbootstrap.accessbootstrap.Collaborator', lazy='dynamic',
                                 backref='address_book')

    @classmethod
    def by_id(cls, address_book_id, exception_to_raise):
        address_books = Session.query(cls).filter_by(id=address_book_id)
        if address_books.count() != 1:
            raise exception_to_raise
        return address_books.one()

    @classmethod
    def owned_by(cls, account):
        return Session.query(cls).filter_by(owner=account)

    @classmethod
    def address_books_visible_to(cls, account):
        visible_books = Session.query(cls).join(Collaborator).filter(Collaborator.account == account).all()
        visible_books.extend(cls.owned_by(account))
        return visible_books

    fields = ExposedNames()
    fields.chosen_collaborator = lambda i: ChoiceField([Choice(i.id, IntegerField(label=i.email)) for i in Session.query(EmailAndPasswordSystemAccount).all()],
                                                       label='Choose collaborator')
    fields.may_edit_address = lambda i: BooleanField(label='May edit existing addresses')
    fields.may_add_address = lambda i: BooleanField(label='May add new addresses')

    events = ExposedNames()
    events.add_collaborator = lambda i: Event(label='Share', action=Action(i.add_collaborator))

    def add_collaborator(self):
        chosen_account = Session.query(EmailAndPasswordSystemAccount).filter_by(id=self.chosen_collaborator).one()
        self.allow(chosen_account, can_add_addresses=self.may_add_address, can_edit_addresses=self.may_edit_address)

    @property
    def addresses(self):
        return Session.query(Address).filter_by(address_book=self).all()

    @property
    def display_name(self):
        return 'Address book of %s' % self.owner.email

    def allow(self, account, can_add_addresses=False, can_edit_addresses=False):
        Session.query(Collaborator).filter_by(address_book=self, account=account).delete()
        Collaborator(address_book=self, account=account,
            can_add_addresses=can_add_addresses,
            can_edit_addresses=can_edit_addresses)

    def can_be_edited_by(self, account):
        if account is self.owner:
            return True

        collaborator = self.get_collaborator(account)
        return (collaborator and collaborator.can_edit_addresses) or self.can_be_added_to_by(account)

    def can_be_added_to_by(self, account):
        if account is self.owner:
            return True

        collaborator = self.get_collaborator(account)
        return collaborator and collaborator.can_add_addresses

    def can_be_added_to(self):
        account = LoginSession.for_current_session().account
        return self.can_be_added_to_by(account)

    def collaborators_can_be_added_by(self, account):
        return self.owner is account

    def collaborators_can_be_added(self):
        account = LoginSession.for_current_session().account
        return self.collaborators_can_be_added_by(account)

    def is_visible_to(self, account):
        return self in self.address_books_visible_to(account)

    def is_visible(self):
        account = LoginSession.for_current_session().account
        return self.is_visible_to(account)

    def get_collaborator(self, account):
        collaborators = self.collaborators.filter_by(account=account)
        count = collaborators.count()
        if count == 1:
            return collaborators.one()
        if count > 1:
            raise ProgrammerError('There can be only one Collaborator per account. Here is more than one.')
        return None


class Collaborator(Base):
    __tablename__ = 'access_collaborator'
    id      = Column(Integer, primary_key=True)

    address_book_id = Column(Integer, ForeignKey(AddressBook.id))

    account_id = Column(Integer, ForeignKey(EmailAndPasswordSystemAccount.id), nullable=False)
    account = relationship(EmailAndPasswordSystemAccount)

    can_add_addresses = Column(Boolean, default=False)
    can_edit_addresses = Column(Boolean, default=False)


class AddressAppPage(HTML5Page):
    def __init__(self, view, home_bookmark):
        super().__init__(view)
        self.use_layout(PageLayout(document_layout=Container()))
        contents_layout = ColumnLayout(ColumnOptions('main', ResponsiveSize(lg=6))).with_slots()
        self.layout.contents.use_layout(contents_layout)

        login_session = LoginSession.for_current_session()
        if login_session.is_logged_in():
            logged_in_as = login_session.account.email
        else:
            logged_in_as = 'Not logged in'

        self.layout.header.add_child(P(view, text=logged_in_as))
        self.layout.header.add_child(Nav(view).use_layout(TabLayout()).with_bookmarks([home_bookmark]))


class LoginForm(Form):
    def __init__(self, view, accounts):
        super().__init__(view, 'login')
        self.use_layout(FormLayout())

        if self.exception:
            self.layout.add_alert_for_domain_exception(self.exception)

        self.layout.add_input(TextInput(self, accounts.fields.email))
        self.layout.add_input(PasswordInput(self, accounts.fields.password))

        self.define_event_handler(accounts.events.login_event)
        self.add_child(Button(self, accounts.events.login_event, style='primary'))


class LogoutForm(Form):
    def __init__(self, view, accounts):
        super().__init__(view, 'logout')
        self.define_event_handler(accounts.events.log_out_event)
        self.add_child(Button(self, accounts.events.log_out_event, style='primary'))


class HomePageWidget(Widget):
    def __init__(self, view, address_book_ui):
        super().__init__(view)
        accounts = AccountManagementInterface.for_current_session()
        login_session = LoginSession.for_current_session()
        if login_session.is_logged_in():
            self.add_child(AddressBookList(view, address_book_ui))
            self.add_child(LogoutForm(view, accounts))
        else:
            self.add_child(LoginForm(view, accounts))


class AddressBookList(Div):
    def __init__(self, view, address_book_ui):
        super().__init__(view)

        current_account = LoginSession.for_current_session().account
        address_books = [book for book in AddressBook.address_books_visible_to(current_account)]
        bookmarks = [address_book_ui.get_address_book_bookmark(address_book, description=address_book.display_name)
                     for address_book in address_books]

        for bookmark in bookmarks:
            p = self.add_child(P(view))
            p.add_child(A.from_bookmark(view, bookmark))


class AddressBookPanel(Div):
    def __init__(self, view, address_book, address_book_ui):
        self.address_book = address_book
        super().__init__(view)

        self.add_child(H(view, 1, text='Addresses in %s' % address_book.display_name))
        self.add_child(Nav(view).use_layout(TabLayout()).with_bookmarks(self.menu_bookmarks(address_book_ui)))
        self.add_children([AddressBox(view, address) for address in address_book.addresses])

    def menu_bookmarks(self, address_book_ui):
        return [address_book_ui.get_add_address_bookmark(self.address_book),
                address_book_ui.get_add_collaborator_bookmark(self.address_book)]


class EditAddressForm(Form):
    def __init__(self, view, address):
        super().__init__(view, 'edit_form')

        grouped_inputs = self.add_child(FieldSet(view, legend_text='Edit address'))
        grouped_inputs.use_layout(FormLayout())
        grouped_inputs.layout.add_input(TextInput(self, address.fields.name))
        grouped_inputs.layout.add_input(TextInput(self, address.fields.email_address))

        grouped_inputs.add_child(Button(self, address.events.update.with_arguments(address_book_id=address.address_book.id), style='primary'))


class AddAddressForm(Form):
    def __init__(self, view, address_book):
        super().__init__(view, 'add_form')

        new_address = Address(address_book=address_book)

        grouped_inputs = self.add_child(FieldSet(view, legend_text='Add an address'))
        grouped_inputs.use_layout(FormLayout())
        grouped_inputs.layout.add_input(TextInput(self, new_address.fields.name))
        grouped_inputs.layout.add_input(TextInput(self, new_address.fields.email_address))

        grouped_inputs.add_child(Button(self, new_address.events.save.with_arguments(address_book_id=address_book.id), style='primary'))


class AddressBox(Form):
    def __init__(self, view, address):
        form_name = 'address_%s' % address.id
        super().__init__(view, form_name)
        self.use_layout(FormLayout())

        par = self.add_child(P(view, text='%s: %s ' % (address.name, address.email_address)))
        par.add_child(Button(self, address.events.edit.with_arguments(address_id=address.id)))


class AddressBookView(UrlBoundView):
    def assemble(self, address_book_id=None, address_book_ui=None):
        address_book = AddressBook.by_id(address_book_id, CannotCreate())

        self.title = address_book.display_name
        self.set_slot('main', AddressBookPanel.factory(address_book, address_book_ui))
        self.read_check = address_book.is_visible


class AddAddressView(UrlBoundView):
    def assemble(self, address_book_id=None):
        address_book = AddressBook.by_id(address_book_id, CannotCreate())

        self.title = 'Add to %s' % address_book.display_name
        self.set_slot('main', AddAddressForm.factory(address_book))
        self.write_check = address_book.can_be_added_to


class AddCollaboratorForm(Form):
    def __init__(self, view, address_book):
        super().__init__(view, 'add_collaborator_form')

        grouped_inputs = self.add_child(FieldSet(view, legend_text='Add a collaborator'))
        grouped_inputs.use_layout(FormLayout())
        grouped_inputs.layout.add_input(SelectInput(self, address_book.fields.chosen_collaborator))

        rights_inputs = grouped_inputs.add_child(FieldSet(view, legend_text='Rights'))
        rights_inputs.use_layout(FormLayout())
        rights_inputs.layout.add_input(CheckboxInput(self, address_book.fields.may_edit_address))
        rights_inputs.layout.add_input(CheckboxInput(self, address_book.fields.may_add_address))

        grouped_inputs.add_child(Button(self, address_book.events.add_collaborator.with_arguments(address_book_id=address_book.id), style='primary'))


class AddCollaboratorView(UrlBoundView):
    def assemble(self, address_book_id=None):
        address_book = AddressBook.by_id(address_book_id, CannotCreate())

        self.title = 'Add collaborator to %s' % address_book.display_name
        self.set_slot('main', AddCollaboratorForm.factory(address_book))
        self.read_check = address_book.collaborators_can_be_added


class EditAddressView(UrlBoundView):
    def assemble(self, address_id=None):
        address = Address.by_id(address_id, CannotCreate())

        self.title = 'Edit Address for %s' % address.name
        self.set_slot('main', EditAddressForm.factory(address))
        self.read_check = address.can_be_edited


class AddressBookUI(UserInterface):
    def assemble(self):

        home = self.define_view('/', title='Address books')
        home.set_slot('main', HomePageWidget.factory(self))

        self.address_book_page = self.define_view('/address_book', view_class=AddressBookView,
                                                  address_book_id=IntegerField(required=True),
                                                  address_book_ui=self)
        self.add_address_page = self.define_view('/add_address', view_class=AddAddressView,
                                                 address_book_id=IntegerField(required=True))

        edit_address_page = self.define_view('/edit_address', view_class=EditAddressView,
                                             address_id=IntegerField(required=True))

        self.add_collaborator_page = self.define_view('/add_collaborator', view_class=AddCollaboratorView,
                                                     address_book_id=IntegerField(required=True))

        self.define_transition(Address.events.save, self.add_address_page, self.address_book_page)
        self.define_transition(Address.events.edit, self.address_book_page, edit_address_page)
        self.define_transition(Address.events.update, edit_address_page, self.address_book_page)
        self.define_transition(AddressBook.events.add_collaborator, self.add_collaborator_page, self.address_book_page)

        self.define_page(AddressAppPage, home.as_bookmark(self))

    def get_address_book_bookmark(self, address_book, description=None):
        return self.address_book_page.as_bookmark(self, description=description, address_book_id=address_book.id)

    def get_add_address_bookmark(self, address_book, description='Add address'):
        return self.add_address_page.as_bookmark(self, description=description, address_book_id=address_book.id)

    def get_add_collaborator_bookmark(self, address_book, description='Add collaborator'):
        return self.add_collaborator_page.as_bookmark(self, description=description, address_book_id=address_book.id)









