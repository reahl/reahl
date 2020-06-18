#!/bin/sh -evx

if [ ! -f /.provisioned ]; then
    echo Regenerate host keys
    /bin/rm -fv /etc/ssh/ssh_host_*
    dpkg-reconfigure openssh-server

    echo Secure ssh access
    sed -Ei 's|#?\W*(PasswordAuthentication)\W+yes|\1 no|g' /etc/ssh/sshd_config
    sed -Ei 's|#?\W*(PermitRootLogin)\W+.*|\1 no|g' /etc/ssh/sshd_config
    echo "ClientAliveInterval 30" >> /etc/ssh/sshd_config

    echo Fake /run/user/1000
    mkdir -p /run/user/1000
    chown developer.developer /run/user/1000
    chmod 700 /run/user/1000
    
    /etc/init.d/ssh start

    su developer -c -- sh -c '
    echo Update localhost known_hosts;
    mkdir ~/.ssh; 
    chmod 700 ~/.ssh; 
    ssh-keyscan -t rsa localhost > ~/.ssh/known_hosts;

    echo Setup virtualenv, virtualenvwrapper;
    echo "export WORKON_HOME=~/.venvs" >> $HOME/.profile;
    echo "source /usr/share/virtualenvwrapper/virtualenvwrapper.sh" >> $HOME/.profile;
    echo "workon python3.8" >> $HOME/.profile;

    echo Create a development virtualenv;
    WORKON_HOME=~/.venvs;
    . /usr/share/virtualenvwrapper/virtualenvwrapper.sh;
    mkvirtualenv -p $(which python3.8) python3.8

    if [ -d ~/reahl ]; then
       cd ~/reahl;
       . $HOME/.profile;
       python scripts/bootstrap.py --script-dependencies;
       python scripts/bootstrap.py --pip-installs;
    fi;

    '

    USER=developer $REAHL_SCRIPTS/vagrant/setupDevDatabases.sh

    /etc/init.d/ssh stop

    touch /.provisioned
fi

