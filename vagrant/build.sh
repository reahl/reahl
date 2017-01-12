#!/bin/bash -e

export VAGRANT_VAGRANTFILE=./vagrant/Vagrantfile.buildbox
vagrant up --provider=virtualbox
vagrant halt -f
vagrant package --vagrantfile=./vagrant/Vagrantfile.insidebox --output=/tmp/reahl.virtualbox.box


