
from __future__ import print_function, unicode_literals, absolute_import, division

from sqlalchemy import Column, ForeignKey, Integer, UnicodeText, Boolean
from sqlalchemy.orm import relationship

from reahl.sqlalchemysupport import Session, Base
from reahl.domain.systemaccountmodel import AccountManagementInterface, EmailAndPasswordSystemAccount, LoginSession
from reahl.component.modelinterface import exposed, IntegerField, BooleanField, Field, EmailField, Event, Action, Choice, ChoiceField
from reahl.web.fw import UserInterface, UrlBoundView, CannotCreate
from reahl.web.ui import HTML5Page, Form, TextInput, LabelledBlockInput, Button, Panel, A, P, H, InputGroup, Menu, HorizontalLayout,\
                         PasswordInput, ErrorFeedbackMessage, Slot, Widget, SelectInput, CheckboxInput
from reahl.web.pure import PageColumnLayout, UnitSize

class Address(Base):
    __tablename__ = 'access2_address'

    id              = Column(Integer, primary_key=True)    
    address_book_id = Column(Integer, ForeignKey('access2_address_book.id'))
    address_book    = relationship('reahl.doc.examples.tutorial.access2.access2.AddressBook')
    email_address   = Column(UnicodeText)
    name            = Column(UnicodeText)

    @classmethod
    def by_id(cls, address_id, exception_to_raise):
        addresses = Session.query(cls).filter_by(id=address_id)
        if addresses.count() != 1:
            raise exception_to_raise
        return addresses.one()

    @exposed
    def fields(self, fields):
        fields.name = Field(label='Name')
        fields.email_address = EmailField(label='Email', required=True)

    @exposed('save', 'update', 'edit')
    def events(self, events):
        events.save = Event(label='Save', action=Action(self.save))
        events.update = Event(label='Update')
        events.edit = Event(label='Edit')

    def save(self):
        Session.add(self)


