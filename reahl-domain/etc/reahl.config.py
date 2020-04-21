
from reahl.sqlalchemysupport import SqlAlchemyControl

reahlsystem.root_egg = 'reahl-domain'
#reahlsystem.connection_uri = 'mysql:///reahl'
reahlsystem.connection_uri = 'postgresql:///reahl'
#reahlsystem.connection_uri = 'sqlite:////tmp/test.db'

reahlsystem.orm_control = SqlAlchemyControl(echo=False)
