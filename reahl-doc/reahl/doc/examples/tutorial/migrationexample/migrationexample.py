

from __future__ import unicode_literals
from __future__ import print_function
from datetime import datetime

import elixir



from reahl.sqlalchemysupport import Session, metadata

from reahl.web.fw import UserInterface, Widget
from reahl.web.ui import TwoColumnPage, Form, TextInput, LabelledBlockInput, Button, Panel, P, H, InputGroup
from reahl.component.modelinterface import exposed, EmailField, Field, Event, Action
from reahl.component.migration import Migration

from sqlalchemy import Column, DateTime
from alembic import op

class AddDate(Migration):
    version = '0.1'
    def schedule_upgrades(self):
        print('scheduling upgrades for AddDate')
        self.schedule('alter', op.add_column, 'migration_address', Column('added_date', DateTime))
            

class AddressBookUI(UserInterface):
    def assemble(self):
        self.define_page(TwoColumnPage, style='basic')
        find = self.define_view('/', title='Addresses')
        find.set_slot('main', AddressBookPanel.factory())


class AddressBookPanel(Panel):
    def __init__(self, view):
        super(AddressBookPanel, self).__init__(view)

        self.add_child(H(view, 1, text='Addresses'))
        
        for address in Address.query.all():
            self.add_child(AddressBox(view, address))

        self.add_child(AddAddressForm(view))


class AddAddressForm(Form):
    def __init__(self, view):
        super(AddAddressForm, self).__init__(view, 'add_form')

        new_address = Address()

        grouped_inputs = self.add_child(InputGroup(view, label_text='Add an address'))
        grouped_inputs.add_child( LabelledBlockInput(TextInput(self, new_address.fields.name)) )
        grouped_inputs.add_child( LabelledBlockInput(TextInput(self, new_address.fields.email_address)) )

        self.define_event_handler(new_address.events.save)
        grouped_inputs.add_child(Button(self, new_address.events.save))


class AddressBox(Widget):
    def __init__(self, view, address):
        super(AddressBox, self).__init__(view)
        self.add_child(P(view, text='%s: %s (%s)' % (address.name, address.email_address, address.added_date)))


class Address(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata, tablename='migration_address')
    elixir.using_mapper_options(save_on_init=False)
    
    email_address = elixir.Field(elixir.UnicodeText)
    name          = elixir.Field(elixir.UnicodeText)
#    added_date    = elixir.Field(elixir.DateTime)
    added_date    = 'TODO'

    @exposed
    def fields(self, fields):
        fields.name = Field(label='Name', required=True)
        fields.email_address = EmailField(label='Email', required=True)

    def save(self):
        self.added_date = datetime.now()
        Session.add(self)
        
    @exposed
    def events(self, events):
        events.save = Event(label='Save', action=Action(self.save))

