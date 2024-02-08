#!/bin/bash -ev

function cleanup_keyfiles {
  find /tmp/ -maxdepth 2 -name 'key*' -type f -exec shred -fu {} \;
}
trap cleanup_keyfiles EXIT

function configure_gnupg {
  # Note:
  # we're configuring gpg for being able to preset the passphrase, but that does not
  # work. No idea why. Perhaps something to do with the fact that we have stub keys also?
  # So, we've hacked reahl build to pipe the environment variable GPG_PASSPHRASE to
  # gpg using --pinentry-mode loopback when signing, hence only allow-loopback is
  # really necessary. I'm leaving all this config here for possible future reference
  # though. 
  mkdir -p ~/.gnupg
  echo "allow-preset-passphrase" >> ~/.gnupg/gpg-agent.conf
  echo "allow-loopback-pinentry" >> ~/.gnupg/gpg-agent.conf
  echo "use-agent" >> ~/.gnupg/gpg.conf
  gpgconf --reload gpg-agent
}

function import_gpg_keys() {
  from_dir=$1
  GPG_PASSPHRASE=""
  gpg --status-fd 2 --pinentry-mode loopback --passphrase-fd 0 --import $from_dir/key.secret.asc <<< $GPG_PASSPHRASE
  gpg --status-fd 2 --import-ownertrust < $from_dir/trust.asc
}


rm -f ~/.gnupg/options ~/.gnupg/gpg.conf

configure_gnupg

import_gpg_keys scripts/keys  # We import these anyways for use by tests that sign stuff

gpg --list-secret-keys --with-keygrip
