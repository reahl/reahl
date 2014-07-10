
from __future__ import unicode_literals
from __future__ import print_function
from reahl.web.fw import UserInterface, Widget
from reahl.web.ui import TwoColumnPage, Panel, P, H


class AddressBookUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Addresses', page=AddressBookPage.factory())


class AddressBookPage(TwoColumnPage):
    def __init__(self, view):
        super(AddressBookPage, self).__init__(view, style='basic')
        self.main.add_child(AddressBookPanel(view))


class AddressBookPanel(Panel):
    def __init__(self, view):
        super(AddressBookPanel, self).__init__(view)

        self.add_child(H(view, 1, text='Addresses'))

        for address in Address.query.all():
            self.add_child(AddressBox(view, address))


class AddressBox(Widget):
    def __init__(self, view, address):
        super(AddressBox, self).__init__(view)
        self.add_child(P(view, text='%s: %s' % (address.name, address.email_address)))


# The model from before:
import elixir
from reahl.sqlalchemysupport import Session, metadata

class Address(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata)
    elixir.using_mapper_options(save_on_init=False)

    email_address = elixir.Field(elixir.UnicodeText)
    name          = elixir.Field(elixir.UnicodeText)

    def save(self):
        Session.add(self)



