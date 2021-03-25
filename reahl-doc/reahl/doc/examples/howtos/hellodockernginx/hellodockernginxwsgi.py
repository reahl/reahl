
from reahl.web.fw import ReahlWSGIApplication
application = ReahlWSGIApplication.from_directory('/etc/app-reahl', start_on_first_request=True)

