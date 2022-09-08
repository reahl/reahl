



from reahl.web.fw import UserInterface, Widget, CannotCreate, UrlBoundView
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import Div, H, P, A
from reahl.web.bootstrap.navbar import Navbar, ResponsiveLayout
from reahl.web.bootstrap.navs import Nav
from reahl.web.bootstrap.grid import Container, ColumnLayout, ColumnOptions, ResponsiveSize
from reahl.web.bootstrap.forms import TextInput, Form, FormLayout, Button, FieldSet
from reahl.component.modelinterface import ExposedNames, Field, EmailField, Action, Event, IntegerField
from reahl.sqlalchemysupport import Session, Base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import Column, Integer, UnicodeText


class AddressBookPage(HTML5Page):
    def __init__(self, view, bookmarks):
        super().__init__(view)
        self.use_layout(PageLayout(document_layout=Container()))
        contents_layout = ColumnLayout(ColumnOptions('main', size=ResponsiveSize())).with_slots()
        self.layout.contents.use_layout(contents_layout)

        layout = ResponsiveLayout('md', colour_theme='dark', bg_scheme='primary')
        navbar = Navbar(view, css_id='my_nav').use_layout(layout)
        navbar.layout.set_brand_text('Address book')
        navbar.layout.add(Nav(view).with_bookmarks(bookmarks))

        self.layout.header.add_child(navbar)


class EditView(UrlBoundView):
    def assemble(self, address_id=None):
        try:
            address = Session.query(Address).filter_by(id=address_id).one()
        except NoResultFound:
            raise CannotCreate()

        self.title = 'Edit %s' % address.name
        self.set_slot('main', EditAddressForm.factory(address))


class EditAddressForm(Form):
    def __init__(self, view, address):
        super().__init__(view, 'edit_form')

        grouped_inputs = self.add_child(FieldSet(view, legend_text='Edit address'))
        grouped_inputs.use_layout(FormLayout())
        grouped_inputs.layout.add_input(TextInput(self, address.fields.name))
        grouped_inputs.layout.add_input(TextInput(self, address.fields.email_address))

        grouped_inputs.add_child(Button(self, address.events.update, style='primary'))


class AddressForm(Form):
    def __init__(self, view):
        super().__init__(view, 'address_form')

        new_address = Address()
        grouped_inputs = self.add_child(FieldSet(view, legend_text='Add an address'))
        grouped_inputs.use_layout(FormLayout())
        grouped_inputs.layout.add_input(TextInput(self, new_address.fields.name))
        grouped_inputs.layout.add_input(TextInput(self, new_address.fields.email_address))

        grouped_inputs.add_child(Button(self, new_address.events.save, style='primary'))


class AddressBookPanel(Div):
    def __init__(self, view, address_book_ui):
        super().__init__(view)

        self.add_child(H(view, 1, text='Addresses'))

        for address in Session.query(Address).all():
            self.add_child(AddressBox(view, address, address_book_ui))


class AddressBox(Widget):
    def __init__(self, view, address, address_book_ui):
        super().__init__(view)
        bookmark = address_book_ui.get_edit_bookmark(address=address, description='edit')
        paragraph = self.add_child(P(view, text='%s: %s ' % (address.name, address.email_address)))
        paragraph.add_child(A.from_bookmark(view, bookmark))


class AddressBookUI(UserInterface):
    def assemble(self):
        home = self.define_view('/', title='Show')
        add = self.define_view('/add', title='Add')
        edit = self.define_view('/edit', view_class=EditView, address_id=IntegerField())

        home.set_slot('main', AddressBookPanel.factory(self))
        add.set_slot('main', AddressForm.factory())

        bookmarks = [f.as_bookmark(self) for f in [home, add]]
        self.define_page(AddressBookPage, bookmarks)

        self.define_transition(Address.events.save, add, home)
        self.define_transition(Address.events.update, edit, home)

        self.edit = edit

    def get_edit_bookmark(self, address, description=None):
        return self.edit.as_bookmark(self, address_id=address.id, description=description)


class Address(Base):
    __tablename__ = 'parameterised1_address'

    id            = Column(Integer, primary_key=True)
    email_address = Column(UnicodeText)
    name          = Column(UnicodeText)

    fields = ExposedNames()
    fields.name = lambda i: Field(label='Name', required=True)
    fields.email_address = lambda i: EmailField(label='Email', required=True)

    def save(self):
        Session.add(self)

    events = ExposedNames()
    events.save = lambda i: Event(label='Save', action=Action(i.save))
    events.update = lambda i: Event(label='Update')
