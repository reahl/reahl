#!/bin/bash -ev

MYSQL="mysql-client"
POSTGRES="postgresql-client"
SQLITE="sqlite3 libsqlite3-0"
DEV_ENV="virtualenvwrapper openssh-server openssh-client xpra x11-utils firefox firefox-geckodriver screen unzip git apt-utils"

export DEBIAN_FRONTEND=noninteractive
apt-get update 
apt-get install --no-install-recommends -y gnupg2 wget

wget https://xpra.org/gpg.asc -O- | apt-key add
wget https://xpra.org/repos/focal/xpra.list -O - > /etc/apt/sources.list.d/xpra.list

apt-get update 
apt-get install --no-install-recommends -y $DEV_ENV $MYSQL $POSTGRES $SQLITE
apt-get clean
rm -rf /var/cache/apt/*

