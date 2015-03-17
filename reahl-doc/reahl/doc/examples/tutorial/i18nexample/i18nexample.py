

from __future__ import print_function, unicode_literals, absolute_import, division
import datetime

from sqlalchemy import Column, Integer, UnicodeText, Date

from reahl.sqlalchemysupport import Session, Base

from reahl.web.fw import UserInterface, Widget
from reahl.web.ui import HTML5Page, Form, TextInput, LabelledBlockInput, Button, Panel, P, H, InputGroup, \
                         Menu, VerticalLayout
from reahl.web.pure import PageColumnLayout, UnitSize
from reahl.component.modelinterface import exposed, EmailField, Field, Event, Action
from reahl.component.i18n import Translator
import babel.dates 


_ = Translator('reahl-doc')


class AddressBookPage(HTML5Page):
    def __init__(self, view):
        super(AddressBookPage, self).__init__(view, style='basic')
        self.use_layout(PageColumnLayout(('secondary', UnitSize('1/4')), ('main', UnitSize('3/4'))))
        self.layout.columns['secondary'].add_child(Menu.from_languages(view).use_layout(VerticalLayout()))


class AddressBookUI(UserInterface):
    def assemble(self):
        self.define_page(AddressBookPage)
        find = self.define_view('/', title=_('Address Book'))
        find.set_slot('main', AddressBookPanel.factory())


class AddressBookPanel(Panel):
    def __init__(self, view):
        super(AddressBookPanel, self).__init__(view)

        self.add_child(H(view, 1, text=_.ngettext('Address', 'Addresses', Session.query(Address).count())))
        
        for address in Session.query(Address).all():
            self.add_child(AddressBox(view, address))

        self.add_child(AddAddressForm(view))



class AddAddressForm(Form):
    def __init__(self, view):
        super(AddAddressForm, self).__init__(view, 'add_form')

        new_address = Address()

        grouped_inputs = self.add_child(InputGroup(view, label_text=_('Add an address')))
        grouped_inputs.add_child( LabelledBlockInput(TextInput(self, new_address.fields.name)) )
        grouped_inputs.add_child( LabelledBlockInput(TextInput(self, new_address.fields.email_address)) )

        self.define_event_handler(new_address.events.save)
        grouped_inputs.add_child(Button(self, new_address.events.save))


class AddressBox(Widget):
    def __init__(self, view, address):
        super(AddressBox, self).__init__(view)
        formatted_date = babel.dates.format_date(address.added_date, locale=_.current_locale)
        self.add_child(P(view, text='%s: %s (%s)' % (address.name, address.email_address, formatted_date)))


class Address(Base):
    __tablename__ = 'i18nexample_address'
    id            = Column(Integer, primary_key=True)
    email_address = Column(UnicodeText)
    name          = Column(UnicodeText)
    added_date    = Column(Date)

    @exposed
    def fields(self, fields):
        fields.name = Field(label=_('Name'), required=True)
        fields.email_address = EmailField(label=_('Email'), required=True)

    def save(self):
        self.added_date = datetime.date.today()
        Session.add(self)
        
    @exposed
    def events(self, events):
        events.save = Event(label=_('Save'), action=Action(self.save))

