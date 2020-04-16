import os

# In production this has to be set, to the name of the egg of your application:
reahlsystem.root_egg = 'helloanywhere'   
reahlsystem.debug = False

# If using SQLite:
reahlsystem.connection_uri = 'sqlite:///%s/helloanywhere.db' % os.path.expanduser('~')

# If using MySql:
# reahlsystem.connection_uri = 'mysql://myname:mydatabasepassword@myname.mysql.pythonanywhere-services.com/helloanywhere'

# If using PostgreSQL:
#reahlsystem.connection_uri = 'postgresql://myname:mydatabasepassword@myname-somenumber.postgres.pythonanywhere-services.com/helloanywhere'

