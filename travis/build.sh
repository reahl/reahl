#!/bin/bash -x

function cleanup_keys {
  shred -f /tmp/keys* .gnupg/*
}
trap cleanup_keys EXIT

# Setup ssh for password-less access to localhost
./travis/createTestSshKey.sh
reahl build -sdX

