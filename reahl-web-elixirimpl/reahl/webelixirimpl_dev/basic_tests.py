# Copyright 2011, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from __future__ import unicode_literals
from __future__ import print_function
import six
from six.moves import http_cookies
from six.moves.urllib import parse as urllib_parse

from webob import Response
from elixir import using_options

from nose.tools import istest
from reahl.tofu import test
from reahl.tofu import vassert
from reahl.stubble import stubclass

from reahl.sqlalchemysupport import metadata, Session
from reahl.web_dev.fixtures import WebFixture

from reahl.webelixirimpl import WebUserSession


@istest
class BasicTests(object):
    @test(WebFixture)
    def web_session_handling_of_login(self, fixture):
        """  """     
        web_session = fixture.context.session
        account = fixture.system_account
        config = fixture.config
        context = fixture.context
        vassert( config.accounts.idle_secure_lifetime < config.accounts.idle_lifetime )
        vassert( config.accounts.idle_lifetime < config.accounts.idle_lifetime_max )

        # Case: user logs in over http
        fixture.request.scheme = 'http'
        web_session.last_activity = None
        web_session.set_as_logged_in(account, False)
        context.request.cookies[context.config.web.secure_key_name] = web_session.secure_salt
        vassert( web_session.is_logged_in() )
        vassert( not web_session.is_secure() )

        # Case: user logs in over https
        fixture.request.scheme = 'https'
        web_session.last_activity = None
        web_session.set_as_logged_in(account, False)
        context.request.cookies[context.config.web.secure_key_name] = web_session.secure_salt
        vassert( web_session.is_logged_in() )
        vassert( web_session.is_secure() )

    @test(WebFixture)
    def setting_cookies_on_response(self, fixture):
        """How WebExecutionContext sets session and secure cookies in the response."""
        @stubclass(WebUserSession)
        class WebUserSessionStub(WebUserSession):
            using_options(metadata=metadata, session=Session, shortnames=True)
            secured = False
            def is_secure(self):
                return self.secured

        with fixture.persistent_test_classes(WebUserSessionStub):
            web_session = WebUserSessionStub()

            class ResponseStub(Response):
                @property
                def cookies(self):
                    cookies = http_cookies.SimpleCookie()
                    for header, value in self.headerlist:
                        if header == 'Set-Cookie':
                            cookies.load(value)
                    return cookies

            # Case: with an unsecured session, set only the session cookie
            web_session.secured = False
            response = ResponseStub()

            web_session.set_session_key(response)

            session_cookie = response.cookies[fixture.config.web.session_key_name]
            vassert( session_cookie.value == urllib_parse.quote(web_session.as_key()) )
            vassert( session_cookie['path'] == '/' )
            vassert( not session_cookie['max-age'] )
            #vassert( 'httponly' in session_cookie )

            vassert( fixture.config.web.secure_key_name not in response.cookies )


            # Case: with an secured session, set the session cookie and the secure cookie
            web_session.secured = True
            response = ResponseStub()

            web_session.set_session_key(response)

            vassert( fixture.config.web.session_key_name in response.cookies )

            secure_cookie = response.cookies[fixture.config.web.secure_key_name]
            vassert( web_session.secure_salt == secure_cookie.value )
            vassert( secure_cookie['path'] == '/' )
            vassert( secure_cookie['max-age'] == '%s' % fixture.config.accounts.idle_secure_lifetime )
            vassert( 'secure' in secure_cookie )
            #vassert( 'httponly' in secure_cookie )
        

    @test(WebFixture)
    def reading_cookies_on_initialising_a_session(self, fixture):
        account = fixture.system_account
        
        # Case: session cookie not set in Request
        fixture.context.initialise_web_session()
        vassert( not fixture.context.session.is_logged_in() )
        vassert( not fixture.context.session.is_secure() )
        
        # Case: session cookie set in Request
        fixture.context.set_session(None)
        web_session = WebUserSession()
        fixture.request.headers['Cookie'] = ('reahl=%s' % web_session.as_key()).encode('utf-8')

        fixture.context.initialise_web_session()
        
        vassert( fixture.context.session is web_session )
        vassert( not fixture.context.session.is_logged_in() )
        vassert( not fixture.context.session.is_secure() )

        # Case: session cookie set, secure cookie also set in Request, https
        fixture.request.scheme = 'https'
        fixture.context.set_session(None)
        web_session = WebUserSession()
        web_session.set_as_logged_in(account, False)

        fixture.request.headers['Cookie'] = ('reahl=%s , reahl_secure=%s' % \
                                            (web_session.as_key(), web_session.secure_salt)).encode('utf-8')
        fixture.context.initialise_web_session()

        vassert( fixture.context.session is web_session )
        vassert( fixture.context.session.account is account )
        vassert( fixture.context.session.is_logged_in() )
        vassert( fixture.context.session.is_secure() )

        # Case: session cookie set, secure cookie also set in Request, http
        fixture.request.scheme = 'http'
        fixture.context.set_session(None)
        web_session = WebUserSession()
        web_session.set_as_logged_in(account, False)
        fixture.request.headers['Cookie'] = ('reahl=%s , reahl_secure=%s' % \
                                            (web_session.as_key(), web_session.secure_salt)).encode('utf-8')
         
        fixture.context.initialise_web_session()

        vassert( fixture.context.session is web_session )
        vassert( fixture.context.session.account is account )
        vassert( fixture.context.session.is_logged_in() )
        vassert( not fixture.context.session.is_secure() )
