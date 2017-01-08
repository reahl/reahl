#!/bin/bash -e

export REGION=eu


while getopts "r:" opt; do
    case $opt in
        r) 
           export REGION="$OPTARG"
           ;;
        *)
           echo "Usage: $(basename $0) [-r region]"  >&2
           exit 1
           ;;
    esac
done

CONFIG=$(vagrant ssh-config)
HOSTNAME=$(echo $CONFIG | sed -E 's|.*HostName ([^\s ]+).*|\1|g' -)
PORT=$(echo $CONFIG | sed -E 's|.*Port ([^\s ]+).*|\1|g' -)
(
    PATH=$PATH:~/bin:.:~
    NGROK=$(which ngrok)
    set -x
    $NGROK tcp --region=$REGION $HOSTNAME:$PORT
)
