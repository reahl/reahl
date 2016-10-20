#!/bin/bash
set -e

mkdir $HOME/.pip
cat > $HOME/.pip/pip.conf <<EOF
find-links = /home/travis/.reahlworkspace/dist-egg
[global]
EOF

