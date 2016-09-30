#!/bin/bash
set -e

mkdir $HOME/.pip
cat > $HOME/.pip/pip.conf <<EOF
[global]
index-url = http://localhost:3141/travis/dev
EOF

cat > $HOME/.pydistutils.cfg <<EOF
[easy_install]
index-url = http://localhost:3141/travis/dev/+simple/
EOF


cat > $HOME/.pypirc <<EOF
[distutils]
index-servers=devpi

[devpi]
username = travis
password = 123
repository = http://localhost:3141/travis/dev/
EOF

devpi-server --start
devpi use http://localhost:3141
devpi user -c travis password=123
devpi login travis --password=123
devpi index -c dev bases=root/pypi
devpi use travis/dev
