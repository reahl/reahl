#!/bin/sh -e

# Setup postgresql user and test database
/etc/init.d/postgresql start
sudo -u postgres -- createuser --superuser $USER

/etc/init.d/mysql start
sudo mysql -uroot -- <<EOF
  CREATE USER $USER@'localhost' IDENTIFIED WITH 'auth_socket';
  GRANT PROXY on 'root' TO $USER@'localhost' WITH GRANT OPTION;
  GRANT ALL PRIVILEGES ON *.* to $USER@'localhost' WITH GRANT OPTION;
  FLUSH PRIVILEGES
EOF




