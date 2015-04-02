

from __future__ import print_function, unicode_literals, absolute_import, division

from sqlalchemy import Column, Integer, UnicodeText, Boolean

from reahl.sqlalchemysupport import Session, Base

from reahl.web.fw import UserInterface, Widget
from reahl.web.ui import HTML5Page, Form, TextInput, LabelledBlockInput, Button, Panel, P, H, InputGroup
from reahl.web.pure import PageColumnLayout, UnitSize
from reahl.component.modelinterface import exposed, EmailField, Field, Event, Action


class AddressBookUI(UserInterface):
    def assemble(self):
        self.define_page(HTML5Page, style='basic').use_layout(PageColumnLayout(('main', UnitSize('1/3'))))
        find = self.define_view('/', title='Addresses')
        find.set_slot('main', AddressBookPanel.factory())


class AddressBookPanel(Panel):
    def __init__(self, view):
        super(AddressBookPanel, self).__init__(view)

        self.add_child(H(view, 1, text='Addresses'))
        
        for address in Session.query(Address).all():
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
        new = ' (new)' if address.added_today else ''
        self.add_child(P(view, text='%s: %s%s' % (address.name, address.email_address, new)))


class Address(Base):
    __tablename__ = 'jobs_address'

    id            = Column(Integer, primary_key=True)
    email_address = Column(UnicodeText)
    name          = Column(UnicodeText)
    added_today   = Column(Boolean, nullable=False, default=True)

    @classmethod
    def clear_added_flags(cls):
        for address in Session.query(cls).filter_by(added_today=True):
            address.added_today = False

    @exposed
    def fields(self, fields):
        fields.name = Field(label='Name', required=True)
        fields.email_address = EmailField(label='Email', required=True)

    @exposed
    def events(self, events):
        events.save = Event(label='Save', action=Action(self.save))

    def save(self):
        Session.add(self)

