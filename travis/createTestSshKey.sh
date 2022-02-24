#!/bin/sh -ev

# Generate the key
ssh-keygen -t rsa -f ~/.ssh/id_localhost -N ""
echo 'Host localhost' >> ~/.ssh/config
echo '  IdentityFile ~/.ssh/id_localhost' >> ~/.ssh/config
cat ~/.ssh/id_localhost.pub >> ~/.ssh/authorized_keys

# Start ssh agent for passwordless
# eval $(ssh-agent)
# ssh-add

# Accept localhost server key
ssh-keyscan -t rsa localhost >> ~/.ssh/known_hosts
ssh -v localhost ls

