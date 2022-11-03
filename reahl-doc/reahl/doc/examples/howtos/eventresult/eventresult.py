



from reahl.web.fw import UserInterface, CannotCreate, UrlBoundView
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import Div, H, P
from reahl.web.bootstrap.navbar import Navbar, ResponsiveLayout
from reahl.web.bootstrap.navs import Nav
from reahl.web.bootstrap.grid import Container, ColumnLayout, ColumnOptions, ResponsiveSize
from reahl.web.bootstrap.forms import TextInput, Form, FormLayout, Button, FieldSet
from reahl.component.modelinterface import ExposedNames, Field, EmailField, Action, Event, IntegerField
from reahl.sqlalchemysupport import Session, Base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import Column, Integer, UnicodeText, Boolean


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


class ReviewView(UrlBoundView):
    def assemble(self, address_id=None):
        try:
            address = Session.query(Address).filter_by(id=address_id).one()
        except NoResultFound:
            raise CannotCreate()

        self.title = 'Review %s' % address.name
        self.set_slot('main', AddressReviewForm.factory(address))


class AddressReviewForm(Form):
    def __init__(self, view, address):
        super().__init__(view, 'review_form')

        self.add_child(AddressBox(view, address))
        self.add_child(Button(self, address.events.review, style='primary'))


class AddressForm(Form):
    def __init__(self, view):
        super().__init__(view, 'address_form')

        new_address = Address()
        grouped_inputs = self.add_child(FieldSet(view, legend_text='Add an address'))
        grouped_inputs.use_layout(FormLayout())
        grouped_inputs.layout.add_input(TextInput(self, new_address.fields.name))
        grouped_inputs.layout.add_input(TextInput(self, new_address.fields.email_address))

        grouped_inputs.add_child(Button(self, new_address.events.save.with_returned_argument('address_id'), style='primary'))


class AddressBookPanel(Div):
    def __init__(self, view):
        super().__init__(view)

        self.add_child(H(view, 1, text='Addresses'))

        for address in Session.query(Address).all():
            self.add_child(AddressBox(view, address))


class AddressBox(P):
    def __init__(self, view, address):
        reviewed = ' (reviewed)' if address.reviewed else ''
        super().__init__(view, text='%s: %s%s' % (address.name, address.email_address, reviewed))


class AddressBookUI(UserInterface):
    def assemble(self):
        home = self.define_view('/', title='Show')
        add = self.define_view('/add', title='Add')
        review = self.define_view('/review', view_class=ReviewView, address_id=IntegerField())

        home.set_slot('main', AddressBookPanel.factory())
        add.set_slot('main', AddressForm.factory())

        bookmarks = [f.as_bookmark(self) for f in [home, add]]
        self.define_page(AddressBookPage, bookmarks)

        self.define_transition(Address.events.save, add, review)
        self.define_transition(Address.events.review, review, home)


class Address(Base):
    __tablename__ = 'eventresult_address'
    
    id            = Column(Integer, primary_key=True)
    email_address = Column(UnicodeText)
    name          = Column(UnicodeText)
    reviewed      = Column(Boolean)

    fields = ExposedNames()
    fields.name = lambda i: Field(label='Name', required=True)
    fields.email_address = lambda i: EmailField(label='Email', required=True)

    def save(self):
        Session.add(self)
        Session.flush()
        return self.id
        
    def review(self):
        self.reviewed = True

    events = ExposedNames()
    events.save = lambda i: Event(label='Save', action=Action(i.save), address_id=IntegerField())
    events.review = lambda i: Event(label='Mark as reviewed', action=Action(i.review))


