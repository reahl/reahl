#!/bin/bash -ev

cat > $HOME/.pypirc <<EOF
[distutils]
index-servers=pypi

[pypi]


EOF
