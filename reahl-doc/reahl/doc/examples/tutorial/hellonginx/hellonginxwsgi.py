
from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.web.fw import ReahlWSGIApplication
application = ReahlWSGIApplication.from_directory('/etc/reahl.d/hellonginx')
application.start()

