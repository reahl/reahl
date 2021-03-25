
from reahl.web.fw import ReahlWSGIApplication
application = ReahlWSGIApplication.from_directory('/etc/reahl.d/hellonginx', start_on_first_request=True)

