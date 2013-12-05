from nose.tools import istest

class Address(object):
    def __init__(self, name, email_address):
        self.name = name
        self.email_address = email_address

    def save(self, address_book):
        address_book.add_address(self)


class AddressBook(object):
    def __init__(self):
        self.addresses = []

    def add_address(self, address):
        self.addresses.append(address)




@istest
def test_model():
    contacts = AddressBook()
    Address(u'John', u'john@world.com').save(contacts)
    Address(u'Jane', u'jane@world.com').save(contacts)

    assert contacts.addresses[0].name == u'John'
    assert contacts.addresses[0].email_address == u'john@world.com'

    #import pdb; pdb.set_trace()
    assert contacts.addresses[1].name == u'Jane'
    assert contacts.addresses[1].email_address == u'jane@world.com'





