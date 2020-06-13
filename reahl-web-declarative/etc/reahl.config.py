
from reahl.sqlalchemysupport import SqlAlchemyControl

reahlsystem.root_egg = 'reahl-web-declarative'
#reahlsystem.connection_uri = 'postgresql:///reahl'
reahlsystem.connection_uri = 'postgresql://reahl:reahl@postgres/reahl'
#reahlsystem.connection_uri = 'sqlite://'
reahlsystem.orm_control = SqlAlchemyControl(echo=False)
#reahlsystem.debug = True



