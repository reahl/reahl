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

case $PROVIDER in
    lxc)
        # Re-package so we can augment the Vagrantfile inside. lxc does not honour the --vagrantfile= switch above
        
        rm -rf /tmp/reahl.lxc
        mkdir /tmp/reahl.lxc
        (
            cd /tmp/reahl.lxc
            tar -zxvf /tmp/reahl.lxc.box
        )
        cat /tmp/reahl.lxc/Vagrantfile ./vagrant/Vagrantfile.insidebox > /tmp/reahl.lxc/Vagrantfile.lxc
        mv /tmp/reahl.lxc/Vagrantfile{.lxc,}
        (
            cd /tmp/reahl.lxc
            tar -zcvf /tmp/reahl.lxc.box ./
        )
    ;;
esac
