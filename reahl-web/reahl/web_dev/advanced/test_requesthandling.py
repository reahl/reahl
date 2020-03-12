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

import threading

from webob import Request, Response
from webob.exc import HTTPNotFound

from reahl.component.dbutils import SystemControl
from reahl.tofu import expected, Fixture, scenario
from reahl.tofu.pytestsupport import with_fixtures, uses
from reahl.stubble import stubclass, CallMonitor, exempt

from reahl.component.context import ExecutionContext
from reahl.web.fw import Resource, ReahlWSGIApplication, InternalRedirect, UserInterface
from reahl.web.interfaces import UserSessionProtocol
from reahl.dev.fixtures import ReahlSystemFixture
from reahl.web.ui import HTML5Page
from reahl.web_dev.fixtures import ReahlWSGIApplicationStub, BasicPageLayout
from reahl.webdev.tools import Browser

from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture
from reahl.web_dev.fixtures import WebFixture


class WSGIFixture(Fixture):
    status = None
    headers = None
    def result_is_valid(self, result):
        return result.startswith('<!DOCTYPE html><html ') and result.endswith('</html>')
    def some_headers_are_set(self, headers):
        return dict(headers)['Content-Type'] == 'text/html; charset=utf-8'


@with_fixtures(WebFixture, WSGIFixture)
def test_wsgi_interface(web_fixture, wsgi_fixture):
    """A ReahlWSGIApplication is a WSGI application."""
    fixture = wsgi_fixture
    wsgi_app = web_fixture.wsgi_app

    environ = Request.blank('/', charset='utf8').environ
    def start_response(status, headers):
        fixture.status = status
        fixture.headers = headers

    wsgi_iterator = wsgi_app(environ, start_response)

    result = ''.join([i.decode('utf-8') for i in wsgi_iterator])  # To check that it is iterable and get the value
    assert fixture.result_is_valid(result)
    assert fixture.status == '200 OK'
    assert fixture.some_headers_are_set(fixture.headers)\


@uses(web_fixture=WebFixture)
class WSGIWithAppFixture(WSGIFixture):
    def new_wsgi_app(self):
        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(HTML5Page).use_layout(BasicPageLayout())
                self.define_view('/', title='Home page')
        config = self.web_fixture.config
        config.web.site_root = MainUI

        return ReahlWSGIApplication(config)

    def call_wsgi_app(self):
        environ = Request.blank('/', charset='utf8').environ
        def start_response(status, headers):
            self.status = status
            self.headers = headers

        wsgi_iterator = self.wsgi_app(environ, start_response)
        result = ''.join([i.decode('utf-8') for i in wsgi_iterator]) #so it gets __call_'ed


@stubclass(SystemControl)
class SystemControlStub(SystemControl):
    @exempt
    def set_as_connected(self, status):
        self.connect_status = status

    def connect(self):
        pass

    def disconnect(self):
        pass

    @property
    def connected(self):
        return self.connect_status


@uses(web_fixture=WebFixture)
class ConnectScenarios(Fixture):

    def new_system_control(self):
        return SystemControlStub(self.web_fixture.config)

    @scenario
    def not_connected(self):
        self.connected = False

    @scenario
    def connected(self):
        self.connected = True


@with_fixtures(WSGIWithAppFixture, ConnectScenarios)
def test_wsgi_connect_on_start(wsgi_fixture, connect_scenario):
    """A ReahlWSGIApplication can make its system_control_connect, if it is not already connected."""
    wsgi_app = wsgi_fixture.wsgi_app
    wsgi_app.system_control = connect_scenario.system_control

    connect_scenario.system_control.set_as_connected(connect_scenario.connected)

    with CallMonitor(connect_scenario.system_control.connect) as monitor:

        assert not wsgi_app.started
        wsgi_fixture.call_wsgi_app()
        assert wsgi_app.started

    if connect_scenario.connected:
        assert len(monitor.calls) == 0
    else:
        assert len(monitor.calls) == 1


@stubclass(SystemControl)
class SystemControlSlowConnectStub(SystemControl):
    is_connected = False
    @exempt
    def block_connect(self):
        self.connect_lock = threading.Lock()
        self.connect_lock.acquire()

    @exempt
    def unblock_connect(self):
        self.connect_lock.release()

    def connect(self):
        if self.connect_lock.acquire(False):
            raise Exception('Another thread should not be here')
        self.connect_lock.acquire() #first thread to get here will block
        self.connect_lock.release()
        self.is_connected = True

    @property
    def connected(self):
        return self.is_connected

    def disconnect(self):
        pass


@with_fixtures(WebFixture, WSGIWithAppFixture)
def test_wsgi_starts_on_first_call(web_fixture, wsgi_fixture):
    """Threads"""
    wsgi_app = wsgi_fixture.wsgi_app
    wsgi_app.system_control = SystemControlSlowConnectStub(web_fixture.config)

    wsgi_app.system_control.block_connect() #start will be calling this - use it to delay the first start

    assert not wsgi_app.system_control.connected
    assert not wsgi_app.started

    with CallMonitor(wsgi_app.start) as monitor:

        # simulate multiple requests hitting an app, whoever is first, will cause it to start
        thread1 = threading.Thread(target=wsgi_fixture.call_wsgi_app)
        thread1.start()

        thread2 = threading.Thread(target=wsgi_fixture.call_wsgi_app)
        thread2.start()

        wsgi_app.system_control.unblock_connect()
        thread1.join()
        thread2.join()

    assert wsgi_app.system_control.connected
    assert wsgi_app.started
    assert len(monitor.calls) == 1



