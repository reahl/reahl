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

        Address(name=u'John', email_address=u'john@world.com').save()
        Address(name=u'Jane', email_address=u'jane@world.com').save()

        addresses = Address.query.all()

        assert addresses[0].name == u'John'
        assert addresses[0].email_address == u'john@world.com'

        assert addresses[1].name == u'Jane'
        assert addresses[1].email_address == u'jane@world.com'

