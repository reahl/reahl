import sys
from reahl.component.config import StoredConfiguration
from reahl.component.dbutils import SystemControl
from reahl.sqlalchemysupport import Session, metadata
from reahl.component.context import ExecutionContext

from reahl.doc.examples.tutorial.migrationexamplebootstrap.migrationexamplebootstrap import Address

config = StoredConfiguration(sys.argv[1])
config.configure()
with ExecutionContext() as context:
    context.config = config
    context.system_control = SystemControl(config)

    try:
        context.system_control.orm_control.connect()
        metadata.create_all()

        Session.add(Address(name='John Doe', email_address='johndoe@some.org'))
        Session.add(Address(name='Jane Johnson', email_address='janejohnson@some.org'))
        Session.add(Address(name='Jack Black', email_address='jackblack@some.org'))

        context.system_control.orm_control.commit()

    finally:
        context.system_control.orm_control.disconnect()

