

from __future__ import unicode_literals
from __future__ import print_function
import elixir
from sqlalchemy.orm.exc import NoResultFound

from reahl.sqlalchemysupport import Session, metadata

from reahl.web.fw import CannotCreate
from reahl.web.fw import UrlBoundView
from reahl.web.fw import UserInterface
from reahl.web.fw import Widget
from reahl.web.ui import TwoColumnPage, Form, TextInput, LabelledBlockInput, Button, Panel, P, H, A, InputGroup, HMenu
from reahl.component.modelinterface import exposed, EmailField, Field, Event, IntegerField, Action


class AddressBookPage(TwoColumnPage):
    def __init__(self, view, main_bookmarks):
        super(AddressBookPage, self).__init__(view, style='basic')
        self.header.add_child(HMenu.from_bookmarks(view, main_bookmarks))


class EditView(UrlBoundView):
    def assemble(self, address_id=None):
        try:
            address = Address.query.filter_by(id=address_id).one()
        except NoResultFound:
            raise CannotCreate()

        self.title = 'Edit %s' % address.name
        self.set_slot('main', EditAddressForm.factory(address))


class AddressBookUI(UserInterface):
    def assemble(self):

        add = self.define_view('/add', title='Add an address')
        add.set_slot('main', AddAddressForm.factory())

        edit = self.define_view('/edit', view_class=EditView, address_id=IntegerField())

        addresses = self.define_view('/', title='Addresses')
        addresses.set_slot('main', AddressBookPanel.factory(self))

        bookmarks = [f.as_bookmark(self) for f in [addresses, add]]
        self.define_page(AddressBookPage, bookmarks)

        self.define_transition(Address.events.save, add, addresses)
        self.define_transition(Address.events.update, edit, addresses)

        self.edit = edit

    def get_edit_bookmark(self, address, description=None):
        return self.edit.as_bookmark(self, address_id=address.id, description=description)



class AddressBookPanel(Panel):
    def __init__(self, view, address_book_ui):
        super(AddressBookPanel, self).__init__(view)

        self.add_child(H(view, 1, text='Addresses'))
        
        for address in Address.query.all():
            self.add_child(AddressBox(view, address, address_book_ui))


class EditAddressForm(Form):
    def __init__(self, view, address):
        super(EditAddressForm, self).__init__(view, 'edit_form')

        grouped_inputs = self.add_child(InputGroup(view, label_text='Edit address'))
        grouped_inputs.add_child(LabelledBlockInput(TextInput(self, address.fields.name)))
        grouped_inputs.add_child(LabelledBlockInput(TextInput(self, address.fields.email_address)))

        grouped_inputs.add_child(Button(self, address.events.update))


class AddAddressForm(Form):
    def __init__(self, view):
        super(AddAddressForm, self).__init__(view, 'add_form')

        new_address = Address()
        grouped_inputs = self.add_child(InputGroup(view, label_text='Add an address'))
        grouped_inputs.add_child(LabelledBlockInput(TextInput(self, new_address.fields.name)))
        grouped_inputs.add_child(LabelledBlockInput(TextInput(self, new_address.fields.email_address)))

        grouped_inputs.add_child(Button(self, new_address.events.save))


class AddressBox(Widget):
    def __init__(self, view, address, address_book_ui):
        super(AddressBox, self).__init__(view)

        bookmark = address_book_ui.get_edit_bookmark(address=address, description='edit')
        par = self.add_child(P(view, text='%s: %s ' % (address.name, address.email_address)))
        par.add_child(A.from_bookmark(view, bookmark))


class Address(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata, tablename='tutorial_parameterised1_address')
    elixir.using_mapper_options(save_on_init=False)
    
    email_address = elixir.Field(elixir.UnicodeText)
    name          = elixir.Field(elixir.UnicodeText)

    @exposed
    def fields(self, fields):
        fields.name = Field(label='Name', required=True)
        fields.email_address = EmailField(label='Email', required=True)

    @exposed('save', 'update')
    def events(self, events):
        events.save = Event(label='Save', action=Action(self.save))
        events.update = Event(label='Update')

    def save(self):
        Session.add(self)


