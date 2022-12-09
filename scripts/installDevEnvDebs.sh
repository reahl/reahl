#!/bin/sh -ev

MYSQL="default-libmysqlclient-dev mysql-client"
POSTGRES="postgresql-client"
SQLITE="sqlite3 libsqlite3-0"
DEV_ENV="virtualenvwrapper openssh-server openssh-client xpra python3-paramiko x11-utils firefox screen unzip git apt-utils plantuml graphviz vim less"

export DEBIAN_FRONTEND=noninteractive
apt-get update 
apt-get install --no-install-recommends -y gnupg2 wget


#in github actions env this seems to be preinstalled: https://github.com/actions/virtual-environments/pull/4674
#and causes the script to break when installing mysql-client with apt.
if dpkg-query --show  "mysql-client"
then
  MYSQL="default-libmysqlclient-dev"
fi


apt-get install --no-install-recommends -y $DEV_ENV $MYSQL $POSTGRES $SQLITE
apt-get clean
rm -rf /var/cache/apt/*

#fix for geckodriver not included in ubuntu 22.04 repo (firefox-geckodriver). https://bugs.launchpad.net/ubuntu/+source/firefox/+bug/1968266
wget https://github.com/mozilla/geckodriver/releases/download/v0.32.0/geckodriver-v0.32.0-linux64.tar.gz
sudo tar -xzvf geckodriver-v0.32.0-linux64.tar.gz -C /usr/local/bin
chmod +x /usr/local/bin/geckodriver

