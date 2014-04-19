
from reahl.web.fw import UserInterface
from reahl.web.ui import TwoColumnPage, Form, Panel, P, H, InputGroup


class AddressBookUI(UserInterface):
    def assemble(self):
        self.define_view(u'/', title=u'Addresses', page=AddressBookPage.factory())


class AddressBookPage(TwoColumnPage):
    def __init__(self, view):
        super(AddressBookPage, self).__init__(view, style=u'basic')
        self.main.add_child(AddressBookPanel(view))


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
        self.add_child(InputGroup(view, label_text=u'Add an address'))

        # More stuff needed here, like inputs and buttons!!

class AddressBox(Panel):
    def __init__(self, view, address):
        super(AddressBox, self).__init__(view)
        self.add_child(P(view, text=u'%s: %s' % (address.name, address.email_address)))


# The model from before:
import elixir
from reahl.sqlalchemysupport import Session, metadata
from reahl.component.modelinterface import Field, Event, EmailField, Action, exposed

class Address(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata)
    elixir.using_mapper_options(save_on_init=False)

    email_address = elixir.Field(elixir.UnicodeText)
    name          = elixir.Field(elixir.UnicodeText)

    def save(self):
        Session.add(self)

    @exposed
    def fields(self, fields):
        fields.name = Field(label=u'Name', required=True)
        fields.email_address = EmailField(label=u'Email', required=True)

    @exposed
    def events(self, events):
        events.save = Event(label=u'Save', action=Action(self.save))


