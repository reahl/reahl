#!/bin/bash -ev

# Installs needed to develop on reahl itself

PYTHON_DEPS="python3 python3-virtualenv virtualenvwrapper python3-dev gcc cython libxml2-dev libxslt-dev libsqlite3-0 sqlite3 postgresql-server-dev-all zlib1g-dev libfreetype6-dev equivs openssh-client dpkg-dev postgresql libyaml-dev"
UTILS="screen unzip git"

# For X11 forwarding to work and other misc stuff we need
OS_DEPS="xauth dmidecode"

# These are for chromium-browser and chromedriver:
CHROMIUM_DEPS="gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libfreetype6 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgnome-keyring0 libgtk2.0-0 libnspr4 libnss3 libpam0g libpango-1.0-0 libpangocairo-1.0-0 libpangoft2-1.0-0 libstdc++6 libx11-6 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2  libxrender1 libxss1 libxtst6 zlib1g bash libnss3 xdg-utils"
# liblcms1-dev -> liblcms2-dev
# libjpeg62-dev -> libjpeg62-turbo-dev

apt-get update
apt-get install -y $PYTHON_DEPS $UTILS $CHROMIUM_DEPS $OS_DEPS


