

from __future__ import print_function, unicode_literals, absolute_import, division

from sqlalchemy import Column, Integer, UnicodeText

from reahl.sqlalchemysupport import Session, Base

from reahl.web.fw import UserInterface, Widget
from reahl.web.ui import HTML5Page, Form, TextInput, LabelledBlockInput, Button, Panel, P, H, InputGroup, Menu, HorizontalLayout
from reahl.component.modelinterface import exposed, EmailField, Field, Event, Action


class AddressBookPage(HTML5Page):
    def __init__(self, view, main_bookmarks):
        super(AddressBookPage, self).__init__(view, style='basic')
        self.body.add_child(Menu.from_bookmarks(view, main_bookmarks).use_layout(HorizontalLayout()))


class HomePage(AddressBookPage):
    def __init__(self, view, main_bookmarks):
        super(HomePage, self).__init__(view, main_bookmarks)
        self.body.add_child(AddressBookPanel(view))


class AddPage(AddressBookPage):
    def __init__(self, view, main_bookmarks):
        super(AddPage, self).__init__(view, main_bookmarks)
        self.body.add_child(AddAddressForm(view))


class AddressBookUI(UserInterface):
    def assemble(self):
        addresses = self.define_view('/', title='Addresses')
        add = self.define_view('/add', title='Add an address')
        
        bookmarks = [v.as_bookmark(self) for v in [addresses, add]]

        addresses.set_page(HomePage.factory(bookmarks))
        add.set_page(AddPage.factory(bookmarks))

        self.define_transition(Address.events.save, add, addresses)


class AddressBookPanel(Panel):
    def __init__(self, view):
        super(AddressBookPanel, self).__init__(view)

        self.add_child(H(view, 1, text='Addresses'))
        
        for address in Session.query(Address).all():
            self.add_child(AddressBox(view, address))


class AddAddressForm(Form):
    def __init__(self, view):
        super(AddAddressForm, self).__init__(view, 'add_form')

        new_address = Address()

        grouped_inputs = self.add_child(InputGroup(view, label_text='Add an address'))
        grouped_inputs.add_child( LabelledBlockInput(TextInput(self, new_address.fields.name)) )
        grouped_inputs.add_child( LabelledBlockInput(TextInput(self, new_address.fields.email_address)) )

        grouped_inputs.add_child(Button(self, new_address.events.save))


class AddressBox(Widget):
    def __init__(self, view, address):
        super(AddressBox, self).__init__(view)
        self.add_child(P(view, text='%s: %s' % (address.name, address.email_address)))


class Address(Base):
    __tablename__ = 'pageflow2_address'
    
    id            = Column(Integer, primary_key=True)
    email_address = Column(UnicodeText)
    name          = Column(UnicodeText)

    @exposed
    def fields(self, fields):
        fields.name = Field(label='Name', required=True)
        fields.email_address = EmailField(label='Email', required=True)

    def save(self):
        Session.add(self)
        
    @exposed('save')
    def events(self, events):
        events.save = Event(label='Save', action=Action(self.save))




