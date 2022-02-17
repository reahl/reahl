#!/bin/sh -ev

MYSQL="default-libmysqlclient-dev mysql-client"
POSTGRES="postgresql-client"
SQLITE="sqlite3 libsqlite3-0"
DEV_ENV="virtualenvwrapper openssh-server openssh-client xpra python3-paramiko x11-utils firefox firefox-geckodriver screen unzip git apt-utils plantuml graphviz vim less"

export DEBIAN_FRONTEND=noninteractive
apt-get update 
apt-get install --no-install-recommends -y gnupg2 wget

wget https://xpra.org/gpg.asc -O- | apt-key add
wget https://xpra.org/repos/focal/xpra.list -O - > /etc/apt/sources.list.d/xpra.list

apt-get update --allow-releaseinfo-change-origin

#in github actions env this seems to be preinstalled: https://github.com/actions/virtual-environments/pull/4674
#and causes the script to break when installing mysql-client with apt.
if dpkg-query --show  "mysql-client"
then
  MYSQL="default-libmysqlclient-dev"
fi


apt-get install --no-install-recommends -y $DEV_ENV $MYSQL $POSTGRES $SQLITE
apt-get clean
rm -rf /var/cache/apt/*

