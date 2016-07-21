from __future__ import print_function, unicode_literals, absolute_import, division
import os

from reahl.web.fw import UserInterface

web.site_root = UserInterface
web.static_root = os.getcwd()
