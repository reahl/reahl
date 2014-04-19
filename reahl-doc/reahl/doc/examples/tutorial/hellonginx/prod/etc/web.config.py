
from hellonginx import HelloUI

# The Region class acting as the root of the URL hierachy of your application:
web.site_root = HelloUI 

# HTTP is served on port 80, and HTTPS on 443, except when in development!
web.default_http_port = 80
web.encrypted_http_port = 443

# Each application has one (and only one) directory where static files can be served from
# (This directory needs to be owned by www-data)
web.static_root = '/var/local/hellonginx/www'  

