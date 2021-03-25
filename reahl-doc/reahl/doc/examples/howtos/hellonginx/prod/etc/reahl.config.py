
# In production this has to be set, to the name of the egg of your application:
reahlsystem.root_egg = 'hellonginx'   

# If using SQLite:
reahlsystem.connection_uri = 'sqlite:////var/local/hellonginx/hellonginx.db'  

# If using PostgreSQL:
#reahlsystem.connection_uri = 'postgresql://hellonginx:hellonginx@localhost/hellonginx'  

reahlsystem.debug = False

#reahl.component.config.ConfigurationException: reahlsystem.debug has been defaulted to a value not suitable for production use: "True". You can set it in /etc/reahl.d/hellonginx/reahl.config.py
