

from __future__ import unicode_literals
from __future__ import print_function
import elixir
from sqlalchemy.orm.exc import NoResultFound

from reahl.sqlalchemysupport import Session, metadata

from reahl.web.fw import CannotCreate, UrlBoundView, UserInterface
from reahl.web.ui import Button, Form, H, HMenu, InputGroup, LabelledBlockInput, A, CheckboxInput
from reahl.web.ui import Panel, P, TextInput, TwoColumnPage, StaticColumn, DynamicColumn
from reahl.web.table import DataTable
from reahl.component.modelinterface import exposed, EmailField, Field, Event, IntegerField, Action, BooleanField


class AddressBookPage(TwoColumnPage):
    def __init__(self, view, main_bookmarks):
        super(AddressBookPage, self).__init__(view, style='basic')
        menu = HMenu.from_bookmarks(view, main_bookmarks)
        self.header.add_child(menu)


class EditView(UrlBoundView):
    def assemble(self, address_id=None):
        try:
            address = Address.query.filter_by(id=address_id).one()
        except NoResultFound:
            raise CannotCreate()

        self.title = 'Edit %s' % address.name
        self.set_slot('main', EditAddressForm.factory(address))


class AddressBookUI(UserInterface):
    def assemble(self):

        add = self.define_view('/add', title='Add an address')
        add.set_slot('main', AddAddressForm.factory())

        self.edit = self.define_view('/edit', view_class=EditView, address_id=IntegerField())

        addresses = self.define_view('/', title='Addresses')
        addresses.set_slot('main', AddressBookPanel.factory(self))

        self.define_transition(Address.events.save, add, addresses)
        self.define_transition(Address.events.update, self.edit, addresses)

        bookmarks = [f.as_bookmark(self) for f in [addresses, add]]
        self.define_page(AddressBookPage, bookmarks)

    def get_edit_bookmark(self, address, description=None):
        return self.edit.as_bookmark(self, address_id=address.id, description=description)


class Row(object):
    def __init__(self, address):
        self.address = address
        self.selected_by_user = False

    @exposed
    def fields(self, fields):
        fields.selected_by_user = BooleanField(label='')

    def __getattr__(self, name):
        return getattr(self.address, name)


class AddressBookPanel(Panel):
    def __init__(self, view, address_book_ui):
        super(AddressBookPanel, self).__init__(view)
        self.rows = self.initialise_rows()

        self.add_child(H(view, 1, text='Addresses'))
        
        def make_link_widget(view, row):
            return A.from_bookmark(view, address_book_ui.get_edit_bookmark(row.address, description='Edit'))

        columns = [StaticColumn(Field(label='Name'), 'name', sort_key=lambda x: x.address.name),
                   StaticColumn(EmailField(label='Email'), 'email_address', sort_key=lambda x: x.address.email_address),
                   StaticColumn(IntegerField(label='Zip'), 'zip_code', sort_key=lambda x: x.address.zip_code),
                   DynamicColumn('', make_link_widget)]

        data_table = DataTable(view,
                                columns,
                                self.rows,
                                caption_text='All my friends',
                                summary='Summary for screen reader',
                                css_id='address_data')
        self.add_child(data_table)

    def initialise_rows(self):
        return [Row(address) for address in Address.query.all()]


class EditAddressForm(Form):
    def __init__(self, view, address):
        super(EditAddressForm, self).__init__(view, 'edit_form')

        grouped_inputs = InputGroup(view, label_text='Edit address')
        grouped_inputs.add_child( LabelledBlockInput(TextInput(self, address.fields.name)) )
        grouped_inputs.add_child( LabelledBlockInput(TextInput(self, address.fields.email_address)) )
        self.add_child(grouped_inputs)

        grouped_inputs.add_child(Button(self, address.events.update))


class AddAddressForm(Form):
    def __init__(self, view):
        super(AddAddressForm, self).__init__(view, 'add_form')

        new_address = Address()
        grouped_inputs = InputGroup(view, label_text='Add an address')
        grouped_inputs.add_child( LabelledBlockInput(TextInput(self, new_address.fields.name)) )
        grouped_inputs.add_child( LabelledBlockInput(TextInput(self, new_address.fields.email_address)) )
        self.add_child(grouped_inputs)

        grouped_inputs.add_child(Button(self, new_address.events.save))


class AddressBox(Form):
    def __init__(self, view, address):
        form_name = 'address_%s' % address.id  # Forms need unique names!
        super(AddressBox, self).__init__(view, form_name)

        par = self.add_child(P(view, text='%s: %s ' % (address.name, address.email_address)))
        par.add_child(Button(self, address.events.edit.with_arguments(address_id=address.id)))


class Address(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata, tablename='tutorial_datatable_address')
    elixir.using_mapper_options(save_on_init=False)
    
    email_address = elixir.Field(elixir.UnicodeText)
    name          = elixir.Field(elixir.UnicodeText)
    zip_code      = elixir.Field(elixir.Integer)

    @exposed
    def fields(self, fields):
        fields.name = Field(label='Name', required=True)
        fields.email_address = EmailField(label='Email', required=True)
        fields.zip_code = IntegerField(label='Zipcode', required=True)

    @exposed('save', 'update')
    def events(self, events):
        events.save = Event(label='Save', action=Action(self.save))
        events.update = Event(label='Update')

    def save(self):
        Session.add(self)


