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
from webob import Request, Response
from webob.exc import HTTPNotFound

from nose.tools import istest
from reahl.tofu import test
from reahl.tofu import vassert
from reahl.stubble import stubclass, CallMonitor

from reahl.web.fw import Resource, ReahlWSGIApplication, WebExecutionContext
from reahl.web.interfaces import WebUserSessionProtocol
from reahl.web_dev.fixtures import WebFixture, ReahlWSGIApplicationStub
from reahl.webdev.tools import Browser


@istest
class RequestHandlingTests(object):
    class WSGIFixture(WebFixture):
        status = None
        headers = None
        def result_is_valid(self, result):
            return result.startswith('<!DOCTYPE html><html>') and result.endswith('</html>')
        def some_headers_are_set(self, headers):
            return dict(headers)['Content-Type'] == 'text/html; charset=utf-8'

    @test(WSGIFixture)
    def wsgi_interface(self, fixture):
        """A ReahlWSGIApplication is a WSGI application."""

        wsgi_app = fixture.wsgi_app

        environ = Request.blank('/', charset='utf8').environ
        def start_response(status, headers):
            fixture.status = status
            fixture.headers = headers
        
        wsgi_iterator = wsgi_app(environ, start_response)

        result = ''.join([i for i in wsgi_iterator])  # To check that it is iterable and get the value
        vassert( fixture.result_is_valid(result) )
        vassert( fixture.status == '200 OK' )
        vassert( fixture.some_headers_are_set(fixture.headers) )

    @test(WebFixture)
    def web_session_handling(self, fixture):
        """The core web framework (this egg) does not implement a notion of session directly.
           It relies on such a notion, but expects an implementation for this to be supplied.

           An implementation should implement the WebUserSessionProtocol. The implementation
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
        stubclass(WebUserSessionProtocol)
        class WebUserSessionStub(WebUserSessionProtocol):
            session = None
            last_activity_time_set = False
            key_is_set = False
            @classmethod
            def get_or_create_session(cls):
                cls.session = cls()
                return cls.session

            def set_session_key(self, response):
                self.key_is_set = True
                self.saved_response = response

            def is_secure(self): pass
            def is_logged_in(self): pass
            def set_as_logged_in(self, party, stay_logged_in): pass
            def log_out(self): pass

            def set_last_activity_time(self): 
                self.last_activity_time_set = True

            def get_interface_locale(self):
                return 'en_gb'

        # Setting the implementation in config
        fixture.config.web.session_class = WebUserSessionStub

        with CallMonitor(fixture.system_control.orm_control.commit) as monitor:
            @stubclass(Resource)
            class ResourceStub(object):
                def handle_request(self, request):
                    context = WebExecutionContext.get_context()
                    vassert( context.session is WebUserSessionStub.session )  # By the time user code executes, the session is set
                    vassert( monitor.times_called == 1 )                      # The database has been committed
                    vassert( not context.session.last_activity_time_set )     
                    vassert( not WebUserSessionStub.session.key_is_set )
                    return Response()
        
            @stubclass(ReahlWSGIApplication)
            class ReahlWSGIApplicationStub2(ReahlWSGIApplicationStub):
                def resource_for(self, request):
                    return ResourceStub()

            browser = Browser(ReahlWSGIApplicationStub2(fixture.config))

            # A session is obtained, and the correct params passed to the hook methods
            vassert( not WebUserSessionStub.session )      # Before the request, the session is not yet set
            vassert( monitor.times_called == 0 )           # ... and the database is not yet committed
            browser.open('/')
            
            vassert( monitor.times_called == 1 )           # The database is committed after user code executed
            vassert( WebUserSessionStub.session )          # The session was set
            vassert( WebUserSessionStub.session.key_is_set ) # The set_session_key was called
            vassert( WebUserSessionStub.session.saved_response.status_int is 200 ) # The correct response was passed to set_session_key

            vassert( WebUserSessionStub.session.last_activity_time_set ) # set_last_activity_time was called

    @test(WebFixture)
    def handling_HTTPError_exceptions(self, fixture):
        """If an HTTPError exception is raised, it is used ad response."""
        @stubclass(ReahlWSGIApplication)
        class ReahlWSGIApplicationStub2(ReahlWSGIApplicationStub):
            def resource_for(self, request):
                raise HTTPNotFound()

        browser = Browser(ReahlWSGIApplicationStub2(fixture.config))

        browser.open('/', status=404)
