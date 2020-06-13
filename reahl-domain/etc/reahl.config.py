import os
from reahl.sqlalchemysupport import SqlAlchemyControl

reahlsystem.connection_uri = os.environ.get('REAHL_TEST_CONNECTION_URI', 'postgresql:///reahl')
reahlsystem.root_egg = 'reahl-domain'
#reahlsystem.connection_uri = 'mysql:///reahl'
#reahlsystem.connection_uri = 'sqlite:////tmp/test.db'

reahlsystem.orm_control = SqlAlchemyControl(echo=False)
