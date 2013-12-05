

import elixir
from sqlalchemy.orm.exc import NoResultFound

from reahl.sqlalchemysupport import Session, metadata

from reahl.web.fw import Region, Url, UrlBoundView, CannotCreate
from reahl.web.ui import TwoColumnPage, Form, TextInput, LabelledBlockInput, Button, Panel, P, H, A, InputGroup, HMenu
from reahl.component.modelinterface import exposed, EmailField, Field, Event, IntegerField, Action


class AddressBookPage(TwoColumnPage):
    def __init__(self, view, main_bookmarks):
        super(AddressBookPage, self).__init__(view, style=u'basic')
        self.header.add_child(HMenu.from_bookmarks(view, main_bookmarks))


class EditView(UrlBoundView):
    def assemble(self, address_id=None):
        try:
            address = Address.query.filter_by(id=address_id).one()
        except NoResultFound:
            raise CannotCreate()

        self.title = u'Edit %s' % address.name
        self.set_slot(u'main', EditAddressForm.factory(address))


class AddressBookApp(Region):
    def assemble(self):

        add = self.define_view(u'/add', title=u'Add an address')
        add.set_slot(u'main', AddAddressForm.factory())

        edit = self.define_view(u'/edit', view_class=EditView, address_id=IntegerField())

        addresses = self.define_view(u'/', title=u'Addresses')
        addresses.set_slot(u'main', AddressBookPanel.factory(self))

        bookmarks = [f.as_bookmark(self) for f in [addresses, add]]
        self.define_main_window(AddressBookPage, bookmarks)

        self.define_transition(Address.events.save, add, addresses)
        self.define_transition(Address.events.update, edit, addresses)

        self.edit = edit

    def get_edit_bookmark(self, address, description=None):
        return self.edit.as_bookmark(self, address_id=address.id, description=description)



class AddressBookPanel(Panel):
    def __init__(self, view, address_book_app):
        super(AddressBookPanel, self).__init__(view)

        self.add_child(H(view, 1, text=u'Addresses'))
        
        for address in Address.query.all():
            self.add_child(AddressBox(view, address, address_book_app))


class EditAddressForm(Form):
    def __init__(self, view, address):
        super(EditAddressForm, self).__init__(view, u'edit_form')

        grouped_inputs = self.add_child(InputGroup(view, label_text=u'Edit address'))
        grouped_inputs.add_child(LabelledBlockInput(TextInput(self, address.fields.name)))
        grouped_inputs.add_child(LabelledBlockInput(TextInput(self, address.fields.email_address)))

        grouped_inputs.add_child(Button(self, address.events.update))


class AddAddressForm(Form):
    def __init__(self, view):
        super(AddAddressForm, self).__init__(view, u'add_form')

        new_address = Address()
        grouped_inputs = self.add_child(InputGroup(view, label_text=u'Add an address'))
        grouped_inputs.add_child(LabelledBlockInput(TextInput(self, new_address.fields.name)))
        grouped_inputs.add_child(LabelledBlockInput(TextInput(self, new_address.fields.email_address)))

        grouped_inputs.add_child(Button(self, new_address.events.save))


class AddressBox(Panel):
    def __init__(self, view, address, address_book_app):
        super(AddressBox, self).__init__(view)

        bookmark = address_book_app.get_edit_bookmark(address=address, description=u'edit')
        par = self.add_child(P(view, text=u'%s: %s ' % (address.name, address.email_address)))
        par.add_child(A.from_bookmark(view, bookmark))


class Address(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata, tablename=u'tutorial_parameterised1_address')
    elixir.using_mapper_options(save_on_init=False)
    
    email_address = elixir.Field(elixir.UnicodeText)
    name          = elixir.Field(elixir.UnicodeText)

    @exposed
    def fields(self, fields):
        fields.name = Field(label=u'Name', required=True)
        fields.email_address = EmailField(label=u'Email', required=True)

    @exposed('save', 'update')
    def events(self, events):
        events.save = Event(label=u'Save', action=Action(self.save))
        events.update = Event(label=u'Update')

    def save(self):
        Session.add(self)


