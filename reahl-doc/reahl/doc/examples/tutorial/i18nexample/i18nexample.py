

import datetime

import elixir

from reahl.sqlalchemysupport import Session, metadata

from reahl.web.fw import Region
from reahl.web.ui import TwoColumnPage, Form, TextInput, LabelledBlockInput, Button, Panel, P, H, InputGroup, VMenu
from reahl.component.modelinterface import exposed, EmailField, Field, Event, Action
from reahl.component.i18n import Translator
import babel.dates 


_ = Translator(u'reahl-doc')


class AddressBookPage(TwoColumnPage):
    def __init__(self, view):
        super(AddressBookPage, self).__init__(view, style=u'basic')
        self.secondary.add_child(VMenu.from_languages(view))


class AddressBookApp(Region):
    def assemble(self):
        self.define_main_window(AddressBookPage)
        find = self.define_view(u'/', title=_(u'Address Book'))
        find.set_slot(u'main', AddressBookPanel.factory())



class AddressBookPanel(Panel):
    def __init__(self, view):
        super(AddressBookPanel, self).__init__(view)

        self.add_child(H(view, 1, text=_.ngettext(u'Address', u'Addresses', Address.query.count())))
        
        for address in Address.query.all():
            self.add_child(AddressBox(view, address))

        self.add_child(AddAddressForm(view))



class AddAddressForm(Form):
    def __init__(self, view):
        super(AddAddressForm, self).__init__(view, u'add_form')

        new_address = Address()

        grouped_inputs = self.add_child(InputGroup(view, label_text=_(u'Add an address')))
        grouped_inputs.add_child( LabelledBlockInput(TextInput(self, new_address.fields.name)) )
        grouped_inputs.add_child( LabelledBlockInput(TextInput(self, new_address.fields.email_address)) )

        self.define_event_handler(new_address.events.save)
        grouped_inputs.add_child(Button(self, new_address.events.save))


class AddressBox(Panel):
    def __init__(self, view, address):
        super(AddressBox, self).__init__(view)
        formatted_date = babel.dates.format_date(address.added_date, locale=_.current_locale)
        self.add_child(P(view, text=u'%s: %s (%s)' % (address.name, address.email_address, formatted_date)))


class Address(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata)
    elixir.using_mapper_options(save_on_init=False)
    
    email_address = elixir.Field(elixir.UnicodeText)
    name          = elixir.Field(elixir.UnicodeText)
    added_date    = elixir.Field(elixir.Date)

    @exposed
    def fields(self, fields):
        fields.name = Field(label=_(u'Name'), required=True)
        fields.email_address = EmailField(label=_(u'Email'), required=True)

    def save(self):
        self.added_date = datetime.date.today()
        Session.add(self)
        
    @exposed
    def events(self, events):
        events.save = Event(label=_(u'Save'), action=Action(self.save))

