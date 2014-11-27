
from reahl.sqlalchemysupport import SqlAlchemyControl

reahlsystem.root_egg = 'reahl-web'
reahlsystem.connection_uri = 'postgresql://rhug:rhug@localhost/rhug'
#reahlsystem.connection_uri = 'sqlite:////tmp/test.db'
#reahlsystem.connection_uri = 'sqlite:///:memory:'
reahlsystem.orm_control = SqlAlchemyControl(echo=False)



