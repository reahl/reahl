#!/bin/sh -evx

if [ ! -f /.provisioned ]; then
    # Regenerate host keys
    /bin/rm -fv /etc/ssh/ssh_host_*
    dpkg-reconfigure openssh-server

    # Secure ssh (we modify its config here after the reconfigure above to avoid it asking about changes to config files)
    sed -Ei 's|#?\W*(PasswordAuthentication)\W+yes|\1 no|g' /etc/ssh/sshd_config && \
    sed -Ei 's|#?\W*(PermitRootLogin)\W+.*|\1 no|g' /etc/ssh/sshd_config && \
    echo "ClientAliveInterval 30" >> /etc/ssh/sshd_config
    
    # Fake /run/user/1000
    mkdir -p /run/user/1000
    chown $REAHL_USER.$REAHL_USER /run/user/1000
    chmod 700 /run/user/1000
    
    /etc/init.d/ssh start

    su $REAHL_USER -c -- bash -l -c '
    # Update localhost known_hosts
    mkdir ~/.ssh
    chmod 700 ~/.ssh
    ssh-keyscan -t rsa localhost > ~/.ssh/known_hosts

    if [ ! -z "$BOOTSTRAP_GIT" ]; then
       . $HOME/.profile
       rmvirtualenv $VENV_NAME
       $REAHL_SCRIPTS/scripts/createVenv.sh $VENV_NAME
       cd $BOOTSTRAP_GIT
       python scripts/bootstrap.py --script-dependencies
       python scripts/bootstrap.py --pip-installs
    fi
    '
    if [ ! -z "$BOOTSTRAP_GIT" ]; then
        $REAHL_SCRIPTS/scripts/installBuildDebs.sh
    fi

    /etc/init.d/ssh stop

    touch /.provisioned
fi

