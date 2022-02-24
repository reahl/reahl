import os

reahlsystem.root_egg = 'reahl-component'
reahlsystem.connection_uri = os.environ.get('REAHL_TEST_CONNECTION_URI', 'postgresql:///reahl')



