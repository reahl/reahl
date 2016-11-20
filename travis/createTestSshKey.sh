#!/bin/bash
set -e

# Generate the key
ssh-keygen -f ~/.ssh/id_localhost -N ""
echo 'Host localhost' >> ~/.ssh/config
echo '  IdentityFile ~/.ssh/id_localhost' >> ~/.ssh/config
cat ~/.ssh/id_localhost.pub >> ~/.ssh/authorized_keys

# Start ssh agent for passwordless
# eval $(ssh-agent)
# ssh-add

# Accept localhost server key
ssh -o StrictHostKeyChecking=no localhost ls
