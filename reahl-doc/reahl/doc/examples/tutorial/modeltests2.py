from __future__ import unicode_literals
from __future__ import print_function
from nose.tools import istest

import elixir
from reahl.sqlalchemysupport import Session, metadata
from reahl.component.context import ExecutionContext

class Address(elixir.Entity):
    elixir.using_options(session=Session, metadata=metadata)
    elixir.using_mapper_options(save_on_init=False)

    email_address = elixir.Field(elixir.UnicodeText)
    name          = elixir.Field(elixir.UnicodeText)

    def save(self):
        Session.add(self)


@istest
def test_model():
    metadata.bind = 'sqlite:///:memory:'
    elixir.setup_all()
    elixir.create_all()

    with ExecutionContext():

        Address(name='John', email_address='john@world.com').save()
        Address(name='Jane', email_address='jane@world.com').save()

        addresses = Address.query.all()

        assert addresses[0].name == 'John'
        assert addresses[0].email_address == 'john@world.com'

        assert addresses[1].name == 'Jane'
        assert addresses[1].email_address == 'jane@world.com'

