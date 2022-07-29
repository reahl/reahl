# Copyright 2013-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
#
#    This file is part of Reahl.
#
#    Reahl is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation; version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Configuration for reahl-web.
"""

import os

from reahl.component.context import ExecutionContext
from reahl.component.config import Configuration, ConfigSetting
from reahl.web.libraries import LibraryIndex, JQuery, JQueryUI, Underscore, HTML5Shiv, IE9, Reahl, Holder, Popper, \
    Bootstrap4, ReahlBootstrap4Additions, JsCookie, PlotlyJS


class WebConfig(Configuration):
    filename = 'web.config.py'
    config_key = 'web'

    site_root = ConfigSetting(description='The UserInterface class to be used as the root of the web application')
    static_root = ConfigSetting(default=os.getcwd(),
                                description='The directory from which static files will be served',
                                dangerous=True)
    frontend_libraries = ConfigSetting(description='A collection of front end libraries to include on pages')
    session_key_name = ConfigSetting(default='reahl',
                                     description='The name of this site\'s cookie in a user\'s a browser')
    guest_key_name = ConfigSetting(default='reahl-guest',
                                   description='The name of the cookie used to store information about anonymous visitors')
    guest_key_lifetime = ConfigSetting(default=60*60*24*365,
                                       description='The expiry time in seconds of the anonymous visitors cookie')

    session_class = ConfigSetting(description='The class used for UserSessions',
                                  automatic=True)
    persisted_exception_class = ConfigSetting(description='The class used for PersistedExceptions',
                                              automatic=True)
    persisted_userinput_class = ConfigSetting(description='The class used for UserInput',
                                              automatic=True)
    persisted_file_class = ConfigSetting(description='The class used for PersistedFiles',
                                              automatic=True)
    
    encrypted_http_scheme = ConfigSetting(default='https',
                                          description='The http scheme used for encrypted connections.')
    default_http_scheme = ConfigSetting(default='http',
                                        description='The http scheme used when an encrypted connection is not required' )
    encrypted_http_port = ConfigSetting(default='8363',
                                        description='The http port used for encrypted connections.',
                                        dangerous=True)
    default_http_port = ConfigSetting(default='8000',
                                      description='The http port used when an encrypted connection is not required',
                                      dangerous=True )
    default_url_locale = ConfigSetting(default='en_gb',
                                       description='The locale used when no locale is present in an URL')
    cache_max_age = ConfigSetting(default=10*60,
                                  description='The max time (in seconds) a cacheable dynamic page should be cached for')
    session_lifetime = ConfigSetting(default=60*60*24*7*2,
                                     description='The time in seconds a user session will be kept after last use')
    idle_lifetime = ConfigSetting(default=60*60*2,
                                  description='The time in seconds after which a user session will be considered not logged in anymore')
    idle_lifetime_max = ConfigSetting(default=60*60*24*7*2,
                                      description='The time in seconds after which a user session will be considered not logged in anymore - when the user opted to stay logged in')
    idle_secure_lifetime = ConfigSetting(default=60*60,
                                         description='The time in seconds after which a secure session will be considered expired')
    debug_concurrency_hash = ConfigSetting(default=False,
                                   description='If True, replaces the concurrency hash with a long string indicating the values used in calculating the hash')
    csrf_key = ConfigSetting(default='unsafekey',
                             description='Used to sign CSRF tokens for a site. Set this to a secret long string unique to your deployment.',
                             dangerous=True)
    csrf_timeout_seconds = ConfigSetting(default=60*15,
                                         description='Forms have to be submitted within this time (in seconds) after being rendered.')

    @property
    def secure_key_name(self):
        return '%s_secure' % self.session_key_name

    def __init__(self):
        super().__init__()
        # We create it here, so that each instance of a WebConfig will have its own LibraryIndex instance
        self.frontend_libraries = LibraryIndex(JQuery(), JsCookie(), JQueryUI(), Underscore(), HTML5Shiv(), IE9(), Reahl(), Holder(),
                                               Popper(),  # must be before Bootstrap in html script includes
                                               Bootstrap4(), ReahlBootstrap4Additions(), PlotlyJS())
