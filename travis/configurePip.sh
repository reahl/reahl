#!/bin/sh -ev

mkdir $HOME/.pip
cat > $HOME/.pip/pip.conf <<EOF
[global]
find-links = $REAHLWORKSPACE/.reahlworkspace/dist-egg
EOF

