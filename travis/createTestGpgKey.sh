#!/bin/bash -ev

function cleanup_keyfiles {
  find /tmp/ -maxdepth 1 -name keys* -type f -exec shred -f {} \;
}
trap cleanup_keyfiles EXIT

function configure_gnupg {
  mkdir -p ~/.gnupg
  echo "allow-preset-passphrase" >> ~/.gnupg/gpg-agent.conf
  echo "allow-loopback-pinentry" >> ~/.gnupg/gpg-agent.conf
  echo "use-agent" >> ~/.gnupg/gpg.conf
  gpgconf --reload gpg-agent
#  gpg-connect-agent reloadagent /bye
}

function preset_passphrase {
  /usr/lib/gnupg2/gpg-preset-passphrase --preset $GPG_KEYGRIP <<< $GPG_PASSPHRASE
  gpg-connect-agent 'keyinfo --list' /bye
}

function import_gpg_keys () {
  from_dir=$1
  gpg --status-fd 2 --pinentry-mode loopback --passphrase-fd 0 --import $from_dir/key.secret.asc <<< $GPG_PASSPHRASE
  gpg --status-fd 2 --import-ownertrust < $from_dir/trust.asc
}

rm -f ~/.gnupg/options ~/.gnupg/gpg.conf

configure_gnupg

if [ "$TRAVIS_SECURE_ENV_VARS" == 'true' ]; then
  echo "SECRETS are available, fetching reahl GPG signing key"
  gpg --keyserver $GPG_KEYSERVER --recv $GPG_KEY_ID
  pip install awscli
  aws s3 cp s3://$AWS_BUCKET/keys.tgz.enc /tmp/keys.tgz.enc
  set +x
  openssl aes-256-cbc -K $encrypted_f7a01544e957_key -iv $encrypted_f7a01544e957_iv -in /tmp/keys.tgz.enc -out /tmp/keys.tgz -d
  set -x
  tar -C /tmp -zxvf /tmp/keys.tgz 
  preset_passphrase
  import_gpg_keys /tmp/keys
  echo "default-key $GPG_KEY_ID" >> ~/.gnupg/gpg.conf
else
  echo "SECRETS NOT available, using fake key for signing"
fi

import_gpg_keys travis/keys  # We import these anyways for use by tests that sign stuff