@with_fixtures(ReahlSystemFixture, WebFixture)
def test_web_session_handling(reahl_system_fixture, web_fixture):
    """The core web framework (this egg) does not implement a notion of session directly.
       It relies on such a notion, but expects an implementation for this to be supplied.

       An implementation should implement the UserSessionProtocol. The implementation
       is thus responsible for associating an instance of itself with the current request.

       The implementation to be used is set in the web.session_class configuration setting.

       The framework ensures that an instance of web.session_class is available during any
       Request. The database is committed before any user code executes, so that any database activity
       done by web.session_class would be committed even if an exception in the user code occurs.
       After user code is executed, methods are called on the web.session_class so that it can set
       its key on the response and save the last_activity_time.
       Finally, another commit is issued to the database so that any database activity during these last
       actions would also be saved.
    """
    stubclass(UserSessionProtocol)
    class UserSessionStub(UserSessionProtocol):
        session = None
        last_activity_time_set = False
        key_is_set = False
        @classmethod
        def for_current_session(cls):
            assert None, 'Not implemented'

        @classmethod
        def get_or_create_session(cls):
            cls.session = cls()
            return cls.session

        @classmethod
        def initialise_web_session_on(cls, context):
            context.session = cls.get_or_create_session()

        def set_session_key(self, response):
            self.key_is_set = True
            self.saved_response = response

        def is_active(self): pass
        def is_secured(self): pass
        def set_as_logged_in(self, party, stay_logged_in): pass
        def log_out(self): pass

        def set_last_activity_time(self):
            self.last_activity_time_set = True

        def get_interface_locale(self):
            return 'en_gb'

    # Setting the implementation in config
    web_fixture.config.web.session_class = UserSessionStub
    with CallMonitor(reahl_system_fixture.system_control.orm_control.commit) as monitor:
        @stubclass(Resource)
        class ResourceStub(object):
            should_commit = True
            def cleanup_after_transaction(self):
                assert monitor.times_called == 2  # The database has been committed after user code started executed, before cleanup
            def handle_request(self, request):
                context = ExecutionContext.get_context()
                assert context.session is UserSessionStub.session  # By the time user code executes, the session is set
                assert monitor.times_called == 1  # The database has been committed before user code started executing
                assert not context.session.last_activity_time_set
                assert not UserSessionStub.session.key_is_set
                return Response()

        @stubclass(ReahlWSGIApplication)
        class ReahlWSGIApplicationStub2(ReahlWSGIApplicationStub):
            def resource_for(self, request):
                return ResourceStub()

        browser = Browser(ReahlWSGIApplicationStub2(web_fixture.config))

        # A session is obtained, and the correct params passed to the hook methods
        assert not UserSessionStub.session  # Before the request, the session is not yet set
        assert monitor.times_called == 0  # ... and the database is not yet committed
        browser.open('/')

        assert monitor.times_called == 2  # The database is committed to save session changes before user code and again after user code executed
        assert UserSessionStub.session  # The session was set
        assert UserSessionStub.session.key_is_set  # The set_session_key was called
        assert UserSessionStub.session.saved_response.status_int is 200  # The correct response was passed to set_session_key

        assert UserSessionStub.session.last_activity_time_set  # set_last_activity_time was called


@with_fixtures(WebFixture)
def test_handling_HTTPError_exceptions(web_fixture):
    """If an HTTPError exception is raised, it is used as response."""
    @stubclass(ReahlWSGIApplication)
    class ReahlWSGIApplicationStub2(ReahlWSGIApplicationStub):
        def resource_for(self, request):
            raise HTTPNotFound()

    browser = Browser(ReahlWSGIApplicationStub2(web_fixture.config))

    browser.open('/', status=404)


@with_fixtures(WebFixture)
def test_internal_redirects(web_fixture):
    """During request handling, an InternalRedirect exception can be thrown. This is handled by
       restarting the request loop from scratch to handle the same request again, using a freshly
       constructed resource just as though the request was submitted again by the browser
       save for the browser round trip."""

    fixture = web_fixture
    fixture.requests_handled = []
    fixture.handling_resources = []

    @stubclass(Resource)
    class ResourceStub(object):
        should_commit = True
        def cleanup_after_transaction(self): pass
        def handle_request(self, request):
            fixture.requests_handled.append(request)
            fixture.handling_resources.append(self)
            if hasattr(request, 'internal_redirect'):
                return Response(body='response given after internal redirect')
            raise InternalRedirect(None, None)

    @stubclass(ReahlWSGIApplication)
    class ReahlWSGIApplicationStub2(ReahlWSGIApplicationStub):
        def resource_for(self, request):
            return ResourceStub()

    browser = Browser(ReahlWSGIApplicationStub2(fixture.config))

    browser.open('/')

    assert browser.raw_html == 'response given after internal redirect'
    assert fixture.requests_handled[0] is fixture.requests_handled[1]
    assert fixture.handling_resources[0] is not fixture.handling_resources[1]


@with_fixtures(WebFixture)
def test_handling_uncaught_exceptions(web_fixture):
    """If an uncaught exception is raised, the session is closed properly."""

    @stubclass(ReahlWSGIApplication)
    class ReahlWSGIApplicationStub2(ReahlWSGIApplicationStub):
        def resource_for(self, request):
            raise AssertionError('this an unknown breakage')


    app = ReahlWSGIApplicationStub2(web_fixture.config)
    browser = Browser(app)

    with CallMonitor(app.system_control.finalise_session) as monitor:
        assert monitor.times_called == 0
        with expected(AssertionError):
            browser.open('/')
        assert monitor.times_called == 1