class AddressBook(Base):
    __tablename__ = 'access2_address_book'

    id              = Column(Integer, primary_key=True)

    owner_id   = Column(Integer, ForeignKey(EmailAndPasswordSystemAccount.id), nullable=False)
    owner      = relationship(EmailAndPasswordSystemAccount)
    collaborators = relationship('reahl.doc.examples.tutorial.access2.access2.Collaborator', lazy='dynamic',
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

    @exposed
    def fields(self, fields):
        collaborators = [Choice(i.id, IntegerField(label=i.email)) for i in Session.query(EmailAndPasswordSystemAccount).all()]
        fields.chosen_collaborator = ChoiceField(collaborators, label='Choose collaborator')
        fields.may_edit_address = BooleanField(label='May edit existing addresses')
        fields.may_add_address = BooleanField(label='May add new addresses')

    @exposed('add_collaborator')
    def events(self, events):
        events.add_collaborator = Event(label='Share', action=Action(self.add_collaborator))

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
        
    def collaborators_can_be_added_by(self, account):
        return self.owner is account

    def is_visible_to(self, account):
        return self in self.address_books_visible_to(account)

    def get_collaborator(self, account):            
        collaborators = self.collaborators.filter_by(account=account)
        count = collaborators.count()
        if count == 1:
            return collaborators.one()
        if count > 1:
            raise ProgrammerError('There can be only one Collaborator per account. Here is more than one.')
        return None


class Collaborator(Base):
    __tablename__ = 'access2_collaborator'
    id      = Column(Integer, primary_key=True)

    address_book_id = Column(Integer, ForeignKey(AddressBook.id))

    account_id = Column(Integer, ForeignKey(EmailAndPasswordSystemAccount.id), nullable=False)
    account = relationship(EmailAndPasswordSystemAccount)
    
    can_add_addresses = Column(Boolean, default=False)
    can_edit_addresses = Column(Boolean, default=False)


class AddressAppPage(HTML5Page):
    def __init__(self, view, home_bookmark):
        super(AddressAppPage, self).__init__(view, style='basic')
        self.use_layout(PageColumnLayout(('main', UnitSize('1/2'))))

        login_session = LoginSession.for_current_session()
        if login_session.is_logged_in():
            logged_in_as = login_session.account.email
        else:
            logged_in_as = 'Not logged in'

        self.layout.header.add_child(P(view, text=logged_in_as))
        self.layout.header.add_child(Menu.from_bookmarks(view, [home_bookmark]).use_layout(HorizontalLayout()))


class LoginForm(Form):
    def __init__(self, view, accounts):
        super(LoginForm, self).__init__(view, 'login')
        
        if self.exception:
            self.add_child(ErrorFeedbackMessage(view, self.exception.as_user_message()))

        self.add_child(LabelledBlockInput(TextInput(self, accounts.fields.email)))
        self.add_child(LabelledBlockInput(PasswordInput(self, accounts.fields.password)))

        self.define_event_handler(accounts.events.login_event)
        self.add_child(Button(self, accounts.events.login_event))


class LogoutForm(Form):
    def __init__(self, view, accounts):
        super(LogoutForm, self).__init__(view, 'logout')
        self.define_event_handler(accounts.events.log_out_event)
        self.add_child(Button(self, accounts.events.log_out_event))


class HomePageWidget(Widget):
    def __init__(self, view, address_book_ui):
        super(HomePageWidget, self).__init__(view)
        accounts = AccountManagementInterface.for_current_session()
        login_session = LoginSession.for_current_session()
        if login_session.is_logged_in():
            self.add_child(AddressBookList(view, address_book_ui))
            self.add_child(LogoutForm(view, accounts))
        else:
            self.add_child(LoginForm(view, accounts))


class AddressBookList(Panel):
    def __init__(self, view, address_book_ui):
        super(AddressBookList, self).__init__(view)

        current_account = LoginSession.for_current_session().account
        address_books = [book for book in AddressBook.address_books_visible_to(current_account)]
        bookmarks = [address_book_ui.get_address_book_bookmark(address_book, description=address_book.display_name)
                     for address_book in address_books]

        for bookmark in bookmarks:
            p = self.add_child(P(view))
            p.add_child(A.from_bookmark(view, bookmark))
        

class AddressBookPanel(Panel):
    def __init__(self, view, address_book, address_book_ui):
        self.address_book = address_book
        super(AddressBookPanel, self).__init__(view)
        
        self.add_child(H(view, 1, text='Addresses in %s' % address_book.display_name))
        self.add_child(Menu.from_bookmarks(view, self.menu_bookmarks(address_book_ui)).use_layout(HorizontalLayout()))
        self.add_children([AddressBox(view, address) for address in address_book.addresses])

    def menu_bookmarks(self, address_book_ui):
        return [address_book_ui.get_add_address_bookmark(self.address_book), 
                address_book_ui.get_add_collaborator_bookmark(self.address_book)]


class EditAddressForm(Form):
    def __init__(self, view, address):
        super(EditAddressForm, self).__init__(view, 'edit_form')

        grouped_inputs = self.add_child(InputGroup(view, label_text='Edit address'))
        grouped_inputs.add_child(LabelledBlockInput(TextInput(self, address.fields.name)))
        grouped_inputs.add_child(LabelledBlockInput(TextInput(self, address.fields.email_address)))

        grouped_inputs.add_child(Button(self, address.events.update.with_arguments(address_book_id=address.address_book.id)))


class AddAddressForm(Form):
    def __init__(self, view, address_book):
        super(AddAddressForm, self).__init__(view, 'add_form')

        new_address = Address(address_book=address_book)

        grouped_inputs = self.add_child(InputGroup(view, label_text='Add an address'))
        grouped_inputs.add_child(LabelledBlockInput(TextInput(self, new_address.fields.name)))
        grouped_inputs.add_child(LabelledBlockInput(TextInput(self, new_address.fields.email_address)))

        grouped_inputs.add_child(Button(self, new_address.events.save.with_arguments(address_book_id=address_book.id)))


class AddressBox(Form):
    def __init__(self, view, address):
        form_name = 'address_%s' % address.id
        super(AddressBox, self).__init__(view, form_name)

        par = self.add_child(P(view, text='%s: %s ' % (address.name, address.email_address)))
        par.add_child(Button(self, address.events.edit.with_arguments(address_id=address.id)))


class AddressBookView(UrlBoundView):
    def assemble(self, address_book_id=None, address_book_ui=None):
        address_book = AddressBook.by_id(address_book_id, CannotCreate())

        self.title = address_book.display_name
        self.set_slot('main', AddressBookPanel.factory(address_book, address_book_ui))


class AddAddressView(UrlBoundView):
    def assemble(self, address_book_id=None):
        address_book = AddressBook.by_id(address_book_id, CannotCreate())

        self.title = 'Add to %s' % address_book.display_name
        self.set_slot('main', AddAddressForm.factory(address_book))


class AddCollaboratorForm(Form):
    def __init__(self, view, address_book):
        super(AddCollaboratorForm, self).__init__(view, 'add_collaborator_form')

        grouped_inputs = self.add_child(InputGroup(view, label_text='Add a collaborator'))
        grouped_inputs.add_child(LabelledBlockInput(SelectInput(self, address_book.fields.chosen_collaborator)))

        rights_inputs = grouped_inputs.add_child(InputGroup(view, label_text='Rights'))
        rights_inputs.add_child(LabelledBlockInput(CheckboxInput(self, address_book.fields.may_edit_address)))
        rights_inputs.add_child(LabelledBlockInput(CheckboxInput(self, address_book.fields.may_add_address)))

        grouped_inputs.add_child(Button(self, address_book.events.add_collaborator.with_arguments(address_book_id=address_book.id)))


class AddCollaboratorView(UrlBoundView):
    def assemble(self, address_book_id=None):
        address_book = AddressBook.by_id(address_book_id, CannotCreate())

        self.title = 'Add collaborator to %s' % address_book.display_name
        self.set_slot('main', AddCollaboratorForm.factory(address_book))


class EditAddressView(UrlBoundView):
    def assemble(self, address_id=None):
        address = Address.by_id(address_id, CannotCreate())

        self.title = 'Edit Address for %s' % address.name
        self.set_slot('main', EditAddressForm.factory(address))


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






