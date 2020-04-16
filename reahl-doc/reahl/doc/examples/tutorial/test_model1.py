

class Address:
    def __init__(self, name, email_address):
        self.name = name
        self.email_address = email_address

    def save(self, address_book):
        address_book.add_address(self)


class AddressBook:
    def __init__(self):
        self.addresses = []

    def add_address(self, address):
        self.addresses.append(address)


def test_model():
    contacts = AddressBook()
    Address('John', 'john@world.com').save(contacts)
    Address('Jane', 'jane@world.com').save(contacts)

    assert contacts.addresses[0].name == 'John'
    assert contacts.addresses[0].email_address == 'john@world.com'

    #import pdb; pdb.set_trace()
    assert contacts.addresses[1].name == 'Jane'
    assert contacts.addresses[1].email_address == 'jane@world.com'





