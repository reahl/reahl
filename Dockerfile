FROM ubuntu:20.04 as base

# ---- ENV vars set here are available to all phases of the build going forward

ENV VENV_ROOT=/var/local/reahl
ENV VENV=$VENV_ROOT/opt
ENV PIP=$VENV/bin/pip3
ENV PYTHON=$VENV/bin/python3

ENV REAHL_SCRIPTS=/opt/reahl



# ---- Then we start fresh without the ruby build-deps and install what we need for monitor: 

FROM base as python-install


RUN mkdir -p $REAHL_SCRIPTS
COPY ./scripts/installDebs.sh $REAHL_SCRIPTS/scripts/installDebs.sh

RUN $REAHL_SCRIPTS/scripts/installDebs.sh && \
    adduser --disabled-password --gecos '' developer && \
    echo "Defaults env_keep += REAHL_SCRIPTS\ndeveloper ALL=(root) NOPASSWD: /opt/reahl/scripts/provision.sh" > /etc/sudoers.d/reahl

COPY ./scripts $REAHL_SCRIPTS/scripts
COPY ./travis $REAHL_SCRIPTS/travis
COPY ./vagrant $REAHL_SCRIPTS/vagrant

RUN /etc/init.d/ssh start && \
        sudo -i -u developer bash -c "cd $REAHL_SCRIPTS; $REAHL_SCRIPTS/vagrant/setupDevEnv.sh" && \
        /etc/init.d/ssh stop

EXPOSE 80 8000 8363
ENTRYPOINT [ "/opt/reahl/scripts/runDevelopmentDocker.sh" ]
CMD [ "/usr/sbin/sshd", "-D" ]


