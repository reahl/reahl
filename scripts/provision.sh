#!/bin/sh -evx

if [ ! -f /.provisioned ]; then
    # Regenerate host keys
    /bin/rm -fv /etc/ssh/ssh_host_*
    dpkg-reconfigure openssh-server
    apt-get update -o Dir::Etc::SourceList=/etc/apt/sources.list -o Dir::Etc::SourceParts=/dev/null
    apt-get install -y ca-certificates

    # Secure ssh (we modify its config here after the reconfigure above to avoid it asking about changes to config files)
    echo "PasswordAuthentication no" >> /etc/ssh/sshd_config.d/reahl.conf
    echo "PermitRootLogin no" >> /etc/ssh/sshd_config.d/reahl.conf
    echo "AuthorizedKeysFile .ssh/authorized_keys .ssh/authorized_keys2" >> /etc/ssh/sshd_config.d/reahl.conf
    echo "ClientAliveInterval 30" >> /etc/ssh/sshd_config.d/reahl.conf
    echo "AddressFamily inet" >> /etc/ssh/sshd_config.d/reahl.conf  # For ssh X11 forwarding to work
    
    # Fake /run/user/1000
    mkdir -p /run/user/1000
    chown $REAHL_USER.$REAHL_USER /run/user/1000
    chmod 700 /run/user/1000
    
    /etc/init.d/ssh start

    # Update localhost known_hosts
    su $REAHL_USER -c 'bash -l -c "ssh-keyscan -t rsa localhost > ~/.ssh/known_hosts"'

    if [ ! -z "$BOOTSTRAP_REAHL_SOURCE" ]; then
        $REAHL_SCRIPTS/scripts/installBuildDebs.sh
        su $REAHL_USER -c 'bash -l -c "
           pip freeze | grep reahl | xargs pip uninstall -y
           cd $BOOTSTRAP_REAHL_SOURCE
           $VENV/bin/python scripts/bootstrap.py --script-dependencies
           $VENV/bin/python scripts/bootstrap.py --pip-installs
        "'
    fi

    /etc/init.d/ssh stop

    touch /.provisioned
fi

