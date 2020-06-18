#!/bin/bash -ev

# Installs needed to develop on reahl itself

PYTHON_DEPS="python3 python3-venv virtualenvwrapper"

PYTHON_DEV="zlib1g-dev libfreetype6-dev dpkg-dev libyaml-dev"
LXML_DEV="build-essential python3-dev gcc cython libxml2-dev libxslt-dev"
MYSQL_DEV="build-essential python3-dev default-libmysqlclient-dev"
POSTGRES_DEV="postgresql-server-dev-all"

MYSQL="mysql-client"
POSTGRES="postgresql-client"
SQLITE="sqlite3 libsqlite3-0"

OS_DEPS="ca-certificates sudo xauth libexif12"
OS_DEPS_BUILD="ca-certificates wget gnupg"
OS_DEPS_DEV="wget gnupg"


RUNTIME_DEPS="$OS_DEPS $PYTHON_DEPS"
BUILD_DEPS="$OS_DEPS_BUILD $PYTHON_DEV $LXML_DEV $MYSQL_DEV $POSTGRES_DEV"

DEV_ENV="openssh-server openssh-client xpra x11-utils firefox firefox-geckodriver screen unzip git apt-utils"


export DEBIAN_FRONTEND=noninteractive

debconf-set-selections <<HERE
tzdata tzdata/Areas select Africa
tzdata tzdata/Zones/Africa select Johannesburg
locales locales/locales_to_be_generated multiselect     en_US.UTF-8 en_GB.UTF-8 en_ZA.UTF-8 UTF-8
locales locales/default_environment_locale      select  en_ZA.UTF-8
HERE

apt-get update 
apt-get install --no-install-recommends -y $BUILD_DEPS

wget https://xpra.org/gpg.asc -O- | apt-key add
wget https://xpra.org/repos/focal/xpra.list -O- > /etc/apt/sources.list.d/xpra.list

apt-get update 
apt-get install --no-install-recommends -y $RUNTIME_DEPS $DEV_ENV $MYSQL $POSTGRES $SQLITE


apt-get clean
rm -rf /var/cache/apt/*

