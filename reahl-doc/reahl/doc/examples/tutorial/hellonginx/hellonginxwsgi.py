from __future__ import unicode_literals
from __future__ import print_function
from reahl.web.fw import ReahlWSGIApplication
application = ReahlWSGIApplication.from_directory('/etc/reahl.d/hellonginx')
application.start()

