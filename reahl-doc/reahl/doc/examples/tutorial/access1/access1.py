
from __future__ import unicode_literals
from __future__ import print_function
import elixir

from reahl.sqlalchemysupport import Session, metadata
from reahl.systemaccountmodel import EmailAndPasswordSystemAccount


class Address(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata)
    elixir.using_mapper_options(save_on_init=False)
    
    address_book  = elixir.ManyToOne('reahl.doc.examples.tutorial.access1.access1.AddressBook')
    email_address = elixir.Field(elixir.UnicodeText)
    name          = elixir.Field(elixir.UnicodeText)

    def save(self):
        Session.add(self)

        


class AddressBook(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata)

    owner      = elixir.ManyToOne(EmailAndPasswordSystemAccount, required=True)

    @classmethod
    def owned_by(cls, account):
        return cls.query.filter_by(owner=account)
        
    @classmethod
    def address_books_visible_to(cls, account):
        visible_books = cls.query.join(Collaborator).filter(Collaborator.account == account).all()
        visible_books.extend(cls.owned_by(account))
        return visible_books

    # See https://groups.google.com/forum/?fromgroups=#!topic/sqlelixir/ZlR9Kvcor6Q
    #    addresses  = elixir.OneToMany(Address)
    @property
    def addresses(self):
        return Address.query.filter_by(address_book=self).all()

    collaborators = elixir.OneToMany('reahl.doc.examples.tutorial.access1.access1.Collaborator', lazy='dynamic')

    def allow(self, account, can_add_addresses=False, can_edit_addresses=False):
        Collaborator.query.filter_by(address_book=self, account=account).delete()
        Collaborator(address_book=self, account=account,
            can_add_addresses=can_add_addresses,
            can_edit_addresses=can_edit_addresses)

    def can_be_edited_by(self, account):
        if account is self.owner: 
            return True
            
        collaborator = self.get_collaborator(account)
        return (collaborator and collaborator.can_edit_addresses) or self.can_be_added_to_by(account)

    def can_be_added_to_by(self, account):
        if account is self.owner: 
            return True

        collaborator = self.get_collaborator(account)
        return collaborator and collaborator.can_add_addresses
        
    def collaborators_can_be_added_by(self, account):
        return self.owner is account

    def is_visible_to(self, account):
        return self in self.address_books_visible_to(account)

    def get_collaborator(self, account):            
        collaborators = self.collaborators.filter_by(account=account)
        count = collaborators.count()
        if count == 1:
            return collaborators.one()
        if count > 1:
            raise ProgrammerError('There can be only one Collaborator per account. Here is more than one.')
        return None


class Collaborator(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata)

    account = elixir.ManyToOne(EmailAndPasswordSystemAccount)
    can_add_addresses = elixir.Field(elixir.Boolean, default=False)
    can_edit_addresses = elixir.Field(elixir.Boolean, default=False)

    address_book = elixir.ManyToOne(AddressBook)


