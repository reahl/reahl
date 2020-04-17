#!/bin/bash -ev

function cleanup_keyfiles {
  find /tmp/ -maxdepth 1 -name keys* -type f -exec shred -f {} \;
}
trap cleanup_keyfiles EXIT

function preset_passphrase {
  echo 'Calling gpg-preset-passphrase'
  set +x
  echo $GPG_PASSPHRASE | /usr/lib/gnupg2/gpg-preset-passphrase --preset $GPG_KEYGRIP
  echo $GPG_PASSPHRASE | /usr/lib/gnupg2/gpg-preset-passphrase --preset $GPG_SIGN_KEYGRIP
  set -x
  echo 'done'
}

function import_gpg_keys () {
  from_dir=$1
  gpg --status-fd 2 --import $from_dir/key.secret.asc
  gpg --status-fd 2 --import-ownertrust < $from_dir/trust.asc
}

rm -f ~/.gnupg/options ~/.gnupg/gpg.conf

if [ "$TRAVIS_SECURE_ENV_VARS" == 'true' ]; then
  set +x
  echo "SECRETS are available, fetching reahl GPG signing key"
  gpg --keyserver $GPG_KEYSERVER --recv $GPG_KEY_ID
  pip install awscli
  aws s3 cp s3://$AWS_BUCKET/keys.tgz.enc /tmp/keys.tgz.enc
  openssl aes-256-cbc -K $encrypted_f7a01544e957_key -iv $encrypted_f7a01544e957_iv -in /tmp/keys.tgz.enc -out /tmp/keys.tgz -d
  tar -C /tmp -zxvf /tmp/keys.tgz 
#  echo "allow-loopback-pinentry" >> ~/.gnupg/gpg-agent.conf
  echo "allow-preset-passphrase" >> ~/.gnupg/gpg-agent.conf
  gpgconf --reload gpg-agent
  gpg-connect-agent reloadagent /bye
  sleep 2
  preset_passphrase
  import_gpg_keys /tmp/keys
  mkdir -p ~/.gnupg
  echo "default-key $GPG_KEY_ID" >> ~/.gnupg/gpg.conf
  ls ~/.gnupg
  cat ~/.gnupg/*
  ps aux | grep gpg
else
  echo "SECRETS NOT available, using fake key for signing"
fi

import_gpg_keys travis/keys  # We import these anyways for use by tests that sign stuff
