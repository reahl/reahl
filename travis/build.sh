#!/bin/bash -x

function cleanup_keys {
  if [ ! -z "$(ls /tmp/keys*)" ]; then
    shred -f /tmp/keys* $HOME/.gnupg/*
  fi 
}
trap cleanup_keys EXIT

# Setup ssh for password-less access to localhost
./travis/createTestGpgKey.sh
reahl build -sdX

