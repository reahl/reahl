
# In production this has to be set, to the name of the egg of your application:
from __future__ import print_function, unicode_literals, absolute_import, division
reahlsystem.root_egg = 'helloapache'   

# If using SQLite:
reahlsystem.connection_uri = 'sqlite:////var/local/helloapache/helloapache.db'  

# If using PostgreSQL:
#reahlsystem.connection_uri = 'postgresql://helloapache:helloapache@localhost/helloapache'  
