#!/bin/bash -ev

# Generate the key
ssh-keygen -f ~/.ssh/id_rsa -N ""
cp ~/.ssh/{id_rsa.pub,authorized_keys}

# Start ssh agent for passwordless
# eval $(ssh-agent)
# ssh-add

# Accept localhost server key
ssh -o StrictHostKeyChecking=no localhost ls
