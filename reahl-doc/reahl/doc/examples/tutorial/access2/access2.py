
import elixir

from reahl.sqlalchemysupport import Session, metadata
from reahl.systemaccountmodel import AccountManagementInterface, EmailAndPasswordSystemAccount, UserSession
from reahl.component.modelinterface import exposed, IntegerField, BooleanField, Field, EmailField, Event, Action, Choice, ChoiceField
from reahl.web.fw import Region, UrlBoundView, CannotCreate
from reahl.web.ui import TwoColumnPage, Form, TextInput, LabelledBlockInput, Button, Panel, A, P, H, InputGroup, HMenu,\
                         PasswordInput, ErrorFeedbackMessage, Slot, Widget, SelectInput, CheckboxInput



class Address(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata)
    elixir.using_mapper_options(save_on_init=False)
    
    address_book  = elixir.ManyToOne(u'reahl.doc.examples.tutorial.access2.access2.AddressBook')
    email_address = elixir.Field(elixir.UnicodeText)
    name          = elixir.Field(elixir.UnicodeText)

    @classmethod
    def by_id(cls, address_id, exception_to_raise):
        addresses = Address.query.filter_by(id=address_id)
        if addresses.count() != 1:
            raise exception_to_raise
        return addresses.one()

    @exposed
    def fields(self, fields):
        fields.name = Field(label=u'Name')
        fields.email_address = EmailField(label=u'Email', required=True)

    @exposed(u'save', u'update', u'edit')
    def events(self, events):
        events.save = Event(label=u'Save', action=Action(self.save))
        events.update = Event(label=u'Update')
        events.edit = Event(label=u'Edit')

    def save(self):
        Session.add(self)


class AddressBook(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata)

    owner      = elixir.ManyToOne(EmailAndPasswordSystemAccount, required=True)

    @classmethod
    def by_id(cls, address_book_id, exception_to_raise):
        address_books = AddressBook.query.filter_by(id=address_book_id)
        if address_books.count() != 1:
            raise exception_to_raise
        return address_books.one()
    
    @classmethod
    def owned_by(cls, account):
        return cls.query.filter_by(owner=account)
        
    @classmethod
    def address_books_visible_to(cls, account):
        visible_books = cls.query.join(Collaborator).filter(Collaborator.account == account).all()
        visible_books.extend(cls.owned_by(account))
        return visible_books

    @exposed
    def fields(self, fields):
        collaborators = [Choice(i.id, IntegerField(label=i.email)) for i in EmailAndPasswordSystemAccount.query.all()]
        fields.chosen_collaborator = ChoiceField(collaborators, label=u'Choose collaborator')
        fields.may_edit_address = BooleanField(label=u'May edit existing addresses')
        fields.may_add_address = BooleanField(label=u'May add new addresses')

    @exposed(u'add_collaborator')
    def events(self, events):
        events.add_collaborator = Event(label=u'Share', action=Action(self.add_collaborator))

    def add_collaborator(self):
        chosen_account = EmailAndPasswordSystemAccount.query.filter_by(id=self.chosen_collaborator).one()
        self.allow(chosen_account, can_add_addresses=self.may_add_address, can_edit_addresses=self.may_edit_address)

    # See https://groups.google.com/forum/?fromgroups=#!topic/sqlelixir/ZlR9Kvcor6Q
    #    addresses  = elixir.OneToMany(Address)
    @property
    def addresses(self):
        return Address.query.filter_by(address_book=self).all()

    collaborators = elixir.OneToMany(u'reahl.doc.examples.tutorial.access2.access2.Collaborator', lazy=u'dynamic')

    @property
    def display_name(self):
        return u'Address book of %s' % self.owner.email

    def allow(self, account, can_add_addresses=False, can_edit_addresses=False):
        Collaborator.query.filter_by(address_book=self, account=account).delete()
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


class Collaborator(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata)

    account = elixir.ManyToOne(EmailAndPasswordSystemAccount)
    can_add_addresses = elixir.Field(elixir.Boolean, default=False)
    can_edit_addresses = elixir.Field(elixir.Boolean, default=False)

    address_book = elixir.ManyToOne(AddressBook)


