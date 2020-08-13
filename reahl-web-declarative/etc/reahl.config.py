import os

from reahl.sqlalchemysupport import SqlAlchemyControl

reahlsystem.connection_uri = os.environ.get('REAHL_TEST_CONNECTION_URI', 'postgresql:///reahl')
reahlsystem.root_egg = 'reahl-web-declarative'
#reahlsystem.connection_uri = 'sqlite://'
reahlsystem.orm_control = SqlAlchemyControl(echo=False)
#reahlsystem.debug = True



