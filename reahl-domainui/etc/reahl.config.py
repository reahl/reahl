
from reahl.sqlalchemysupport import SqlAlchemyControl
import os

reahlsystem.connection_uri = os.environ.get('REAHL_TEST_CONNECTION_URI', 'postgresql:///reahl')
reahlsystem.root_egg = 'reahl-domainui'
#reahlsystem.connection_uri = 'sqlite:////tmp/test.db'
reahlsystem.orm_control = SqlAlchemyControl(echo=False)



