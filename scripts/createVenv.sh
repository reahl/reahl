#!/bin/bash -evx

VENV=$1

python3 -m venv $VENV
$VENV/bin/pip install -U pip wheel

