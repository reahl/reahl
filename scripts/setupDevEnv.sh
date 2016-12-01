#!/bin/bash -e

# Setup environment
echo "export REAHLWORKSPACE=\$HOME" >> $HOME/.profile
echo "export EMAIL=noone@example.org" >> $HOME/.profile
echo "export DEBFULLNAME=\"Travis Tester\"" >> $HOME/.profile
echo "export DEBEMAIL=\$EMAIL" >> $HOME/.profile
echo "export PACKAGESIGNKEYID=DE633F86" >> $HOME/.profile
echo "export WORKON_HOME=\$HOME/virtualenv" >> $HOME/.profile
echo "export PATH=\$HOME/bin:\$PATH" >> $HOME/.profile

# User installs and config
./travis/installChromium.sh
./travis/createTestSshKey.sh
./travis/createTestGpgKey.sh

# Setup virtualenv, virtualenvwrapper 
mkdir -p $HOME/virtualenv
echo "source /usr/share/virtualenvwrapper/virtualenvwrapper.sh" >> $HOME/.profile
source $HOME/.profile
echo "workon python3.5" >> $HOME/.profile

# Create a development virtualenv
mkvirtualenv -p $(which python3.5) python3.5 || true
workon python3.5
python scripts/bootstrap.py --script-dependencies && python scripts/bootstrap.py --pip-installs

# Setup postgresql user and test database
sudo /etc/init.d/postgresql start
sudo su - postgres -c "createuser --superuser $USER"
reahl-control createdb reahl-web/etc
