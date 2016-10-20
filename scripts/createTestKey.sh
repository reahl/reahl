#!/bin/bash
set -e

gpg --import travis/testkey.public.asc travis/testkey.secret.asc
gpg --import-ownertrust < travis/testkey.trust.asc
