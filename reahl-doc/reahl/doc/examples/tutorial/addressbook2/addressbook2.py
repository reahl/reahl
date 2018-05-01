from __future__ import print_function, unicode_literals, absolute_import, division

from reahl.web.fw import UserInterface, Widget
from reahl.web.bootstrap.ui import HTML5Page, TextNode, Div, H, P, FieldSet
from reahl.web.bootstrap.navbar import Navbar, ResponsiveLayout
from reahl.web.bootstrap.grid import Container
from reahl.web.bootstrap.forms import TextInput, Form, FormLayout, Button, ButtonLayout
from reahl.component.modelinterface import exposed, Field, EmailField, Action, Event
from reahl.sqlalchemysupport import Session, Base
from sqlalchemy import Column, Integer, UnicodeText


class AddressBookPage(HTML5Page):
    def __init__(self, view):
        super(AddressBookPage, self).__init__(view)
        self.body.use_layout(Container())

        layout = ResponsiveLayout('md', colour_theme='dark', bg_scheme='primary')
        navbar = Navbar(view, css_id='my_nav').use_layout(layout)
        navbar.layout.set_brand_text('Address book')
        navbar.layout.add(TextNode(view, 'All your addresses in one place'))

        self.body.add_child(navbar)
        self.body.add_child(AddressBookPanel(view))


class AddressForm(Form):
    def __init__(self, view):
        super(AddressForm, self).__init__(view, 'address_form')

        inputs = self.add_child(FieldSet(view, legend_text='Add an address'))
        inputs.use_layout(FormLayout())
        
        new_address = Address()
        inputs.layout.add_input(TextInput(self, new_address.fields.name))
        inputs.layout.add_input(TextInput(self, new_address.fields.email_address))

        button = inputs.add_child(Button(self, new_address.events.save))
        button.use_layout(ButtonLayout(style='primary'))


class AddressBookPanel(Div):
    def __init__(self, view):
        super(AddressBookPanel, self).__init__(view)

        self.add_child(H(view, 1, text='Addresses'))

        self.add_child(AddressForm(view))

        for address in Session.query(Address).all():
            self.add_child(AddressBox(view, address))


class AddressBox(Widget):
    def __init__(self, view, address):
        super(AddressBox, self).__init__(view)
        self.add_child(P(view, text='%s: %s' % (address.name, address.email_address)))


class AddressBookUI(UserInterface):
    def assemble(self):
        home = self.define_view('/', title='Address book', page=AddressBookPage.factory())
        self.define_transition(Address.events.save, home, home)


class Address(Base):
    __tablename__ = 'addressbook2_address'

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
