#!/bin/sh -evx

VENV_NAME=$1

bash -l -c "export WORKON_HOME=~/.venvs; . /usr/share/virtualenvwrapper/virtualenvwrapper.sh; mkvirtualenv -p $(which python3.8) $VENV_NAME"


