# Copyright 2013-2018 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from sqlalchemy import Column, ForeignKey, Integer
from webob import Response

from reahl.tofu import scenario, Fixture, uses
from reahl.stubble import stubclass, EmptyStub
from reahl.tofu.pytestsupport import with_fixtures

from reahl.sqlalchemysupport import Session
from reahl.component.py3compat import ascii_as_bytes_or_str
from reahl.webdeclarative.webdeclarative import UserSession, SessionData, UserInput

from reahl.web.ui import Form
from reahl.web_dev.fixtures import WebFixture
from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture
from reahl.domain_dev.fixtures import PartyAccountFixture


@with_fixtures(WebFixture)
def test_session_active_state(web_fixture):
    """The session is active if the last user interaction was in the last idle_lifetime """
    fixture = web_fixture
    user_session = fixture.context.session
    config = fixture.config

    # Case: recent interaction
    user_session.set_last_activity_time()
    assert user_session.is_active()

    # Case: last interaction not recent
    user_session.last_activity = datetime.now() - timedelta(seconds=user_session.idle_lifetime+10)
    assert not user_session.is_active()


@uses(web_fixture=WebFixture)
class SecureScenarios(Fixture):

    @scenario
    def secure(self):
        self.scheme = 'https'
        self.last_activity = datetime.now()
        self.secure_cookie = self.web_fixture.context.session.secure_salt
        self.expect_secure = True

    @scenario
    def insecure_scheme(self):
        self.secure()
        self.scheme = 'http'
        self.expect_secure = False

    @scenario
    def old_interaction(self):
        self.secure()
        self.last_activity = datetime.now() - timedelta(seconds=self.web_fixture.config.web.idle_secure_lifetime+10)
        self.expect_secure = False

    @scenario
    def bad_cookie(self):
        self.secure()
        self.secure_cookie = 'bad cookie value'
        self.expect_secure = False


@with_fixtures(WebFixture, SecureScenarios)
def test_session_secure_state(web_fixture, secure_scenarios):
    """The session is only secured when used over https, the secure cookie is set correctly,
       and the last interaction is within idle_secure_lifetime"""
    fixture = secure_scenarios

    user_session = web_fixture.context.session
    config = web_fixture.config
    context = web_fixture.context
    assert config.web.idle_secure_lifetime < config.web.idle_lifetime
    assert config.web.idle_lifetime < config.web.idle_lifetime_max

    web_fixture.request.scheme = fixture.scheme
    user_session.last_activity = fixture.last_activity
    context.request.cookies[context.config.web.secure_key_name] = fixture.secure_cookie
    assert user_session.is_secured() is fixture.expect_secure


@with_fixtures(SqlAlchemyFixture, WebFixture)
def test_setting_cookies_on_response(sql_alchemy_fixture, web_fixture):
    """How UserSession sets session and secure cookies in the response."""
    fixture = web_fixture
    @stubclass(UserSession)
    class UserSessionStub(UserSession):
        __tablename__ = 'usersessionstub'
        __mapper_args__ = {'polymorphic_identity': 'usersessionstub'}
        id = Column(Integer, ForeignKey('usersession.id'), primary_key=True)

        secured = False
        def is_secured(self):
            return self.secured

    with sql_alchemy_fixture.persistent_test_classes(UserSessionStub):
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
        assert session_cookie.value == urllib_parse.quote(user_session.as_key())
        assert session_cookie['path'] == '/'
        assert not session_cookie['max-age']
        #assert 'httponly' in session_cookie

        assert fixture.config.web.secure_key_name not in response.cookies


        # Case: with an secured session, set the session cookie and the secure cookie
        user_session.secured = True
        response = ResponseStub()

        user_session.set_session_key(response)

        assert fixture.config.web.session_key_name in response.cookies

        secure_cookie = response.cookies[fixture.config.web.secure_key_name]
        assert user_session.secure_salt == secure_cookie.value
        assert secure_cookie['path'] == '/'
        assert secure_cookie['max-age'] == '%s' % fixture.config.web.idle_secure_lifetime
        assert 'secure' in secure_cookie
        #assert 'httponly' in secure_cookie


