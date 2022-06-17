#!/bin/bash

function version_is() {
  expected=$1
  output="$(sqlite3 migrationexamplebootstrap.db 'select version from reahl_schema_version where egg_name="migrationexamplebootstrap" ')"
  if [ "$1" = "$output" ]
  then return 0
  else return 1
  fi
}

function schema_is_new() {
    sqlite3 migrationexamplebootstrap.db '.schema migrationbootstrap_address' | grep added_date > /dev/null
}

function fail() {
    echo "ERROR: "$1
    exit 1
}

python -m pip install --no-deps -e .
reahl dropdb etc
reahl createdb etc
reahl createdbtables etc

$( version_is "0.0" ) || fail "Version 0.0 expected"
$( ! schema_is_new ) || fail "Old schema expected"


sed -i 's|<info name="version">0.0</info>|<info name="version">0.1</info>|g' .reahlproject
sed -Ei 's|^#( *)added_date|\1added_date|g' migrationexamplebootstrap.py
sed -Ei 's|^(.*)TODO(.*)|#\1TODO\2|g' migrationexamplebootstrap.py
python -m pip install --no-deps -e .
reahl migratedb etc

$( version_is "0.1" ) || fail "Version 0.1 expected"
$( schema_is_new ) || fail "New schema expected"

python -m pip uninstall $(python -c 'from setuptools.config.setupcfg import read_configuration as c; print(c("setup.cfg")["metadata"]["name"])')


