# Copyright 2021, 2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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


import time
import datetime
import base64

from selenium.common.exceptions import TimeoutException

from reahl.tofu import Fixture, scenario, expected, uses, NoException
from reahl.tofu.pytestsupport import with_fixtures

from reahl.component.context import  ExecutionContext
from reahl.component.modelinterface import Action, Event, ExposedNames, ChoiceField, Choice, IntegerField
from reahl.web.ui import Form, ButtonInput, FormLayout, SelectInput, P
from reahl.web.csrf import ExpiredCSRFToken, InvalidCSRFToken, CSRFToken
from reahl.browsertools.browsertools import XPath

from reahl.web_dev.fixtures import WebFixture



class CSRFFixture(Fixture):
    def new_MyForm(self):
        class MyForm(Form):
            def __init__(self, view):
                super().__init__(view, 'myform')
                self.enable_refresh()
                self.choice = 1
                self.use_layout(FormLayout())
                if self.exception:
                    self.layout.add_alert_for_domain_exception(self.exception)
                self.layout.add_input(SelectInput(self, self.fields.choice, refresh_widget=self))
                self.define_event_handler(self.events.submit_break)
                self.add_child(ButtonInput(self, self.events.submit_break))
                self.add_child(P(view, 'Chosen: %s' % self.choice))

            events = ExposedNames()
            events.submit_break = lambda i: Event(label='Submit')

            fields = ExposedNames()
            fields.choice = lambda i: ChoiceField([Choice(1, IntegerField(label='1')),
                                                   Choice(2, IntegerField(label='2'))])


        return MyForm

    def set_csrf_token_in_rendered_form(self, browser, value):
        browser.execute_script('$("#id-myform-_reahl_csrf_token").attr("value", "%s")' % value)

    def get_csrf_token_in_rendered_form(self, browser):
        return browser.execute_script('return $("#id-myform-_reahl_csrf_token").attr("value")')

    def set_csrf_token_in_rendered_form_to_expired(self, browser):
        valid_token = self.get_csrf_token_in_rendered_form(browser)
        reconstructed_token = CSRFToken.from_coded_string(valid_token)
        allowed_timeout = ExecutionContext.get_context().config.web.csrf_timeout_seconds
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        stale_time = now - datetime.timedelta(seconds=allowed_timeout + 1)
        reconstructed_token.timestamp = stale_time.timestamp()
        stale_token_string = reconstructed_token.as_signed_string()
        self.set_csrf_token_in_rendered_form(browser, stale_token_string)


@with_fixtures(WebFixture, CSRFFixture)
def test_submit_form_with_invalid_csrf_token(web_fixture, csrf_fixture):
    """A Form cannot be submitted without the original CSRF token proving that it was rendered by us originally."""
    fixture = csrf_fixture

    wsgi_app = web_fixture.new_wsgi_app(child_factory=fixture.MyForm.factory(), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser

    browser.open('/')
    fixture.set_csrf_token_in_rendered_form(browser, 'invalid csrf token value')
    assert not browser.is_element_present(XPath.heading(1).with_text("403 Forbidden"))
    browser.click(XPath.button_labelled('Submit'))
    assert browser.is_element_present(XPath.heading(1).with_text("403 Forbidden"))


@with_fixtures(WebFixture, CSRFFixture)
def test_submit_form_with_expired_csrf_token(web_fixture, csrf_fixture):
    """A form submitted with a valid expired token, shows a validation exception. After refresh, a new token is received and submit works."""
    fixture = csrf_fixture

    wsgi_app = web_fixture.new_wsgi_app(child_factory=fixture.MyForm.factory(), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser

    browser.open('/')
    select_widget_path = XPath.select_labelled('choice')
    assert browser.get_value(select_widget_path) == '1'
    browser.select(select_widget_path, '2')

    wsgi_app.config.web.csrf_timeout_seconds = 0.5
    time.sleep(wsgi_app.config.web.csrf_timeout_seconds+0.1)
    browser.click(XPath.button_labelled('Submit'))
    wsgi_app.config.web.csrf_timeout_seconds = 300
    error_message = XPath.paragraph().including_text('This page has expired. For security reasons, please review your input and retry.')
    assert browser.is_element_present(error_message)

    #case: submit again should work now - new csrftoken received in GET
    browser.click(XPath.button_labelled('Submit'))
    assert not browser.is_element_present(error_message)


@with_fixtures(WebFixture, CSRFFixture)
def test_refresh_widget_with_expired_csrf_token(web_fixture, csrf_fixture):
    """An Ajax request done with a valid expired token, shows a validation exception. After refresh, a new token is received and submit works."""
    fixture = csrf_fixture

    wsgi_app = web_fixture.new_wsgi_app(child_factory=fixture.MyForm.factory(), enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser

    wsgi_app.config.reahlsystem.debug = False #causes redirect to the error page and not stacktrace

    browser.open('/')

    select_widget_path = XPath.select_labelled('choice')
    assert browser.get_value(select_widget_path) == '1'
    wsgi_app.config.web.csrf_timeout_seconds = 0.5
    time.sleep(wsgi_app.config.web.csrf_timeout_seconds+0.1)
    browser.select(select_widget_path, '2', wait_for_ajax=False)
    wsgi_app.config.web.csrf_timeout_seconds = 300

    with browser.alert_expected() as js_alert:
        assert js_alert.text == 'This page has expired. For security reasons, please review your input and retry.'
        js_alert.accept()

    #case: new csrftoken received in GET
    assert browser.get_value(select_widget_path) == '1'
    assert browser.wait_for_element_not_present(XPath.paragraph().with_text('Chosen: 2'))
    browser.select(select_widget_path, '2')

    assert browser.wait_for_element_present(XPath.paragraph().with_text('Chosen: 2'))
    assert browser.wait_for_not(browser.is_alert_present)


@with_fixtures(WebFixture)
def test_check_csrf_token_match(web_fixture):
    """A CSRFToken is transformed into a signed string, with timestamp, and can be reconstructed and matched with a reconstructed token."""
    token = CSRFToken(value='hello world')
    csrf_token = token.as_signed_string()

    assert len(csrf_token.split(':')) == 3

    reconstructed_token = CSRFToken.from_coded_string(csrf_token)
    assert reconstructed_token.value == 'hello world'
    assert reconstructed_token.matches(token)


@with_fixtures(WebFixture)
def test_csrf_fiddled_value(web_fixture):
    """A token with signature that does not match its contents is invalid."""
    token = CSRFToken(value='hello world')
    csrf_token = token.as_signed_string()
    value, timestamp, signature = csrf_token.split(":")

    crafted_value = base64.urlsafe_b64encode('new world'.encode()).decode('utf-8')
    crafted_token_string = ':'.join([crafted_value, timestamp, signature])
    with expected(InvalidCSRFToken):
        CSRFToken.from_coded_string(crafted_token_string)


@with_fixtures(WebFixture)
def test_csrf_malformed_token(web_fixture):
    """A malformed token is invalid."""
    with expected(InvalidCSRFToken):
        CSRFToken.from_coded_string("someting without delimeters")


@with_fixtures(WebFixture)
def test_csrf_with_invalid_timestamp(web_fixture):
    """A Token with a timestamp in the future is invalid."""
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    seconds_into_future = 300
    future_time = now + datetime.timedelta(seconds=seconds_into_future)
    future_token = CSRFToken(timestamp=future_time)
    with expected(InvalidCSRFToken):
        CSRFToken.from_coded_string(future_token.as_signed_string())
