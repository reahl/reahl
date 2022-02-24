#!/bin/sh

# schroot -p -c precise-test
# sudo ./scripts/makeenv.sh /usr/local/hellonginx/virtualenv file:///home/craig/develop/.reahlworkspace/dist-egg/
# sudo ./scripts/installsite-nginx.sh
set -x

apt-get install nginx uwsgi ssl-cert
cd reahl-doc/reahl/doc/examples/tutorial/hellonginx/
cp prod/nginx/hellonginx /etc/nginx/sites-available/
cp prod/uwsgi/hellonginx.ini /etc/uwsgi/apps-available/
ln -s /etc/uwsgi/apps-available/hellonginx.ini /etc/uwsgi/apps-enabled/hellonginx.ini
ln -s /etc/nginx/sites-available/hellonginx /etc/nginx/sites-enabled/hellonginx

mkdir  /usr/local/hellonginx
#cp prod/hellonginx.wsgi /usr/local/hellonginx/
mkdir -p /etc/reahl.d/hellonginx
cp -r prod/etc/* /etc/reahl.d/hellonginx
mkdir -p /var/local/hellonginx/www
chown -R www-data:www-data /var/local/hellonginx

chmod 755 /var/local/
chmod -s /var/local

. /usr/local/hellonginx/virtualenv/bin/activate
pip install --no-index -f file:///home/craig/develop/.reahlworkspace/dist-egg/ hellonginx

su - www-data
. /usr/local/hellonginx/virtualenv/bin/activate
reahl createdbtables /etc/reahl.d/hellonginx

exit

service uwsgi restart
service nginx restart

tail -f /var/log/nginx/hellonginx.*.log
w3m localhost
