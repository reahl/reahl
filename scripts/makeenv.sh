#!/bin/sh

SITE_ENV=$1

[ -z "$SITE_ENV" ] && echo "Usage $0 <virtual_env_dir> [<local_eggs_dir>]" && exit 1
[ -e $SITE_ENV ] && echo "$SITE_ENV already exists!" && exit 1

LOCAL_EGGS=""
if [ ! -z $2 ]
then
  LOCAL_EGGS="-f $2"
fi

# non-python packages
sudo apt-get install python-virtualenv           # For virtualenv - see below
sudo apt-get install python-dev gcc cython3       # To be able to compile Python modules implemented in C (WebTest, SQLAlchemy, etc)
sudo apt-get install libsqlite3-0                # Sqlite
sudo apt-get install libxml2-dev libxslt-dev     # Header files for compiling WebTest
# END non-python packages

# non-python packages for postgresql
sudo apt-get install postgresql-9.1              # Postgresql
sudo apt-get install postgresql-server-dev-9.1   # Header files for compiling psycopg2
# END non-python packages for postgresql

# non-python packages for PILLOW
sudo apt-get install zlib1g-dev libjpeg62-dev libfreetype6-dev liblcms1-dev   # Headers for compiling PIL
# END non-python packages for PILLOW

# non-python packages for lxml
sudo apt-get install zlib1g-dev   # Headers for compiling lxml
# END non-python packages for lxml

# non-python packages for selenium tests
sudo apt-get install firefox firefox-geckodriver
# END non-python packages for selenium tests

virtualenv --no-site-packages $SITE_ENV


. $SITE_ENV/bin/activate

pip install $LOCAL_EGGS reahl[all]

deactivate

