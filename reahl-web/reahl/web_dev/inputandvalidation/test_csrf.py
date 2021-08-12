# Copyright 2021 Reahl Software Services (Pty) Ltd. All rights reserved.
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


import datetime
import base64
from webob.exc import HTTPForbidden

from reahl.tofu import Fixture, scenario, expected, uses, NoException
from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import stubclass

from reahl.component.context import  ExecutionContext
from reahl.component.modelinterface import Action, Event, exposed
from reahl.web.ui import Form, CSRFToken, ExpiredCSRFToken, InvalidCSRFToken, ButtonInput
from reahl.browsertools.browsertools import WidgetTester
from reahl.browsertools.browsertools import XPath

from reahl.web_dev.fixtures import WebFixture


@with_fixtures(WebFixture)
def test_submit_form_with_invalid_csrf_token(web_fixture):
    fixture = web_fixture

    class MyForm(Form):
        def __init__(self, view):
            super().__init__(view, 'myform')

            self.define_event_handler(self.events.submit_break)
            self.add_child(ButtonInput(self, self.events.submit_break))

        @exposed
        def events(self, events):
            events.submit_break = Event(label='Submit')


    wsgi_app = web_fixture.new_wsgi_app(child_factory=MyForm.factory(), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser

    browser.open('/')
    browser.execute_script('$("#id-myform-_reahl_csrf_token").attr("value", "%s")' % 'invalid csrf token value')
    assert not browser.is_element_present(XPath.heading(1).with_text("403 Forbidden"))
    browser.click(XPath.button_labelled('Submit'))
    assert browser.is_element_present(XPath.heading(1).with_text("403 Forbidden"))


@with_fixtures(WebFixture)
def test_check_csrf_token_match(web_fixture):
    token = CSRFToken(value='hello world')
    csrf_token = token.as_signed_string()

    reconstructed_token = CSRFToken.from_coded_string(csrf_token)
    assert reconstructed_token.value == 'hello world'
    assert reconstructed_token.matches(token)


@with_fixtures(WebFixture)
def test_csrf_fiddled_value(web_fixture):

    token = CSRFToken(value='hello world')
    csrf_token = token.as_signed_string()
    value, timestamp, signature = csrf_token.split(":")

    crafted_value = base64.urlsafe_b64encode('new world'.encode()).decode('utf-8')
    crafted_token_string = ':'.join([crafted_value, timestamp, signature])
    with expected(InvalidCSRFToken):
        CSRFToken.from_coded_string(crafted_token_string)


@with_fixtures(WebFixture)
def test_csrf_botched_value(web_fixture):

    with expected(InvalidCSRFToken):
        CSRFToken.from_coded_string("someting without delimeters")


@stubclass(CSRFToken)
class CSRFTokenWithSetTimestamp(CSRFToken):
    def __init__(self, time):
        super().__init__()
        self.time = time

    def get_now_timestamp_string(self):
        return repr(self.time.timestamp())

@with_fixtures(WebFixture)
def test_csrf_stale_token(web_fixture):
    """A Token is only valid if reconstructed within a specified time."""
    now = datetime.datetime.now(tz=datetime.timezone.utc)

    #case recent timestamp
    token = CSRFTokenWithSetTimestamp(now)
    with expected(NoException):
        CSRFToken.from_coded_string(token.as_signed_string())

    #case old timestamp
    allowed_timeout = ExecutionContext.get_context().config.web.csrf_timeout_seconds
    stale_time = now - datetime.timedelta(seconds=allowed_timeout+1)
    stale_token = CSRFTokenWithSetTimestamp(stale_time)
    with expected(ExpiredCSRFToken):
        CSRFToken.from_coded_string(stale_token.as_signed_string())

    #case future timestamp
    seconds_into_future = 300
    future_time = now + datetime.timedelta(seconds=seconds_into_future)
    future_token = CSRFTokenWithSetTimestamp(future_time)
    with expected(ExpiredCSRFToken):
        CSRFToken.from_coded_string(future_token.as_signed_string())
