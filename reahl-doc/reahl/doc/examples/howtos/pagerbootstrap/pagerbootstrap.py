

from reahl.web.fw import UserInterface
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import P, H, Div
from reahl.web.bootstrap.grid import ResponsiveSize, ColumnLayout, ColumnOptions, Container
from reahl.web.bootstrap.pagination import PagedPanel, SequentialPageIndex, PageMenu


class AddressBookUI(UserInterface):
    def assemble(self):
        page_layout = PageLayout(document_layout=Container(),
                                 contents_layout=ColumnLayout(ColumnOptions('main', size=ResponsiveSize(lg=6))).with_slots())
        self.define_page(HTML5Page).use_layout(page_layout)
        find = self.define_view('/', title='Addresses')
        find.set_slot('main', AddressBookPanel.factory())


class AddressBookPanel(Div):
    def __init__(self, view):
        super().__init__(view)

        self.add_child(H(view, 1, text='Addresses'))

        self.page_index = SequentialPageIndex(Address.all_addresses(), items_per_page=5)
        self.address_list = AddressList(view, self.page_index)
        self.page_menu = PageMenu(view, 'page_menu', self.page_index, self.address_list)

        self.add_children([self.page_menu, self.address_list])


class AddressList(PagedPanel):
    def __init__(self, view, page_index):
        super().__init__(view, page_index, 'addresslist')
        for address in self.current_contents:
            self.add_child(P(view, text='%s: %s' % (address.name, address.email_address)))


class Address:
    def __init__(self, name, email_address):
        self.name = name
        self.email_address = email_address

    @classmethod
    def all_addresses(cls):
        return [Address('friend %s' % i,'friend%s@some.org' % i ) for i in list(range(200))]
