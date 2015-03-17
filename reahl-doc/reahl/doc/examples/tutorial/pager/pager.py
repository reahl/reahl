


from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.web.fw import UserInterface
from reahl.web.ui import HTML5Page, P, H, Panel, HorizontalLayout
from reahl.web.pure import PageColumnLayout
from reahl.web.pager import SequentialPageIndex, PageMenu, PagedPanel


class AddressBookUI(UserInterface):
    def assemble(self):
        self.define_page(HTML5Page, style='basic').use_layout(PageColumnLayout('main'))
        find = self.define_view('/', title='Addresses')
        find.set_slot('main', AddressBookPanel.factory())


class AddressBookPanel(Panel):
    def __init__(self, view):
        super(AddressBookPanel, self).__init__(view)

        self.add_child(H(view, 1, text='Addresses'))

        self.page_index = SequentialPageIndex(Address.all_addresses(), items_per_page=5)
        self.address_list = AddressList(view, self.page_index)
        self.page_menu = PageMenu(view, 'page_menu', self.page_index, self.address_list).use_layout(HorizontalLayout())
        self.add_children([self.page_menu, self.address_list])


class AddressList(PagedPanel):
    def __init__(self, view, page_index):
        super(AddressList, self).__init__(view, page_index, 'addresslist')
        for address in self.current_contents:
            self.add_child(P(view, text='%s: %s' % (address.name, address.email_address)))


class Address(object):
    def __init__(self, name, email_address):
        self.name = name
        self.email_address = email_address
        
    @classmethod
    def all_addresses(cls):
        return [Address('friend %s' % i,'friend%s@some.org' % i ) for i in list(range(200))]
