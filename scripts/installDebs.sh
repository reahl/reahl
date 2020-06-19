#!/bin/bash -ev

PYTHON_DEPS="python3 python3-venv"

MYSQL="mysql-client"
POSTGRES="postgresql-client"
SQLITE="sqlite3 libsqlite3-0"

OS_DEPS="ca-certificates sudo xauth libexif12 wget"

RUNTIME_DEPS="$OS_DEPS $PYTHON_DEPS"

export DEBIAN_FRONTEND=noninteractive
apt-get update 
apt-get install --no-install-recommends -y $RUNTIME_DEPS
apt-get clean
rm -rf /var/cache/apt/*