@with_fixtures(WebFixture)
def test_reading_cookies_on_initialising_a_session(web_fixture):
    fixture = web_fixture

    # Case: session cookie not set in Request
    UserSession.initialise_web_session_on(fixture.context)
    assert not fixture.context.session.is_active()
    assert not fixture.context.session.is_secured()

    # Case: session cookie set in Request
    fixture.context.session = None
    user_session = UserSession()
    user_session.set_last_activity_time()
    Session.add(user_session)

    fixture.request.headers['Cookie'] = ascii_as_bytes_or_str('reahl=%s' % user_session.as_key())
    UserSession.initialise_web_session_on(fixture.context)

    assert fixture.context.session is user_session
    assert fixture.context.session.is_active()
    assert not fixture.context.session.is_secured()

    # Case: session cookie set, secure cookie also set in Request, https
    fixture.request.scheme = 'https'
    fixture.context.session = None
    user_session = UserSession()
    user_session.set_last_activity_time()
    Session.add(user_session)

    fixture.request.headers['Cookie'] = ascii_as_bytes_or_str('reahl=%s , reahl_secure=%s' % \
                                        (user_session.as_key(), user_session.secure_salt))
    UserSession.initialise_web_session_on(fixture.context)

    assert fixture.context.session is user_session
    assert fixture.context.session.is_active()
    assert fixture.context.session.is_secured()

    # Case: session cookie set, secure cookie also set in Request, http
    fixture.request.scheme = 'http'
    fixture.context.session = None
    user_session = UserSession()
    user_session.set_last_activity_time()
    Session.add(user_session)
    fixture.request.headers['Cookie'] = ascii_as_bytes_or_str('reahl=%s , reahl_secure=%s' % \
                                        (user_session.as_key(), user_session.secure_salt))

    UserSession.initialise_web_session_on(fixture.context)

    assert fixture.context.session is user_session
    assert fixture.context.session.is_active()
    assert not fixture.context.session.is_secured()


@with_fixtures(WebFixture)
def test_session_data_disappears_when_session_does(web_fixture):
    """When a UserSession is deleted, all associated SessionData disappear as well."""
    fixture = web_fixture

    UserSession.initialise_web_session_on(fixture.context)
    user_session = fixture.context.session
    ui_name = 'user_interface'
    channel_name = 'channel'

    session_data = SessionData(web_session=user_session, ui_name=ui_name, channel_name=channel_name)
    Session.add(session_data)
    Session.flush()

    Session.delete(user_session)

    assert Session.query(SessionData).filter_by(id=session_data.id).count() == 0
    assert Session.query(UserSession).filter_by(id=user_session.id).count() == 0


@with_fixtures(WebFixture)
def test_session_keeps_living(web_fixture):
    """When SessionData is deleted, the associated UserSession is not affected."""
    fixture = web_fixture

    UserSession.initialise_web_session_on(fixture.context)
    user_session = fixture.context.session
    ui_name = 'user_interface'
    channel_name = 'channel'

    session_data = SessionData(web_session=user_session, ui_name=ui_name, channel_name=channel_name)
    Session.add(session_data)
    Session.flush()

    Session.delete(session_data)

    assert Session.query(SessionData).filter_by(id=session_data.id).count() == 0
    assert Session.query(UserSession).filter_by(id=user_session.id).one() is user_session


class InputScenarios(Fixture):
    @scenario
    def text(self):
        self.entered_input_type = six.text_type
        self.entered_input = 'some value to save'
        self.empty_entered_input = ''

    @scenario
    def lists(self):
        self.entered_input_type = list
        self.entered_input = ['one', 'two']
        self.empty_entered_input = []


@with_fixtures(PartyAccountFixture, InputScenarios)
def test_persisting_input(party_account_fixture, input_scenarios):
    """UserInput can persist and find user input entered as a string or a list of strings (useful for things
       like multiple select boxes or multiple checkboxes with the same name).
    """
    @stubclass(Form)
    class FormStub(object):
        user_interface = EmptyStub(name='myui')
        channel_name = 'myform'

    fixture = input_scenarios
    form = FormStub()

    # If never persisted, getting it returns None
    previously_entered = UserInput.get_previously_entered_for_form(form, 'aninput', fixture.entered_input_type)
    assert previously_entered is None

    # Once persisted, getting it returns what you persisted
    UserInput.save_input_value_for_form(form, 'aninput', fixture.entered_input, fixture.entered_input_type)
    previously_entered = UserInput.get_previously_entered_for_form(form, 'aninput', fixture.entered_input_type)
    assert previously_entered == fixture.entered_input

    # Persisting empty values returns them correctly, not None (None means was not entered previously)
    UserInput.clear_for_form(form)
    previously_entered = UserInput.get_previously_entered_for_form(form, 'aninput', fixture.entered_input_type)
    assert previously_entered is None

    UserInput.save_input_value_for_form(form, 'aninput', fixture.empty_entered_input, fixture.entered_input_type)
    previously_entered = UserInput.get_previously_entered_for_form(form, 'aninput', fixture.entered_input_type)
    assert previously_entered == fixture.empty_entered_input


