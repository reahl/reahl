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

export OUT_FILE=/tmp/reahl.$PROVIDER.box
if [ -f $OUT_FILE ]
then
   echo $OUT_FILE exists, please remove it first!
   exit 1
fi

export VAGRANT_VAGRANTFILE=./vagrant/Vagrantfile.buildbox
vagrant up --provider=$PROVIDER
vagrant halt -f
vagrant package --vagrantfile=./vagrant/Vagrantfile.insidebox --output=$OUT_FILE

case $PROVIDER in
    lxc)
        echo Re-package the lxc box so we can augment the Vagrantfile inside. lxc does not honour the --vagrantfile= switch above
        
        rm -rf /tmp/reahl.lxc
        mkdir /tmp/reahl.lxc
        (
            cd /tmp/reahl.lxc
            tar -zxf $OUT_FILE
        )
        cat /tmp/reahl.lxc/Vagrantfile ./vagrant/Vagrantfile.insidebox > /tmp/reahl.lxc/Vagrantfile.lxc
        mv /tmp/reahl.lxc/Vagrantfile{.lxc,}
        (
            cd /tmp/reahl.lxc
            tar -zcf $OUT_FILE ./
        )
    ;;
esac
