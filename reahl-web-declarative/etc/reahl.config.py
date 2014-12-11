from __future__ import print_function, unicode_literals, absolute_import, division

from reahl.sqlalchemysupport import SqlAlchemyControl

reahlsystem.root_egg = 'reahl-web-declarative'
reahlsystem.connection_uri = 'postgresql://rhug:rhug@localhost/rhug'
#reahlsystem.connection_uri = 'sqlite://'
reahlsystem.orm_control = SqlAlchemyControl(echo=False)
#reahlsystem.debug = True



