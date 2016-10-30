#!/bin/bash
set -e


function whack_passphrase {
  gpg --status-fd 1 --command-fd 0 --edit-key $GPG_KEY_ID <<EOF
password
$GPG_PASSPHRASE

y
save
y

EOF
}

function import_gpg_keys () {
  from_dir=$1
  gpg --import $from_dir/key.secret.asc
  gpg --import-ownertrust < $from_dir/trust.asc
}

if [ "$TRAVIS_SECURE_ENV_VARS" == 'true' ]; then
  echo "SECRETS are available, fetching reahl GPG signing key"
  pip install awscli
  aws s3 cp s3://$AWS_BUCKET/keys.tgz.enc /tmp/keys.tgz.enc
  openssl aes-256-cbc -K $encrypted_8ad69f44e444_key -iv $encrypted_8ad69f44e444_iv -in /tmp/keys.tgz.enc -out /tmp/keys.tgz -d
  tar -C /tmp -zxvf /tmp/keys.tgz 
  import_gpg_keys /tmp/keys
  mkdir -p ~/.gnupg
  echo "--default-key $GPG_KEY_ID" >> ~/.gnupg/options
  whack_passphrase
else
  echo "SECRETS NOT available, using fake key for signing"
  import_gpg_keys travis/keys
fi
