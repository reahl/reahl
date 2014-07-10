
# In production this has to be set, to the name of the egg of your application:
from __future__ import unicode_literals
from __future__ import print_function
reahlsystem.root_egg = 'hellonginx'   

# If using SQLite:
reahlsystem.connection_uri = 'sqlite:////var/local/hellonginx/hellonginx.db'  

# If using PostgreSQL:
#reahlsystem.connection_uri = 'postgres://hellonginx:hellonginx@localhost/hellonginx'  
