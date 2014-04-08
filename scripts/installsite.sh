
apt-get install apache ssl-cert
cd reahl-doc/reahl/doc/examples/tutorial/helloapache/
cp prod/apache/default-ssl /etc/apache2/sites-available/default-ssl 
cp prod/apache/default /etc/apache2/sites-available/
mkdir  /usr/local/helloapache
cp prod/helloapache.wsgi /usr/local/helloapache/
mkdir -p /etc/reahl.d/helloapache
cp -r prod/etc/ /etc/reahl.d/helloapache
mkdir -p /var/local/helloapache/www
chown -R www-data:www-data /var/local/helloapache

chmod 755 /var/local/
chmod -s /var/local

source /usr/local/helloapache/virtualenv/bin/activate
pip install --no-index -f file:///home/craig/develop/.reahlworkspace/dist-egg/ helloapache

su - www-data
source /usr/local/helloapache/virtualenv/bin/activate
reahl-control createdbtables /etc/reahl.d/helloapache/etc

exit

a2enmod ssl
a2enmod wsgi
a2ensite default
a2ensite default-ssl
service apache2 start

tail -f /var/log/apache2/helloapache.*.log
w3m localhost