class AddressAppPage(TwoColumnPage):
    def __init__(self, view, home_bookmark):
        super(AddressAppPage, self).__init__(view, style=u'basic')

        user_session = UserSession.for_current_session()
        if user_session.is_logged_in():
            logged_in_as = user_session.account.email
        else:
            logged_in_as = u'Not logged in'

        self.header.add_child(P(view, text=logged_in_as))
        self.header.add_child(HMenu.from_bookmarks(view, [home_bookmark]))


class LoginForm(Form):
    def __init__(self, view, accounts):
        super(LoginForm, self).__init__(view, u'login')
        
        if self.exception:
            self.add_child(ErrorFeedbackMessage(view, self.exception.as_user_message()))

        self.add_child(LabelledBlockInput(TextInput(self, accounts.fields.email)))
        self.add_child(LabelledBlockInput(PasswordInput(self, accounts.fields.password)))

        self.define_event_handler(accounts.events.login_event)
        self.add_child(Button(self, accounts.events.login_event))


class LogoutForm(Form):
    def __init__(self, view, accounts):
        super(LogoutForm, self).__init__(view, u'logout')
        self.define_event_handler(accounts.events.log_out_event)
        self.add_child(Button(self, accounts.events.log_out_event))


class HomePageWidget(Widget):
    def __init__(self, view, address_book_app):
        super(HomePageWidget, self).__init__(view)
        accounts = AccountManagementInterface.for_current_session()
        user_session = UserSession.for_current_session()
        if user_session.is_logged_in():
            self.add_child(AddressBookList(view, address_book_app))
            self.add_child(LogoutForm(view, accounts))
        else:
            self.add_child(LoginForm(view, accounts))


class AddressBookList(Panel):
    def __init__(self, view, address_book_app):
        super(AddressBookList, self).__init__(view)

        current_account = UserSession.for_current_session().account
        address_books = [book for book in AddressBook.address_books_visible_to(current_account)]
        bookmarks = [address_book_app.get_address_book_bookmark(address_book, description=address_book.display_name)
                     for address_book in address_books]

        for bookmark in bookmarks:
            p = self.add_child(P(view))
            p.add_child(A.from_bookmark(view, bookmark))
        

class AddressBookPanel(Panel):
    def __init__(self, view, address_book, address_book_app):
    	self.address_book = address_book
        super(AddressBookPanel, self).__init__(view)
        
        self.add_child(H(view, 1, text=u'Addresses in %s' % address_book.display_name))
        self.add_child(HMenu.from_bookmarks(view, self.menu_bookmarks(address_book_app)))
        self.add_children([AddressBox(view, address) for address in address_book.addresses])

    def menu_bookmarks(self, address_book_app):
        return [address_book_app.get_add_address_bookmark(self.address_book), 
                address_book_app.get_add_collaborator_bookmark(self.address_book)]


class EditAddressForm(Form):
    def __init__(self, view, address):
        super(EditAddressForm, self).__init__(view, u'edit_form')

        grouped_inputs = self.add_child(InputGroup(view, label_text=u'Edit address'))
        grouped_inputs.add_child(LabelledBlockInput(TextInput(self, address.fields.name)))
        grouped_inputs.add_child(LabelledBlockInput(TextInput(self, address.fields.email_address)))

        grouped_inputs.add_child(Button(self, address.events.update.with_arguments(address_book_id=address.address_book.id)))


class AddAddressForm(Form):
    def __init__(self, view, address_book):
        super(AddAddressForm, self).__init__(view, u'add_form')

        new_address = Address(address_book=address_book)

        grouped_inputs = self.add_child(InputGroup(view, label_text=u'Add an address'))
        grouped_inputs.add_child(LabelledBlockInput(TextInput(self, new_address.fields.name)))
        grouped_inputs.add_child(LabelledBlockInput(TextInput(self, new_address.fields.email_address)))

        grouped_inputs.add_child(Button(self, new_address.events.save.with_arguments(address_book_id=address_book.id)))


