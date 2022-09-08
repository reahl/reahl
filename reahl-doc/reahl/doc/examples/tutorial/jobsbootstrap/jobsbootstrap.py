


from sqlalchemy import Column, Integer, UnicodeText, Boolean

from reahl.sqlalchemysupport import Session, Base

from reahl.web.fw import UserInterface, Widget
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import Div, P, H
from reahl.web.bootstrap.forms import Form, TextInput, Button, FormLayout, FieldSet
from reahl.web.bootstrap.grid import ColumnLayout, ColumnOptions, ResponsiveSize, Container
from reahl.component.modelinterface import ExposedNames, EmailField, Field, Event, Action


class AddressBookUI(UserInterface):
    def assemble(self):
        find = self.define_view('/', title='Addresses', page=AddressBookPage.factory())
        find.set_slot('main', AddressBookPanel.factory())


class AddressBookPage(HTML5Page):
    def __init__(self, view):
        super().__init__(view)
        self.use_layout(PageLayout(document_layout=Container()))
        contents_layout = ColumnLayout(ColumnOptions('main', size=ResponsiveSize(md=4))).with_slots()
        self.layout.contents.use_layout(contents_layout)


class AddressBookPanel(Div):
    def __init__(self, view):
        super().__init__(view)

        self.add_child(H(view, 1, text='Addresses'))

        for address in Session.query(Address).all():
            self.add_child(AddressBox(view, address))

        self.add_child(AddAddressForm(view))


class AddAddressForm(Form):
    def __init__(self, view):
        super().__init__(view, 'add_form')

        new_address = Address()

        grouped_inputs = self.add_child(FieldSet(view, legend_text='Add an address'))
        grouped_inputs.use_layout(FormLayout())
        grouped_inputs.layout.add_input(TextInput(self, new_address.fields.name))
        grouped_inputs.layout.add_input(TextInput(self, new_address.fields.email_address))

        self.define_event_handler(new_address.events.save)
        grouped_inputs.add_child(Button(self, new_address.events.save, style='primary'))


class AddressBox(Widget):
    def __init__(self, view, address):
        super().__init__(view)
        new = ' (new)' if address.added_today else ''
        self.add_child(P(view, text='%s: %s%s' % (address.name, address.email_address, new)))


class Address(Base):
    __tablename__ = 'jobsbootstrap_address'

    id            = Column(Integer, primary_key=True)
    email_address = Column(UnicodeText)
    name          = Column(UnicodeText)
    added_today   = Column(Boolean, nullable=False, default=True)

    @classmethod
    def clear_added_flags(cls):
        for address in Session.query(cls).filter_by(added_today=True):
            address.added_today = False

    fields = ExposedNames()
    fields.name = lambda i: Field(label='Name', required=True)
    fields.email_address = lambda i: EmailField(label='Email', required=True)

    events = ExposedNames()
    events.save = lambda i: Event(label='Save', action=Action(i.save))

    def save(self):
        Session.add(self)



