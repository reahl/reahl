#!/bin/bash
set -e

mkdir $HOME/.pip
cat > $HOME/.pip/pip.conf <<EOF
[global]
find-links = /home/travis/.reahlworkspace/dist-egg
EOF

