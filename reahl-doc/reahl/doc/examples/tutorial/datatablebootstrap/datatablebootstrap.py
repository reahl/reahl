


from sqlalchemy import Column, Integer, UnicodeText
from sqlalchemy.orm.exc import NoResultFound

from reahl.sqlalchemysupport import Session, Base, QueryAsSequence

from reahl.web.fw import CannotCreate, UrlBoundView, UserInterface
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import Div, P, H, A
from reahl.web.bootstrap.forms import Form, TextInput, Button, FieldSet, FormLayout
from reahl.web.bootstrap.grid import ColumnLayout, ColumnOptions, ResponsiveSize, Container
from reahl.web.bootstrap.navs import Nav, TabLayout
from reahl.web.bootstrap.tables import DataTable, TableLayout
from reahl.web.ui import StaticColumn, DynamicColumn
from reahl.component.modelinterface import ExposedNames, EmailField, Field, Event, IntegerField, Action, BooleanField


class AddressBookPage(HTML5Page):
    def __init__(self, view, main_bookmarks):
        super().__init__(view)
        self.use_layout(PageLayout(document_layout=Container()))
        contents_layout = ColumnLayout(ColumnOptions('main', ResponsiveSize(lg=6))).with_slots()
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


class Row:
    def __init__(self, address):
        self.address = address
        self.selected_by_user = False

    fields = ExposedNames()
    fields.selected_by_user = lambda i: BooleanField(label='')

    def __getattr__(self, name):
        return getattr(self.address, name)


class AddressBookPanel(Div):
    def __init__(self, view, address_book_ui):
        super().__init__(view)
        self.rows = QueryAsSequence(Session.query(Address).order_by(Address.id), map_function=lambda address: Row(address))

        self.add_child(H(view, 1, text='Addresses'))
        
        def make_link_widget(view, row):
            return A.from_bookmark(view, address_book_ui.get_edit_bookmark(row.address, description='Edit'))

        columns = [StaticColumn(Field(label='Name'), 'name', sort_key=Address.name),
                   StaticColumn(EmailField(label='Email'), 'email_address', sort_key=Address.email_address),
                   StaticColumn(IntegerField(label='Zip'), 'zip_code', sort_key=Address.zip_code),
                   DynamicColumn('', make_link_widget)]

        table_layout = TableLayout(striped=True)
        data_table = DataTable(view,
                                columns,
                                self.rows,
                                caption_text='All my friends',
                                summary='Summary for screen reader',
                                table_layout=table_layout,
                                css_id='address_data')
        self.add_child(data_table)



class EditAddressForm(Form):
    def __init__(self, view, address):
        super().__init__(view, 'edit_form')

        grouped_inputs = self.add_child(FieldSet(view, legend_text='Edit address'))
        grouped_inputs.use_layout(FormLayout())
        grouped_inputs.layout.add_input(TextInput(self, address.fields.name))
        grouped_inputs.layout.add_input(TextInput(self, address.fields.email_address))

        grouped_inputs.add_child(Button(self, address.events.update, style='primary'))


class AddAddressForm(Form):
    def __init__(self, view):
        super().__init__(view, 'add_form')

        new_address = Address()
        grouped_inputs = self.add_child(FieldSet(view, legend_text='Add an address'))
        grouped_inputs.use_layout(FormLayout())
        grouped_inputs.layout.add_input(TextInput(self, new_address.fields.name))
        grouped_inputs.layout.add_input(TextInput(self, new_address.fields.email_address))

        grouped_inputs.add_child(Button(self, new_address.events.save, style='primary'))


class AddressBox(Form):
    def __init__(self, view, address):
        form_name = 'address_%s' % address.id  # Forms need unique names!
        super().__init__(view, form_name)

        par = self.add_child(P(view, text='%s: %s ' % (address.name, address.email_address)))
        par.add_child(Button(self, address.events.edit.with_arguments(address_id=address.id)))


class Address(Base):
    __tablename__ = 'datatablebootstrap_address'

    id            = Column(Integer, primary_key=True)
    email_address = Column(UnicodeText)
    name          = Column(UnicodeText)
    zip_code      = Column(Integer)

    fields = ExposedNames()
    fields.name = lambda i: Field(label='Name', required=True)
    fields.email_address = lambda i: EmailField(label='Email', required=True)
    fields.zip_code = lambda i: IntegerField(label='Zipcode', required=True)

    events = ExposedNames()
    events.save = lambda i: Event(label='Save', action=Action(i.save))
    events.update = lambda i: Event(label='Update')

    def save(self):
        Session.add(self)

