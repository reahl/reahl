#!/bin/sh -evx

VENV_NAME=$1

bash -c "export WORKON_HOME=~/.venvs; export VIRTUALENVWRAPPER_PYTHON=$(which python3); . /usr/share/virtualenvwrapper/virtualenvwrapper.sh; mkvirtualenv -p $(which python3) $VENV_NAME"

