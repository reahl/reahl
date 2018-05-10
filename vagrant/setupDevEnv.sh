#!/bin/bash -e


# Setup environment
echo "if [ -z \"\$DISPLAY\" ]; then export DISPLAY=:100; fi" >> $HOME/.profile
echo "export REAHLWORKSPACE=\$HOME" >> $HOME/.profile
echo "export EMAIL=noone@example.org" >> $HOME/.profile
echo "export DEBFULLNAME=\"Travis Tester\"" >> $HOME/.profile
echo "export DEBEMAIL=\$EMAIL" >> $HOME/.profile
echo "export PACKAGESIGNKEYID=DE633F86" >> $HOME/.profile
echo "export PATH=\$HOME/bin:\$PATH" >> $HOME/.profile
source $HOME/.profile

cat <<'EOF' >> $HOME/.profile

# Start xpra if necessary
if ! xdpyinfo -display $DISPLAY 1>/dev/null 2>&1; then 
  echo "There is no display server running on $DISPLAY, starting xpra"
  xpra start --sharing=yes $DISPLAY 1>/dev/null 2>&1
fi

# Show fingerprints of current vagrant host
echo 
echo "The fingerprints of the vagrant host are:"
echo "========================================="
for i in $(ls /etc/ssh/ssh_host_*.pub); do
    for e in md5 sha256; do
        ssh-keygen -l -E $e -f $i;
    done
done
EOF

cat << 'EOF' >> $HOME/.screenrc
hardstatus on
hardstatus alwayslastline
hardstatus string "%{.bW}%-w%{.rW}%n %t%{-}%+w %=%{..G} %H %{..Y} %m/%d %C%a "
EOF

# User installs and config
./travis/installChromium.sh
./travis/createTestSshKey.sh
./travis/createTestGpgKey.sh
./travis/configurePip.sh
./travis/setupTestGit.sh

# Setup postgresql user and test database
sudo systemctl start postgresql
sudo su - postgres -c "createuser --superuser $USER"

sudo systemctl start mysql 
sudo mysql -uroot <<EOF
  CREATE USER $USER@'localhost' IDENTIFIED WITH 'auth_socket';
  GRANT PROXY on 'root' TO $USER@'localhost' WITH GRANT OPTION;
  GRANT ALL PRIVILEGES ON *.* to $USER@'localhost' WITH GRANT OPTION;
  FLUSH PRIVILEGES
EOF




