#!/bin/bash

#!/bin/bash
set -e

cat > $HOME/.pypirc <<EOF
[distutils]
index-servers=pypi

[pypi]
repository = https://testpypi.python.org/pypi

EOF
