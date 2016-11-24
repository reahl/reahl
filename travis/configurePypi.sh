#!/bin/bash -ev

cat > $HOME/.pypirc <<EOF
[distutils]
index-servers=pypi

[pypi]
repository = https://pypi.python.org/pypi

EOF