class AddressBox(Form):
    def __init__(self, view, address):
        form_name = u'address_%s' % address.id
        super(AddressBox, self).__init__(view, form_name)

        par = self.add_child(P(view, text=u'%s: %s ' % (address.name, address.email_address)))
        par.add_child(Button(self, address.events.edit.with_arguments(address_id=address.id)))


class AddressBookView(UrlBoundView):
    def assemble(self, address_book_id=None, address_book_app=None):
        address_book = AddressBook.by_id(address_book_id, CannotCreate())

        self.title = address_book.display_name
        self.set_slot(u'main', AddressBookPanel.factory(address_book, address_book_app))


class AddAddressView(UrlBoundView):
    def assemble(self, address_book_id=None):
        address_book = AddressBook.by_id(address_book_id, CannotCreate())

        self.title = u'Add to %s' % address_book.display_name
        self.set_slot(u'main', AddAddressForm.factory(address_book))


class AddCollaboratorForm(Form):
    def __init__(self, view, address_book):
        super(AddCollaboratorForm, self).__init__(view, u'add_collaborator_form')

        grouped_inputs = self.add_child(InputGroup(view, label_text=u'Add a collaborator'))
        grouped_inputs.add_child(LabelledBlockInput(SelectInput(self, address_book.fields.chosen_collaborator)))

        rights_inputs = grouped_inputs.add_child(InputGroup(view, label_text=u'Rights'))
        rights_inputs.add_child(LabelledBlockInput(CheckboxInput(self, address_book.fields.may_edit_address)))
        rights_inputs.add_child(LabelledBlockInput(CheckboxInput(self, address_book.fields.may_add_address)))

        grouped_inputs.add_child(Button(self, address_book.events.add_collaborator.with_arguments(address_book_id=address_book.id)))


class AddCollaboratorView(UrlBoundView):
    def assemble(self, address_book_id=None):
        address_book = AddressBook.by_id(address_book_id, CannotCreate())

        self.title = u'Add collaborator to %s' % address_book.display_name
        self.set_slot(u'main', AddCollaboratorForm.factory(address_book))


class EditAddressView(UrlBoundView):
    def assemble(self, address_id=None):
        address = Address.by_id(address_id, CannotCreate())

        self.title = u'Edit Address for %s' % address.name
        self.set_slot(u'main', EditAddressForm.factory(address))


class AddressBookApp(Region):
    def assemble(self):

        home = self.define_view(u'/', title=u'Address books')
        home.set_slot(u'main', HomePageWidget.factory(self))
      
        self.address_book_page = self.define_view(u'/address_book', view_class=AddressBookView, 
                                                  address_book_id=IntegerField(required=True),
                                                  address_book_app=self)
        self.add_address_page = self.define_view(u'/add_address', view_class=AddAddressView, 
                                                 address_book_id=IntegerField(required=True))

        edit_address_page = self.define_view(u'/edit_address', view_class=EditAddressView,
                                             address_id=IntegerField(required=True))

        self.add_collaborator_page = self.define_view(u'/add_collaborator', view_class=AddCollaboratorView, 
                                                     address_book_id=IntegerField(required=True))
        
        self.define_transition(Address.events.save, self.add_address_page, self.address_book_page)
        self.define_transition(Address.events.edit, self.address_book_page, edit_address_page)
        self.define_transition(Address.events.update, edit_address_page, self.address_book_page)
        self.define_transition(AddressBook.events.add_collaborator, self.add_collaborator_page, self.address_book_page)

        self.define_main_window(AddressAppPage, home.as_bookmark(self))

    def get_address_book_bookmark(self, address_book, description=None):
        return self.address_book_page.as_bookmark(self, description=description, address_book_id=address_book.id)

    def get_add_address_bookmark(self, address_book, description=u'Add address'):
        return self.add_address_page.as_bookmark(self, description=description, address_book_id=address_book.id)
        
    def get_add_collaborator_bookmark(self, address_book, description=u'Add collaborator'):
        return self.add_collaborator_page.as_bookmark(self, description=description, address_book_id=address_book.id)






