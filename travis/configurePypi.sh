#!/bin/bash

#!/bin/bash
set -e

cat > $HOME/.pypirc <<EOF
[distutils]
index-servers=pypi

[pypi]
repository = https://pypi.python.org/pypi

EOF
