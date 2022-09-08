

import datetime

from reahl.web.fw import UserInterface, Widget
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import Div, H, P, FieldSet
from reahl.web.bootstrap.navbar import Navbar, ResponsiveLayout
from reahl.web.bootstrap.navs import Nav
from reahl.web.bootstrap.grid import Container
from reahl.web.bootstrap.forms import TextInput, Form, FormLayout, Button
from reahl.component.modelinterface import ExposedNames, Field, EmailField, Action, Event
from reahl.sqlalchemysupport import Session, Base
from reahl.component.i18n import Catalogue
from sqlalchemy import Column, Integer, UnicodeText, Date
import babel.dates


# Declare a Catalogue for your component
_ = Catalogue('reahl-doc')


class AddressBookPage(HTML5Page):
    def __init__(self, view):
        super().__init__(view)
        self.body.use_layout(Container())

        layout = ResponsiveLayout('md', colour_theme='dark', bg_scheme='primary')
        navbar = Navbar(view, css_id='my_nav').use_layout(layout)
        navbar.layout.set_brand_text(_('Address book'))
        navbar.layout.add(Nav(view).with_languages())

        self.body.add_child(navbar)
        self.body.add_child(AddressBookPanel(view))


class AddressForm(Form):
    def __init__(self, view):
        super().__init__(view, 'address_form')

        inputs = self.add_child(FieldSet(view, legend_text=_('Add an address')))
        inputs.use_layout(FormLayout())

        new_address = Address()
        inputs.layout.add_input(TextInput(self, new_address.fields.name))
        inputs.layout.add_input(TextInput(self, new_address.fields.email_address))

        inputs.add_child(Button(self, new_address.events.save, style='primary'))


class AddressBookPanel(Div):
    def __init__(self, view):
        super().__init__(view)

        number_of_addresses = Session.query(Address).count()
        self.add_child(H(view, 1, text=_.ngettext('Address', 'Addresses', number_of_addresses)))

        self.add_child(AddressForm(view))

        for address in Session.query(Address).all():
            self.add_child(AddressBox(view, address))


class AddressBox(Widget):
    def __init__(self, view, address):
        super().__init__(view)
        formatted_date = babel.dates.format_date(address.added_date, locale=_.current_locale)
        self.add_child(P(view, text='%s: %s (%s)' % (address.name, address.email_address, formatted_date)))


class AddressBookUI(UserInterface):
    def assemble(self):
        home = self.define_view('/', title=_('Address book'), page=AddressBookPage.factory())
        self.define_transition(Address.events.save, home, home)


class Address(Base):
    __tablename__ = 'i18nexamplebootstrap_address'

    id            = Column(Integer, primary_key=True)
    email_address = Column(UnicodeText)
    name          = Column(UnicodeText)
    added_date    = Column(Date)

    fields = ExposedNames()
    fields.name = lambda i: Field(label=_('Name'), required=True)
    fields.email_address = lambda i: EmailField(label=_('Email'), required=True)

    def save(self):
        self.added_date = datetime.date.today()
        Session.add(self)

    events = ExposedNames()
    events.save = lambda i: Event(label=_('Save'), action=Action(i.save))
