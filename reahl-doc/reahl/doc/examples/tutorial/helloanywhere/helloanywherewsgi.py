
from __future__ import print_function, unicode_literals, absolute_import, division
import os
from reahl.web.fw import ReahlWSGIApplication
application = ReahlWSGIApplication.from_directory('%s/etc/reahl.d/hellonginx' % os.environ['HOME'])
application.start()

