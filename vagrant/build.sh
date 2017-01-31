#!/bin/bash -e

export PROVIDER=virtualbox
while getopts "p:" opt; do
    case $opt in
        p) 
           export PROVIDER="$OPTARG"
           ;;
        *) 
           echo "Usage: $(basename $0) [-p provider]"  >&2
           exit 1
           ;;
    esac
done

export VAGRANT_VAGRANTFILE=./vagrant/Vagrantfile.buildbox
vagrant up --provider=$PROVIDER
vagrant halt -f
vagrant package --vagrantfile=./vagrant/Vagrantfile.insidebox --output=/tmp/reahl.$PROVIDER.box


