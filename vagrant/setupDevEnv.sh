#!/bin/bash -e

# Secure ssh access
sudo sed -Ei 's|#?\W*(PasswordAuthentication)\W+yes|\1 no|g' /etc/ssh/sshd_config
sudo sed -Ei 's|#?\W*(PermitRootLogin)\W+.*|\1 no|g' /etc/ssh/sshd_config 

# Setup environment
echo "if [ -z \"\$DISPLAY\" ]; then export DISPLAY=:100; fi" >> $HOME/.profile
echo "export REAHLWORKSPACE=\$HOME" >> $HOME/.profile
echo "export EMAIL=noone@example.org" >> $HOME/.profile
echo "export DEBFULLNAME=\"Travis Tester\"" >> $HOME/.profile
echo "export DEBEMAIL=\$EMAIL" >> $HOME/.profile
echo "export PACKAGESIGNKEYID=DE633F86" >> $HOME/.profile
echo "export WORKON_HOME=\$HOME/virtualenv" >> $HOME/.profile
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

# User installs and config
./travis/installChromium.sh
./travis/createTestSshKey.sh
./travis/createTestGpgKey.sh
./travis/configurePip.sh
./travis/setupTestGit.sh

# Setup postgresql user and test database
sudo /etc/init.d/postgresql start
sudo su - postgres -c "createuser --superuser $USER"



