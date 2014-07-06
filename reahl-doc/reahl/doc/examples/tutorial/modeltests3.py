from __future__ import unicode_literals
from __future__ import print_function
from nose.tools import istest
from reahl.tofu import expected, NoException

import elixir
from reahl.sqlalchemysupport import Session, metadata
from reahl.component.modelinterface import exposed, EmailField, Field, Event, Action
from reahl.component.context import ExecutionContext


class Address(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata)
    elixir.using_mapper_options(save_on_init=False)

    email_address = elixir.Field(elixir.UnicodeText)
    name          = elixir.Field(elixir.UnicodeText)

    def save(self):
        Session.add(self)

    @exposed
    def fields(self, fields):
        fields.name = Field(label='Name', required=True)
        fields.email_address = EmailField(label='Email', required=True)

    @exposed
    def events(self, events):
        events.save = Event(label='Save', action=Action(self.save))


@istest
def test_reahl_additions():

    metadata.bind = 'sqlite:///:memory:'
    elixir.setup_all()
    elixir.create_all()

    with ExecutionContext():

        address = Address()
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
