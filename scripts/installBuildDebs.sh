#!/bin/sh -ev

PYTHON_DEPS="python3 python3-venv virtualenvwrapper"

PYTHON_DEV="zlib1g-dev libfreetype6-dev dpkg-dev libyaml-dev"
LXML_DEV="build-essential python3-dev gcc cython3 libxml2-dev libxslt-dev"
MYSQL_DEV="build-essential python3-dev default-libmysqlclient-dev"
POSTGRES_DEV="postgresql-server-dev-all"

OS_DEPS_BUILD="ca-certificates wget gnupg openssh-server"
OS_DEPS_DEV="wget gnupg"

BUILD_DEPS="$PYTHON_DEPS $OS_DEPS_BUILD $OS_DEPS_DEV $PYTHON_DEV $LXML_DEV $MYSQL_DEV $POSTGRES_DEV"

export DEBIAN_FRONTEND=noninteractive

debconf-set-selections <<HERE
tzdata tzdata/Areas select Africa
tzdata tzdata/Zones/Africa select Johannesburg
locales locales/locales_to_be_generated multiselect     en_US.UTF-8 en_GB.UTF-8 en_ZA.UTF-8 UTF-8
locales locales/default_environment_locale      select  en_ZA.UTF-8
HERE

apt-get update 
apt-get install --no-install-recommends -y $BUILD_DEPS

apt-get clean
rm -rf /var/cache/apt/*

