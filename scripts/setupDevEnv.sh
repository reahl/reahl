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

# User installs and config
./travis/installChromium.sh
./travis/createTestSshKey.sh
./travis/createTestGpgKey.sh
./travis/configurePip.sh

# Setup postgresql user and test database
sudo /etc/init.d/postgresql start
sudo su - postgres -c "createuser --superuser $USER"



