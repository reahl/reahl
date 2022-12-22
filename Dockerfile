FROM ubuntu:22.04 as base

# ---- ENV vars set here are available to all phases of the build going forward
ENV BOOTSTRAP_REAHL_SOURCE=
ENV REAHL_USER=developer
ENV VENV_HOME=/home/$REAHL_USER/.venvs
ENV VENV_NAME=python3.10
ENV VENV=$VENV_HOME/$VENV_NAME
ENV REAHLWORKSPACE=/home/$REAHL_USER
ENV REAHL_SCRIPTS=$REAHLWORKSPACE/reahl

FROM base as build-image

RUN adduser --disabled-password --gecos '' $REAHL_USER
USER $REAHL_USER

RUN mkdir -p $REAHL_SCRIPTS

COPY --chown=$REAHL_USER:$REAHL_USER ./scripts/installBuildDebs.sh $REAHL_SCRIPTS/scripts/installBuildDebs.sh
COPY --chown=$REAHL_USER:$REAHL_USER ./scripts/installDebs.sh $REAHL_SCRIPTS/scripts/installDebs.sh
COPY --chown=$REAHL_USER:$REAHL_USER ./scripts/installDevEnvDebs.sh $REAHL_SCRIPTS/scripts/installDevEnvDebs.sh

USER root
RUN $REAHL_SCRIPTS/scripts/installBuildDebs.sh && \
    $REAHL_SCRIPTS/scripts/installDebs.sh && \
    $REAHL_SCRIPTS/scripts/installDevEnvDebs.sh

COPY --chown=$REAHL_USER:$REAHL_USER . $REAHLWORKSPACE/reahl

USER $REAHL_USER
RUN $REAHL_SCRIPTS/scripts/createVenv.sh $VENV

USER root
RUN /etc/init.d/ssh start && \
        sudo -i -u $REAHL_USER -- bash -lex -c "export VENV_NAME=$VENV_NAME; cd $REAHL_SCRIPTS && $REAHL_SCRIPTS/scripts/setupDevEnv.sh" && \
        /etc/init.d/ssh stop

USER $REAHL_USER
RUN mkdir -p $REAHLWORKSPACE/.reahlworkspace/dist-egg
RUN bash -l -c "cd $REAHL_SCRIPTS && python scripts/bootstrap.py --script-dependencies && python scripts/bootstrap.py --pip-installs && reahl setup -sdX develop -N"
RUN bash -l -c "cd $REAHL_SCRIPTS && pip freeze"
RUN bash -l -c "cd $REAHL_SCRIPTS && reahl build -sdX -ns; cd reahl-doc/doc; make html"


FROM base as dev-image

RUN adduser --disabled-password --gecos '' $REAHL_USER

COPY --from=build-image "$REAHL_SCRIPTS/reahl-doc/doc/_build/html" "/usr/share/doc/reahl"
COPY --chown=$REAHL_USER --from=build-image "$REAHLWORKSPACE/.reahlworkspace/dist-egg" "$REAHLWORKSPACE/.reahlworkspace/dist-egg"

ENV REAHL_SCRIPTS=/opt/reahl
RUN mkdir -p $REAHL_SCRIPTS 

COPY ./scripts $REAHL_SCRIPTS/scripts

RUN $REAHL_SCRIPTS/scripts/installDebs.sh && \
    $REAHL_SCRIPTS/scripts/installDevEnvDebs.sh

RUN /etc/init.d/ssh start && \
        sudo -i -u $REAHL_USER -- bash -lex -c "export VENV_NAME=$VENV_NAME; cd $REAHL_SCRIPTS && $REAHL_SCRIPTS/scripts/setupDevEnv.sh" && \
        /etc/init.d/ssh stop

USER $REAHL_USER
RUN mkdir -p $VENV_HOME
RUN $REAHL_SCRIPTS/scripts/createVenv.sh $VENV
RUN bash -l -c "$VENV/bin/pip install --pre reahl[all]"

USER root

EXPOSE 80 8000 8363
ENTRYPOINT [ "/opt/reahl/scripts/runDevelopmentDocker.sh" ]
CMD [ "/usr/sbin/sshd", "-D" ]

