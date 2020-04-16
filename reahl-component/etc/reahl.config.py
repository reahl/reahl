from reahl.sqlalchemysupport import SqlAlchemyControl

reahlsystem.root_egg = 'reahl-component'
#reahlsystem.connection_uri = 'postgresql:///reahl'
reahlsystem.connection_uri = 'sqlite:///:memory:'

reahlsystem.orm_control = SqlAlchemyControl(echo=False)
