# Copyright 2013, 2014 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from __future__ import print_function, unicode_literals, absolute_import, division
from datetime import datetime, timedelta

import six
from six.moves import http_cookies
from six.moves.urllib import parse as urllib_parse

from sqlalchemy import Column, ForeignKey, Integer, inspect
from webob import Response

from nose.tools import istest
from reahl.tofu import test, scenario, vassert
from reahl.stubble import stubclass

from reahl.sqlalchemysupport import metadata, Session
from reahl.web_dev.fixtures import WebFixture
from reahl.component.py3compat import ascii_as_bytes_or_str
from reahl.webdeclarative.webdeclarative import UserSession, SessionData


@istest
class BasicTests(object):
    @test(WebFixture)
    def session_active_state(self, fixture):
        """The session is active if the last user interaction was in the last idle_lifetime """     
        user_session = fixture.context.session
        config = fixture.config

        # Case: recent interaction
        user_session.set_last_activity_time()
        vassert( user_session.is_active() )

        # Case: last interaction not recent
        user_session.last_activity = datetime.now() - timedelta(seconds=user_session.idle_lifetime+10)
        vassert( not user_session.is_active() )

    class SecureScenarios(WebFixture):
        @scenario
        def secure(self):
            self.scheme = 'https'
            self.last_activity = datetime.now()
            self.secure_cookie = self.context.session.secure_salt
            self.expect_secure = True

        @scenario
        def insecure_scheme(self):
            self.secure()
            self.scheme = 'http'
            self.expect_secure = False

        @scenario
        def old_interaction(self):
            self.secure()
            self.last_activity = datetime.now() - timedelta(seconds=self.config.web.idle_secure_lifetime+10)
            self.expect_secure = False

        @scenario
        def bad_cookie(self):
            self.secure()
            self.secure_cookie = 'bad cookie value'
            self.expect_secure = False

            
    @test(SecureScenarios)
    def session_secure_state(self, fixture):
        """The session is only secured when used over https, the secure cookie is set correctly,
           and the last interaction is within idle_secure_lifetime"""     
        user_session = fixture.context.session
        config = fixture.config
        context = fixture.context
        vassert( config.web.idle_secure_lifetime < config.web.idle_lifetime )
        vassert( config.web.idle_lifetime < config.web.idle_lifetime_max )

        fixture.request.scheme = fixture.scheme
        user_session.last_activity = fixture.last_activity
        context.request.cookies[context.config.web.secure_key_name] = fixture.secure_cookie
        vassert( user_session.is_secured() is fixture.expect_secure )

    @test(WebFixture)
    def setting_cookies_on_response(self, fixture):
        """How WebExecutionContext sets session and secure cookies in the response."""
        @stubclass(UserSession)
        class UserSessionStub(UserSession):
            __tablename__ = 'usersessionstub'
            __mapper_args__ = {'polymorphic_identity': 'usersessionstub'}
            id = Column(Integer, ForeignKey('usersession.id'), primary_key=True)

            secured = False
            def is_secured(self):
                return self.secured

        with fixture.persistent_test_classes(UserSessionStub):
            user_session = UserSessionStub()

            class ResponseStub(Response):
                @property
                def cookies(self):
                    cookies = http_cookies.SimpleCookie()
                    for header, value in self.headerlist:
                        if header == 'Set-Cookie':
                            cookies.load(value)
                    return cookies

            # Case: with an unsecured session, set only the session cookie
            user_session.secured = False
            response = ResponseStub()

            user_session.set_session_key(response)

            session_cookie = response.cookies[fixture.config.web.session_key_name]
            vassert( session_cookie.value == urllib_parse.quote(user_session.as_key()) )
            vassert( session_cookie['path'] == '/' )
            vassert( not session_cookie['max-age'] )
            #vassert( 'httponly' in session_cookie )

            vassert( fixture.config.web.secure_key_name not in response.cookies )


            # Case: with an secured session, set the session cookie and the secure cookie
            user_session.secured = True
            response = ResponseStub()

            user_session.set_session_key(response)

            vassert( fixture.config.web.session_key_name in response.cookies )

            secure_cookie = response.cookies[fixture.config.web.secure_key_name]
            vassert( user_session.secure_salt == secure_cookie.value )
            vassert( secure_cookie['path'] == '/' )
            vassert( secure_cookie['max-age'] == '%s' % fixture.config.web.idle_secure_lifetime )
            vassert( 'secure' in secure_cookie )
            #vassert( 'httponly' in secure_cookie )
        

    @test(WebFixture)
    def reading_cookies_on_initialising_a_session(self, fixture):
        # Case: session cookie not set in Request
        fixture.context.initialise_web_session()
        vassert( not fixture.context.session.is_active() )
        vassert( not fixture.context.session.is_secured() )
        
        # Case: session cookie set in Request
        fixture.context.set_session(None)
        user_session = UserSession()
        user_session.set_last_activity_time()
        Session.add(user_session)

        fixture.request.headers['Cookie'] = ascii_as_bytes_or_str('reahl=%s' % user_session.as_key())
        fixture.context.initialise_web_session()
        
        vassert( fixture.context.session is user_session )
        vassert( fixture.context.session.is_active() )
        vassert( not fixture.context.session.is_secured() )

        # Case: session cookie set, secure cookie also set in Request, https
        fixture.request.scheme = 'https'
        fixture.context.set_session(None)
        user_session = UserSession()
        user_session.set_last_activity_time()
        Session.add(user_session)

        fixture.request.headers['Cookie'] = ascii_as_bytes_or_str('reahl=%s , reahl_secure=%s' % \
                                            (user_session.as_key(), user_session.secure_salt))
        fixture.context.initialise_web_session()

        vassert( fixture.context.session is user_session )
        vassert( fixture.context.session.is_active() )
        vassert( fixture.context.session.is_secured() )

        # Case: session cookie set, secure cookie also set in Request, http
        fixture.request.scheme = 'http'
        fixture.context.set_session(None)
        user_session = UserSession()
        user_session.set_last_activity_time()
        Session.add(user_session)
        fixture.request.headers['Cookie'] = ascii_as_bytes_or_str('reahl=%s , reahl_secure=%s' % \
                                            (user_session.as_key(), user_session.secure_salt))
         
        fixture.context.initialise_web_session()

        vassert( fixture.context.session is user_session )
        vassert( fixture.context.session.is_active() )
        vassert( not fixture.context.session.is_secured() )

    @test(WebFixture)
    def session_data_disappears_when_session_does(self, fixture):
        """When a UserSession is deleted, all associated SessionData disappear as well."""

        fixture.context.initialise_web_session()
        user_session = fixture.context.session 
        ui_name = 'user_interface'
        channel_name = 'channel'

        session_data = SessionData(web_session=user_session, ui_name=ui_name, channel_name=channel_name)
        Session.add(session_data)
        Session.flush()

        Session.delete(user_session)

        vassert( Session.query(SessionData).filter_by(id=session_data.id).count() == 0 )
        vassert( Session.query(UserSession).filter_by(id=user_session.id).count() == 0 )

    @test(WebFixture)
    def session_keeps_living(self, fixture):
        """When SessionData is deleted, the associated UserSession is not affected."""

        fixture.context.initialise_web_session()
        user_session = fixture.context.session 
        ui_name = 'user_interface'
        channel_name = 'channel'

        session_data = SessionData(web_session=user_session, ui_name=ui_name, channel_name=channel_name)
        Session.add(session_data)
        Session.flush()

        Session.delete(session_data)

        vassert( Session.query(SessionData).filter_by(id=session_data.id).count() == 0 )
        vassert( Session.query(UserSession).filter_by(id=user_session.id).one() is user_session )


