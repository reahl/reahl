FROM nginx:1.19

RUN apt-get update && \
    apt-get install ssl-cert && \
    rm -rf /var/cache/apt/*
COPY prod/nginx/app.conf /etc/nginx/conf.d/default.conf