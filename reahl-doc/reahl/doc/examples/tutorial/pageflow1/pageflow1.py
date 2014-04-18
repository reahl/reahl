

import elixir

from reahl.sqlalchemysupport import Session, metadata

from reahl.web.fw import UserInterface
from reahl.web.ui import TwoColumnPage, Form, TextInput, LabelledBlockInput, Button, Panel, P, H, InputGroup, HMenu
from reahl.component.modelinterface import exposed, EmailField, Field, Event, Action
from reahl.systemaccountmodel import AccountManagementInterface


class AddressBookPage(TwoColumnPage):
    def __init__(self, view, main_bookmarks):
        super(AddressBookPage, self).__init__(view, style=u'basic')
        self.header.add_child(HMenu.from_bookmarks(view, main_bookmarks))


class AddressBookUI(UserInterface):
    def assemble(self):

        addresses = self.define_view(u'/', title=u'Addresses')
        addresses.set_slot(u'main', AddressBookPanel.factory())

        add = self.define_view(u'/add', title=u'Add an address')
        add.set_slot(u'main', AddAddressForm.factory())
        
        bookmarks = [v.as_bookmark(self) for v in [addresses, add]]
        self.define_page(AddressBookPage, bookmarks)


class AddressBookPanel(Panel):
    def __init__(self, view):
        super(AddressBookPanel, self).__init__(view)

        self.add_child(H(view, 1, text=u'Addresses'))
        
        for address in Address.query.all():
            self.add_child(AddressBox(view, address))


class AddAddressForm(Form):
    def __init__(self, view):
        super(AddAddressForm, self).__init__(view, u'add_form')

        new_address = Address()

        grouped_inputs = self.add_child(InputGroup(view, label_text=u'Add an address'))
        grouped_inputs.add_child( LabelledBlockInput(TextInput(self, new_address.fields.name)) )
        grouped_inputs.add_child( LabelledBlockInput(TextInput(self, new_address.fields.email_address)) )

        self.define_event_handler(new_address.events.save)
        grouped_inputs.add_child(Button(self, new_address.events.save))


class AddressBox(Panel):
    def __init__(self, view, address):
        super(AddressBox, self).__init__(view)
        self.add_child(P(view, text=u'%s: %s' % (address.name, address.email_address)))


class Address(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata)
    elixir.using_mapper_options(save_on_init=False)
    
    email_address = elixir.Field(elixir.UnicodeText)
    name          = elixir.Field(elixir.UnicodeText)

    @exposed
    def fields(self, fields):
        fields.name = Field(label=u'Name', required=True)
        fields.email_address = EmailField(label=u'Email', required=True)

    def save(self):
        Session.add(self)
        
    @exposed
    def events(self, events):
        events.save = Event(label=u'Save', action=Action(self.save))


