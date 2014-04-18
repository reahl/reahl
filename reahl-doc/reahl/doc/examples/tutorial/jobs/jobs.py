

from datetime import datetime

import elixir


from reahl.sqlalchemysupport import Session, metadata

from reahl.web.fw import UserInterface
from reahl.web.ui import TwoColumnPage, Form, TextInput, LabelledBlockInput, Button, Panel, P, H, InputGroup
from reahl.component.modelinterface import exposed, EmailField, Field, Event, Action
from reahl.component.migration import Migration


class AddressBookUI(UserInterface):
    def assemble(self):
        self.define_page(TwoColumnPage, style=u'basic')
        find = self.define_view(u'/', title=u'Addresses')
        find.set_slot(u'main', AddressBookPanel.factory())


class AddressBookPanel(Panel):
    def __init__(self, view):
        super(AddressBookPanel, self).__init__(view)

        self.add_child(H(view, 1, text=u'Addresses'))
        
        for address in Address.query.all():
            self.add_child(AddressBox(view, address))

        self.add_child(AddAddressForm(view))


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
        new = u' (new)' if address.added_today else u''
        self.add_child(P(view, text=u'%s: %s%s' % (address.name, address.email_address, new)))


class Address(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata)
    elixir.using_mapper_options(save_on_init=False)
    
    email_address = elixir.Field(elixir.UnicodeText)
    name          = elixir.Field(elixir.UnicodeText)
    added_today   = elixir.Field(elixir.Boolean, required=True, default=True)

    @classmethod
    def clear_added_flags(cls):
        for address in cls.query.filter_by(added_today=True):
            address.added_today = False

    @exposed
    def fields(self, fields):
        fields.name = Field(label=u'Name', required=True)
        fields.email_address = EmailField(label=u'Email', required=True)

    @exposed
    def events(self, events):
        events.save = Event(label=u'Save', action=Action(self.save))

    def save(self):
        Session.add(self)

