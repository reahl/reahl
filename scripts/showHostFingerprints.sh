#!/bin/sh

for i in $(ls /etc/ssh/ssh_host_*.pub); do
    for e in md5 sha256; do
        ssh-keygen -l -E $e -f $i;
    done
done
