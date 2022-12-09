FROM ubuntu:22.04 as base

#For Postgres db
ENV DB_CLIENT_LIBS=postgresql-client

#For MySQL db
#ENV DB_CLIENT_BUILD_LIBS="gcc python3-dev default-libmysqlclient-dev mysql-client"
#ENV DB_CLIENT_LIBS="libmysqlclient21 mysql-client"
#ENV WHEELS_TO_BUILD="reahl[mysql]$REAHL_VERSION_SPEC"

# Stage1: Build distribution package (wheel) using build tools
FROM base as build
ENV REAHL_VERSION_SPEC=""
#ENV REAHL_VERSION_SPEC="~=5.0"
ENV TZ="Africa/Johannesburg"
ENV DEBIAN_FRONTEND=noninteractive
COPY . /app
WORKDIR /app
ENV REAHLWORKSPACE=/app
ENV VENV=/tmp/build-venv
RUN apt-get update -y && apt-get install -y --no-install-recommends python3-pip python3-venv $DB_CLIENT_BUILD_LIBS && \
    apt-get clean && rm -rf /var/cache/apt/* &&  rm -rf /var/lib/apt/lists/* && \
    python3 -m venv $VENV && \
    $VENV/bin/pip install -U pip && \
    $VENV/bin/pip install wheel && \
    if [ ! -z "$WHEELS_TO_BUILD" ]; then $VENV/bin/pip wheel -w /tmp/wheels $WHEELS_TO_BUILD; else mkdir /tmp/wheels ;fi && \
    $VENV/bin/pip install reahl[dev]$REAHL_VERSION_SPEC && \
    $VENV/bin/reahl build -ns && \
    mv /app/.reahlworkspace/dist-egg/* /tmp/wheels/


# Stage: Install wheels in final image
FROM base as release
EXPOSE 8080
WORKDIR /home/www-data
COPY prod/uwsgi/app.ini /etc/app-wsgi.ini
COPY prod/etc /etc/app-reahl
COPY www /app
COPY --from=build /tmp/wheels/* /tmp/wheels/
ENV VENV=/app/venv

RUN apt-get update -y && \
    apt-get install --no-install-recommends -y python3-pip python3-venv uwsgi uwsgi-plugin-python3 $DB_CLIENT_LIBS && \
    apt-get clean && rm -rf /var/cache/apt/* &&  rm -rf /var/lib/apt/lists/* && \
    python3 -m venv $VENV && \
    $VENV/bin/pip install --no-cache-dir -U pip wheel && \
    $VENV/bin/pip install --no-cache-dir --find-links /tmp/wheels/ /tmp/wheels/* && \
    rm -rf /tmp/wheels

USER www-data
CMD ["uwsgi", "--ini", "/etc/app-wsgi.ini"]
