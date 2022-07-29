

from sqlalchemy import Column, Integer, UnicodeText

from reahl.sqlalchemysupport import Session, Base, metadata
from reahl.component.context import ExecutionContext

class Address(Base):
    __tablename__ = 'modeltests2_address'

    id            = Column(Integer, primary_key=True)
    email_address = Column(UnicodeText)
    name          = Column(UnicodeText)

    def save(self):
        Session.add(self)


def test_model():
    with ExecutionContext():

        try:
            metadata.bind = 'sqlite:///:memory:'
            metadata.create_all()

            Address(name='John', email_address='john@world.com').save()
            Address(name='Jane', email_address='jane@world.com').save()

            addresses = Session.query(Address).all()

            assert addresses[0].name == 'John'
            assert addresses[0].email_address == 'john@world.com'

            assert addresses[1].name == 'Jane'
            assert addresses[1].email_address == 'jane@world.com'

        finally:
            metadata.bind = None
