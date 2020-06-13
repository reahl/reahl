#!/bin/bash -ev

# Installs needed to develop on reahl itself

PYTHON_DEPS="python3 python3-venv virtualenvwrapper python3-dev gcc cython libxml2-dev libxslt-dev libsqlite3-0 sqlite3 postgresql-server-dev-all zlib1g-dev libfreetype6-dev build-essential openssh-client dpkg-dev postgresql libyaml-dev mysql-client mysql-server libmysqlclient-dev"
UTILS="screen unzip git apt-utils"

# For X11 forwarding to work and other misc stuff we need
#OS_DEPS="xauth dmidecode xpra libexif12 python-rencode x11-utils"
OS_DEPS="sudo gnupg wget openssh-server xauth dmidecode libexif12 x11-utils firefox firefox-geckodriver"


while (ps aux | grep apt | grep -qv grep )
do
  echo 'Waiting for systemd daily apt jobs to complete'; sleep 1;
done

export DEBIAN_FRONTEND=noninteractive

debconf-set-selections <<HERE
tzdata tzdata/Areas select Africa
tzdata tzdata/Zones/Africa select Johannesburg
locales locales/locales_to_be_generated multiselect     en_US.UTF-8 en_GB.UTF-8 en_ZA.UTF-8 UTF-8
locales locales/default_environment_locale      select  en_ZA.UTF-8
HERE

apt-get update 
apt-get install --no-install-recommends -y $PYTHON_DEPS $UTILS $OS_DEPS

wget https://xpra.org/gpg.asc -O- | apt-key add
wget https://xpra.org/repos/focal/xpra.list -O- > /etc/apt/sources.list.d/xpra.list

apt-get update 
apt-get install -y --no-install-recommends xpra

apt-get clean
rm -rf /var/cache/apt/*

