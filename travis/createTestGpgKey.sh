#!/bin/bash -ev

function cleanup_keyfiles {
  find /tmp/ -maxdepth 1 -name keys* -type f -exec shred -f {} \;
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

function preset_passphrase {
  # This assumes the keys have already been imported
  GPG_KEYGRIP=$(gpg --status-fd 2 --with-keygrip --list-secret-key $GPG_KEY_ID | grep Keygrip | head -n 1 | awk '{print $3}')  
  /usr/lib/gnupg2/gpg-preset-passphrase --preset $GPG_KEYGRIP <<< $GPG_PASSPHRASE
  gpg-connect-agent 'keyinfo --list' /bye
}

function import_gpg_keys () {
  from_dir=$1
  gpg --status-fd 2 --pinentry-mode loopback --passphrase-fd 0 --import $from_dir/key.secret.asc <<< $GPG_PASSPHRASE
  gpg --status-fd 2 --import-ownertrust < $from_dir/trust.asc
}

function cat_if_exists {
  filename=$1
  if [ -f $filename ]
  then
    echo "Contents of: $filename"
    cat $filename | echo
  else
    echo "File not found: $filename"
  fi
}

cat_if_exists ~/.gnupg/gpg.conf
cat_if_exists ~/.gnupg/options

rm -f ~/.gnupg/options ~/.gnupg/gpg.conf
configure_gnupg
echo "no-tty" >> ~/.gnupg/gpg.conf

cat_if_exists ~/.gnupg/gpg.conf
cat_if_exists ~/.gnupg/options


if [ "$TRAVIS_SECURE_ENV_VARS" == 'true' ]; then
  echo "SECRETS are available, fetching reahl GPG signing key"
  i="0"
  while ! gpg --keyserver $GPG_KEYSERVER --recv $GPG_KEY_ID && [ $i -lt 5 ]
  do
    sleep 10
    i=$[$i+1]
    echo "Trying to get key again again[$i]"
  done
  [ $i -lt 5 ] || exit 1
  pip install awscli
  aws s3 cp s3://$AWS_BUCKET/keys.tgz.enc /tmp/keys.tgz.enc
  set +x
  openssl aes-256-cbc -K $encrypted_f7a01544e957_key -iv $encrypted_f7a01544e957_iv -in /tmp/keys.tgz.enc -out /tmp/keys.tgz -d
  set -x
  tar -C /tmp -zxvf /tmp/keys.tgz 
  import_gpg_keys /tmp/keys
  preset_passphrase
  echo "default-key $GPG_KEY_ID" >> ~/.gnupg/gpg.conf
else
  echo "SECRETS NOT available, using fake key for signing"
fi


import_gpg_keys travis/keys  # We import these anyways for use by tests that sign stuff

gpg --list-secret-keys --with-keygrip
