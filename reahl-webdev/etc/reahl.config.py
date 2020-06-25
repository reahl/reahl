import os
from reahl.sqlalchemysupport import SqlAlchemyControl

reahlsystem.connection_uri = os.environ.get('REAHL_TEST_CONNECTION_URI', 'postgresql:///reahl')
reahlsystem.root_egg = 'reahl-webdev'
#reahlsystem.connection_uri = 'sqlite:////tmp/test.db'
#reahlsystem.connection_uri = 'sqlite:///:memory:'
reahlsystem.orm_control = SqlAlchemyControl(echo=False)



