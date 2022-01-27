import os

reahlsystem.connection_uri = os.environ.get('REAHL_TEST_CONNECTION_URI', 'postgresql:///reahl')
reahlsystem.root_egg = 'reahl-doc'
#reahlsystem.connection_uri = 'sqlite:////tmp/hj.db'
#reahlsystem.connection_uri = 'sqlite:///:memory:'
#reahlsystem.debug = True

#from reahl.sqlalchemysupport import SqlAlchemyControl
#reahlsystem.orm_control = SqlAlchemyControl(echo=True)


