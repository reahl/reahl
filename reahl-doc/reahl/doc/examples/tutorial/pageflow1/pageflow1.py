
from reahl.web.fw import UserInterface, Widget
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import Div, H, P, FieldSet
from reahl.web.bootstrap.navbar import Navbar, ResponsiveLayout
from reahl.web.bootstrap.navs import Nav
from reahl.web.bootstrap.grid import Container
from reahl.web.bootstrap.forms import TextInput, Form, FormLayout, Button
from reahl.component.modelinterface import ExposedNames, Field, EmailField, Action, Event
from reahl.sqlalchemysupport import Session, Base
from sqlalchemy import Column, Integer, UnicodeText


class AddressBookPage(HTML5Page):
    def __init__(self, view, bookmarks):
        super().__init__(view)
        self.body.use_layout(Container())

        layout = ResponsiveLayout('md', colour_theme='dark', bg_scheme='primary')
        navbar = Navbar(view, css_id='my_nav').use_layout(layout)
        navbar.layout.set_brand_text('Address book')
        navbar.layout.add(Nav(view).with_bookmarks(bookmarks))

        self.body.add_child(navbar)


class HomePage(AddressBookPage):
    def __init__(self, view, main_bookmarks):
        super().__init__(view, main_bookmarks)
        self.body.add_child(AddressBookPanel(view))


class AddAddressPage(AddressBookPage):
    def __init__(self, view, main_bookmarks):
        super().__init__(view, main_bookmarks)
        self.body.add_child(AddressForm(view))


class AddressForm(Form):
    def __init__(self, view):
        super().__init__(view, 'address_form')

        inputs = self.add_child(FieldSet(view, legend_text='Add an address'))
        inputs.use_layout(FormLayout())

        new_address = Address()
        inputs.layout.add_input(TextInput(self, new_address.fields.name))
        inputs.layout.add_input(TextInput(self, new_address.fields.email_address))

        inputs.add_child(Button(self, new_address.events.save))


class AddressBookPanel(Div):
    def __init__(self, view):
        super().__init__(view)

        self.add_child(H(view, 1, text='Addresses'))

        for address in Session.query(Address).all():
            self.add_child(AddressBox(view, address))


class AddressBox(Widget):
    def __init__(self, view, address):
        super().__init__(view)
        self.add_child(P(view, text='%s: %s' % (address.name, address.email_address)))


class AddressBookUI(UserInterface):
    def assemble(self):
        home = self.define_view('/', title='Show')
        add = self.define_view('/add', title='Add')

        bookmarks = [v.as_bookmark(self) for v in [home, add]]
        home.set_page(HomePage.factory(bookmarks))
        add.set_page(AddAddressPage.factory(bookmarks))

        self.define_transition(Address.events.save, add, home)

class Address(Base):
    __tablename__ = 'pageflow1_address'

    id            = Column(Integer, primary_key=True)
    email_address = Column(UnicodeText)
    name          = Column(UnicodeText)

    fields = ExposedNames()
    fields.name = lambda i: Field(label='Name', required=True)
    fields.email_address = lambda i: EmailField(label='Email', required=True)

    def save(self):
        Session.add(self)

    events = ExposedNames()
    events.save = lambda i: Event(label='Save', action=Action(i.save))
