
from reahl.web.fw import UserInterface
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import TextNode
from reahl.web.bootstrap.navbar import Navbar, ResponsiveLayout
from reahl.web.bootstrap.grid import Container


class AddressBookPage(HTML5Page):
    def __init__(self, view):
        super().__init__(view)
        self.body.use_layout(Container())

        layout = ResponsiveLayout('md', colour_theme='dark', bg_scheme='primary')
        navbar = Navbar(view, css_id='my_nav').use_layout(layout)
        navbar.layout.set_brand_text('Address book')
        navbar.layout.add(TextNode(view, 'All your addresses in one place'))

        self.body.add_child(navbar)


class AddressBookUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Address book', page=AddressBookPage.factory())

