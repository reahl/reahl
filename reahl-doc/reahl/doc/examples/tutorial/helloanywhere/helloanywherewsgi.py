
import os
from reahl.web.fw import ReahlWSGIApplication
application = ReahlWSGIApplication.from_directory('%s/etc' % os.path.expanduser('~'), start_on_first_request=True)

