#!/bin/bash

tmpfile=$(mktemp /tmp/XXXXXX)

function cleanup {
  rm "$tmpfile"
}
trap cleanup EXIT

export MACHINE_NAME="default"
export REMOTE_DISPLAY=":100"

while getopts "v:d:r:p:i:" opt; do
    case $opt in
        v) 
           export MACHINE_NAME="$OPTARG"
           ;;
        d) 
           export REMOTE_DISPLAY="$OPTARG"
           ;;
        r) 
           export REMOTE_HOSTNAME="$OPTARG"
           ;;
        p) 
           export REMOTE_SSH_PORT="$OPTARG"
           ;;
        i) 
           export REMOTE_SSH_IDENTITY="$OPTARG"
           ;;
        *)
           echo "Usage: $(basename $0) [-v vagrant_machine_name] [-d remote_display] [-r remote_hostname -p remote_ssh_port [-i ssh_identity_file]] [-- args passed to xpra attach]"  >&2
           exit 1
           ;;
    esac
done

shift $((OPTIND-1))
export XPRA_ATTACH_ARGS="$@"


echo "Vagrant machine name: $MACHINE_NAME"


if [ ! -z "$REMOTE_HOSTNAME" ]; then
    if [ -z "$REMOTE_SSH_PORT" ]; then
        echo "Please specify a remote port also with -p" >&2
        exit 1
    fi
    echo "Remote hostname: $REMOTE_HOSTNAME"
    echo "Remote port: $REMOTE_SSH_PORT"
    cat <<EOF  >> "$tmpfile"
Host $MACHINE_NAME
   User vagrant
   HostName $REMOTE_HOSTNAME
   Port $REMOTE_SSH_PORT
#   UserKnownHostsFile /dev/null
#   StrictHostKeyChecking no
   PasswordAuthentication no
   LogLevel FATAL
EOF
    if [ ! -z "$REMOTE_SSH_IDENTITY" ]; then
        cat <<EOF >> "$tmpfile"
   IdentitiesOnly yes
   IdentityFile $REMOTE_SSH_IDENTITY
EOF
    fi
else
    vagrant ssh-config $MACHINE_NAME > "$tmpfile"
fi


echo "Using ssh config:"
cat "$tmpfile"
set -x
xpra attach --sharing=yes $XPRA_ATTACH_ARGS ssh:$MACHINE_NAME"$REMOTE_DISPLAY" --ssh="ssh -F $tmpfile"


