from __future__ import print_function, unicode_literals, absolute_import, division
import os

# In production this has to be set, to the name of the egg of your application:
reahlsystem.root_egg = 'helloanywhere'   

# If using SQLite:
reahlsystem.connection_uri = 'sqlite:///%s/helloanywhere.db' % os.environ['HOME']

# If using PostgreSQL:
#reahlsystem.connection_uri = 'postgresql://helloanywhere:helloanywhere@localhost/helloanywhere'  
