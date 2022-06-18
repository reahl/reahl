#!/bin/sh -ev

mkdir $HOME/.pip
cat > $HOME/.pip/pip.conf <<EOF
[global]
index-url = https://pypi.python.org/simple/
find-links = $REAHLWORKSPACE/.reahlworkspace/dist-egg
EOF

