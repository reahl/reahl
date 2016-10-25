#!/bin/bash
set -e

echo '*:*:*:*:rhug' > $HOME/.pgpass
chmod 600 $HOME/.pgpass
reahl-control createdbuser -n reahl-web/etc/
reahl-control createdb reahl-web/etc/
