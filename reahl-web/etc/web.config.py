

import os

from reahl.web.fw import UserInterface

web.site_root = UserInterface
web.static_root = os.getcwd()
#web.csrf_timeout_seconds = 100000000
