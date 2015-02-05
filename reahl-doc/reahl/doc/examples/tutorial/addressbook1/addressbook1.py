
from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.web.fw import UserInterface, Widget
from reahl.web.ui import HTML5Page, Panel, P, H
from reahl.sqlalchemysupport import Session


class AddressBookUI(UserInterface):
    def assemble(self):
        self.define_view('/', title='Addresses', page=AddressBookPage.factory())


class AddressBookPage(HTML5Page):
    def __init__(self, view):
        super(AddressBookPage, self).__init__(view, style='basic')
        self.body.add_child(AddressBookPanel(view))


class AddressBookPanel(Panel):
    def __init__(self, view):
        super(AddressBookPanel, self).__init__(view)

        self.add_child(H(view, 1, text='Addresses'))

        for address in Session.query(Address).all():
            self.add_child(AddressBox(view, address))


class AddressBox(Widget):
    def __init__(self, view, address):
        super(AddressBox, self).__init__(view)
        self.add_child(P(view, text='%s: %s' % (address.name, address.email_address)))


# The model from before:
from sqlalchemy import Column, Integer, UnicodeText
from reahl.sqlalchemysupport import Session, Base

class Address(Base):
    __tablename__ = 'addressbook1_address'

    id            = Column(Integer, primary_key=True)
    email_address = Column(UnicodeText)
    name          = Column(UnicodeText)

    def save(self):
        Session.add(self)



