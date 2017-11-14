#!/bin/bash -ev

function cleanup_keyfiles {
  find /tmp/ -maxdepth 1 -name keys* -type f -exec shred -f {} \;
}
trap cleanup_keyfiles EXIT

function whack_passphrase {
  set +x
  gpg --status-fd 1 --command-fd 0 --edit-key $GPG_KEY_ID <<EOF
password
$GPG_PASSPHRASE

y
save
y

EOF
  set -x
}

function import_gpg_keys () {
  from_dir=$1
  gpg --import $from_dir/key.secret.asc
  gpg --import-ownertrust < $from_dir/trust.asc
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
  import_gpg_keys /tmp/keys
  mkdir -p ~/.gnupg
  echo "default-key $GPG_KEY_ID" >> ~/.gnupg/gpg.conf
  whack_passphrase
else
  echo "SECRETS NOT available, using fake key for signing"
fi

import_gpg_keys travis/keys  # We import these anyways for use by tests that sign stuff
