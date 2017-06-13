
from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.tofu import expected, NoException


from sqlalchemy import Column, Integer, UnicodeText

from reahl.sqlalchemysupport import Session, Base, metadata
from reahl.component.modelinterface import exposed, EmailField, Field, Event, Action
from reahl.component.context import ExecutionContext


class Address(Base):
    __tablename__ = 'modeltests3_address'

    id            = Column(Integer, primary_key=True)
    email_address = Column(UnicodeText)
    name          = Column(UnicodeText)

    def save(self):
        Session.add(self)

    @exposed
    def fields(self, fields):
        fields.name = Field(label='Name', required=True)
        fields.email_address = EmailField(label='Email', required=True)

    @exposed
    def events(self, events):
        events.save = Event(label='Save', action=Action(self.save))


def test_reahl_additions():
    ExecutionContext().install()

    try:
        metadata.bind = 'sqlite:///:memory:'
        metadata.create_all()

        address = Address()
        Session.add(address)
        email_field = address.fields.email_address

        # While a programmer would not usually write code like this,
        # it is useful to show how the framework can use Fields and Events
        # to obtain more information about a certain Field/Event:
        assert email_field.label == 'Email'

        # Fields are used (amongst other things) to validate user input:
        with expected(Exception):
            email_field.from_input('invalid email address')

        with expected(NoException):
            assert address.email_address == None
            email_field.from_input('valid@email.com')
            assert address.email_address == 'valid@email.com'

        # After input was given, the field is set on the object it belongs to:
        # (The value set is a marshalled version of the user input. In this case it is just
        #  a string again, but it could have been, for example an EmailAddress object,
        #  and Integer, or a Date.)
        assert address.email_address == 'valid@email.com'

    finally:
        metadata.bind = None
