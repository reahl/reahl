

import elixir
from sqlalchemy.orm.exc import NoResultFound

from reahl.sqlalchemysupport import Session, metadata

from reahl.web.fw import UserInterface, Url, UrlBoundView, CannotCreate
from reahl.web.ui import TwoColumnPage, Form, TextInput, LabelledBlockInput, Button, Panel, P, H, A, InputGroup, HMenu
from reahl.component.modelinterface import exposed, EmailField, Field, Event, IntegerField, Action


class AddressBookPage(TwoColumnPage):
    def __init__(self, view, main_bookmarks):
        super(AddressBookPage, self).__init__(view, style=u'basic')
        menu = HMenu.from_bookmarks(view, main_bookmarks)
        self.header.add_child(menu)


class EditView(UrlBoundView):
    def assemble(self, address_id=None):
        try:
            address = Address.query.filter_by(id=address_id).one()
        except NoResultFound:
            raise CannotCreate()

        self.title = u'Edit %s' % address.name
        self.set_slot(u'main', EditAddressForm.factory(address))

    
class AddressBookUI(UserInterface):
    def assemble(self):

        add = self.define_view(u'/add', title=u'Add an address')
        add.set_slot(u'main', AddAddressForm.factory())

        edit = self.define_view(u'/edit', view_class=EditView, address_id=IntegerField())

        addresses = self.define_view(u'/', title=u'Addresses')
        addresses.set_slot(u'main', AddressBookPanel.factory())

        self.define_transition(Address.events.save, add, addresses)
        self.define_transition(Address.events.update, edit, addresses)
        self.define_transition(Address.events.edit, addresses, edit)

        bookmarks = [f.as_bookmark(self) for f in [addresses, add]]
        self.define_page(AddressBookPage, bookmarks)


class AddressBookPanel(Panel):
    def __init__(self, view):
        super(AddressBookPanel, self).__init__(view)

        self.add_child(H(view, 1, text=u'Addresses'))
        
        for address in Address.query.all():
            self.add_child(AddressBox(view, address))


class EditAddressForm(Form):
    def __init__(self, view, address):
        super(EditAddressForm, self).__init__(view, u'edit_form')

        grouped_inputs = InputGroup(view, label_text=u'Edit address')
        grouped_inputs.add_child( LabelledBlockInput(TextInput(self, address.fields.name)) )
        grouped_inputs.add_child( LabelledBlockInput(TextInput(self, address.fields.email_address)) )
        self.add_child(grouped_inputs)

        grouped_inputs.add_child(Button(self, address.events.update))


class AddAddressForm(Form):
    def __init__(self, view):
        super(AddAddressForm, self).__init__(view, u'add_form')

        new_address = Address()
        grouped_inputs = InputGroup(view, label_text=u'Add an address')
        grouped_inputs.add_child( LabelledBlockInput(TextInput(self, new_address.fields.name)) )
        grouped_inputs.add_child( LabelledBlockInput(TextInput(self, new_address.fields.email_address)) )
        self.add_child(grouped_inputs)

        grouped_inputs.add_child(Button(self, new_address.events.save))


class AddressBox(Form):
    def __init__(self, view, address):
        form_name = u'address_%s' % address.id  # Forms need unique names!
        super(AddressBox, self).__init__(view, form_name)

        par = self.add_child(P(view, text=u'%s: %s ' % (address.name, address.email_address)))
        par.add_child(Button(self, address.events.edit.with_arguments(address_id=address.id)))


class Address(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata, tablename=u'tutorial_parameterised2_address')
    elixir.using_mapper_options(save_on_init=False)
    
    email_address = elixir.Field(elixir.UnicodeText)
    name          = elixir.Field(elixir.UnicodeText)

    @exposed
    def fields(self, fields):
        fields.name = Field(label=u'Name', required=True)
        fields.email_address = EmailField(label=u'Email', required=True)

    @exposed(u'save', u'update', u'edit')
    def events(self, events):
        events.save = Event(label=u'Save', action=Action(self.save))
        events.update = Event(label=u'Update')
        events.edit = Event(label=u'Edit')

    def save(self):
        Session.add(self)


