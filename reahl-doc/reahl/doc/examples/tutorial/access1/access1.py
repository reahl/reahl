
from __future__ import print_function, unicode_literals, absolute_import, division

from sqlalchemy import Column, ForeignKey, Integer, UnicodeText, Boolean
from sqlalchemy.orm import relationship, backref

from reahl.sqlalchemysupport import Session, Base
from reahl.domain.systemaccountmodel import EmailAndPasswordSystemAccount


class Address(Base):
    __tablename__ = 'access1_address'

    id              = Column(Integer, primary_key=True)    
    address_book_id = Column(Integer, ForeignKey('access1_address_book.id'))
    address_book    = relationship('reahl.doc.examples.tutorial.access1.access1.AddressBook')
    email_address   = Column(UnicodeText)
    name            = Column(UnicodeText)

    def save(self):
        Session.add(self)


class AddressBook(Base):
    __tablename__ = 'access1_address_book'

    id              = Column(Integer, primary_key=True)

    owner_id   = Column(Integer, ForeignKey(EmailAndPasswordSystemAccount.id), nullable=False)
    owner      = relationship(EmailAndPasswordSystemAccount)
    collaborators = relationship('reahl.doc.examples.tutorial.access1.access1.Collaborator', lazy='dynamic',
                                 backref='address_book')

    @classmethod
    def owned_by(cls, account):
        return Session.query(cls).filter_by(owner=account)
        
    @classmethod
    def address_books_visible_to(cls, account):
        visible_books = Session.query(cls).join(Collaborator).filter(Collaborator.account == account).all()
        visible_books.extend(cls.owned_by(account))
        return visible_books

    @property
    def addresses(self):
        return Session.query(Address).filter_by(address_book=self).all()

    def allow(self, account, can_add_addresses=False, can_edit_addresses=False):
        Session.query(Collaborator).filter_by(address_book=self, account=account).delete()
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


class Collaborator(Base):
    __tablename__ = 'access1_collaborator'
    id      = Column(Integer, primary_key=True)

    address_book_id = Column(Integer, ForeignKey(AddressBook.id))

    account_id = Column(Integer, ForeignKey(EmailAndPasswordSystemAccount.id), nullable=False)
    account = relationship(EmailAndPasswordSystemAccount)
    
    can_add_addresses = Column(Boolean, default=False)
    can_edit_addresses = Column(Boolean, default=False)




