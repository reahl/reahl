

from __future__ import print_function, unicode_literals, absolute_import, division

from sqlalchemy import Column, Integer, UnicodeText
from sqlalchemy.orm.exc import NoResultFound

from reahl.sqlalchemysupport import Session, Base

from reahl.web.fw import CannotCreate, UrlBoundView, UserInterface
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.ui import HTML5Page, Div, P, H, A
from reahl.web.bootstrap.forms import Form, TextInput, Button, FieldSet, PrimitiveCheckboxInput, FormLayout, ButtonLayout
from reahl.web.bootstrap.grid import ColumnLayout, ColumnOptions, ResponsiveSize, Container
from reahl.web.bootstrap.navs import Nav, TabLayout
from reahl.web.bootstrap.tables import Table, TableLayout
from reahl.web.ui import StaticColumn, DynamicColumn
from reahl.component.modelinterface import exposed, EmailField, Field, Event, IntegerField, Action, BooleanField


class AddressBookPage(HTML5Page):
    def __init__(self, view, main_bookmarks):
        super(AddressBookPage, self).__init__(view)
        self.use_layout(PageLayout(document_layout=Container()))
        contents_layout = ColumnLayout(ColumnOptions('main', size=ResponsiveSize(lg=6))).with_slots()
        self.layout.contents.use_layout(contents_layout)
        menu = Nav(view).use_layout(TabLayout()).with_bookmarks(main_bookmarks)
        self.layout.header.add_child(menu)


class EditView(UrlBoundView):
    def assemble(self, address_id=None):
        try:
            address = Session.query(Address).filter_by(id=address_id).one()
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


class AddressBookPanel(Div):
    def __init__(self, view, address_book_ui):
        super(AddressBookPanel, self).__init__(view)
        self.rows = self.initialise_rows()

        self.add_child(H(view, 1, text='Addresses'))
        
        form = self.add_child(Form(view, 'address_table_form'))
        self.define_event_handler(self.events.delete_selected)

        def make_link_widget(view, row):
            return A.from_bookmark(view, address_book_ui.get_edit_bookmark(row.address, description='Edit'))

        def make_checkbox_widget(view, row):
            return PrimitiveCheckboxInput(form, row.fields.selected_by_user)

        def make_delete_selected_button(view):
            return Button(form, self.events.delete_selected)

        columns = [StaticColumn(Field(label='Name'), 'name'),
                   StaticColumn(EmailField(label='Email'), 'email_address'),
                   DynamicColumn('', make_link_widget),
                   DynamicColumn(make_delete_selected_button, make_checkbox_widget)]

        table = Table(view, caption_text='All my friends', summary='Summary for screen reader')
        table.use_layout(TableLayout(striped=True))
        table.with_data(columns, self.rows)

        form.add_child(table)

    def initialise_rows(self):
        return [Row(address) for address in Session.query(Address).all()]

    @exposed
    def events(self, events):
        events.delete_selected = Event(label='Delete Selected', action=Action(self.delete_selected))

    def delete_selected(self):
        for row in self.rows:
            if row.selected_by_user:
                Session.delete(row.address)


class EditAddressForm(Form):
    def __init__(self, view, address):
        super(EditAddressForm, self).__init__(view, 'edit_form')

        grouped_inputs = self.add_child(FieldSet(view, legend_text='Edit address'))
        grouped_inputs.use_layout(FormLayout())
        grouped_inputs.layout.add_input(TextInput(self, address.fields.name))
        grouped_inputs.layout.add_input(TextInput(self, address.fields.email_address))

        btn = grouped_inputs.add_child(Button(self, address.events.update))
        btn.use_layout(ButtonLayout(style='primary'))


class AddAddressForm(Form):
    def __init__(self, view):
        super(AddAddressForm, self).__init__(view, 'add_form')

        new_address = Address()
        grouped_inputs = self.add_child(FieldSet(view, legend_text='Add an address'))
        grouped_inputs.use_layout(FormLayout())
        grouped_inputs.layout.add_input(TextInput(self, new_address.fields.name))
        grouped_inputs.layout.add_input(TextInput(self, new_address.fields.email_address))

        btn = grouped_inputs.add_child(Button(self, new_address.events.save))
        btn.use_layout(ButtonLayout(style='primary'))


class AddressBox(Form):
    def __init__(self, view, address):
        form_name = 'address_%s' % address.id  # Forms need unique names!
        super(AddressBox, self).__init__(view, form_name)

        par = self.add_child(P(view, text='%s: %s ' % (address.name, address.email_address)))
        par.add_child(Button(self, address.events.edit.with_arguments(address_id=address.id)))


class Address(Base):
    __tablename__ = 'tablebootstrap_address'

    id            = Column(Integer, primary_key=True)
    email_address = Column(UnicodeText)
    name          = Column(UnicodeText)

    @exposed
    def fields(self, fields):
        fields.name = Field(label='Name', required=True)
        fields.email_address = EmailField(label='Email', required=True)

    @exposed('save', 'update')
    def events(self, events):
        events.save = Event(label='Save', action=Action(self.save))
        events.update = Event(label='Update')

    def save(self):
        Session.add(self)





