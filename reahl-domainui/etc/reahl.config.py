from __future__ import print_function, unicode_literals, absolute_import, division

from reahl.sqlalchemysupport import SqlAlchemyControl

reahlsystem.root_egg = 'reahl-domainui'
reahlsystem.connection_uri = 'postgresql:///reahl'
#reahlsystem.connection_uri = 'sqlite:////tmp/test.db'
reahlsystem.orm_control = SqlAlchemyControl(echo=False)



