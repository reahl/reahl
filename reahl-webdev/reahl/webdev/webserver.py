# Copyright 2009-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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
from threading import Event
from threading import Thread
import select
from wsgiref import simple_server
import sys
import traceback
import socket
import ssl
from contextlib import contextmanager
import logging
import functools
import pkg_resources

from webob import Request
from webob.exc import HTTPInternalServerError

from reahl.component.exceptions import ProgrammerError
from reahl.component.context import ExecutionContext
from reahl.component.config import StoredConfiguration
from reahl.web.fw import ReahlWSGIApplication

class WrappedApp(object):
    """A class in which to wrap a WSGI app, allowing catching of exceptions in the wrapped app.
    """
    def __init__(self, wrapped):
        self.wrapped = wrapped
        self.exception = None
        self.traceback = None

    def __call__(self, environ, start_response):
        app = self.wrapped
        
        request = Request(environ, charset='utf-8')
        
        self.exception = None
        self.traceback = None
        try:
            to_return = b''
            for i in app(environ, start_response):
                to_return += i 
        except socket.error:
            to_return = b''
            for i in HTTPInternalServerError(charset='utf-8')(environ, start_response):
                to_return += i
        except:
            to_return = b''
            (_, self.exception, self.traceback) = sys.exc_info()
            traceback_html = six.text_type(traceback.format_exc(self.traceback))
            for i in HTTPInternalServerError(content_type=b'text/plain', charset=b'utf-8', unicode_body=traceback_html)(environ, start_response):
                to_return += i
        yield to_return

    def set_new_wrapped(self, new_wsgi_app):
        self.wrapped = new_wsgi_app

    def __getattr__(self, name):
        return getattr(self.wrapped, name)

    def has_uncaught_exception(self):
        return self.exception is not None

    def report_exception(self):
        if self.exception:
            six.reraise(self.exception.__class__, self.exception, self.traceback)
            
    def clear_exception(self):
        self.exception = None


class NoopApp(object):
    def __init__(self, config=None):
        pass
    def start(self): pass
    def stop(self): pass
    def __call__(self, environ, start_response):
        status = '200 OK'
        response_headers = [('Content-type','text/plain')]
        start_response(status, response_headers)
        return ['']
    def report_exception(self, *args, **kwargs):
        pass
    def clear_exception(self):
        pass


class LoggingRequestHandler(simple_server.WSGIRequestHandler):
    def log_message(self, format, *args):
        message = format % args
        logging.getLogger(__name__).info(message)

    def setup(self):
        simple_server.WSGIRequestHandler.setup(self)
        # The server will get here if requests_waiting() returned True.
        # In some cases (ref: chrome prefetching/preconnecting) requests_waiting() will return True,
        #   but there really is nothing to read on the socket, and our server will block here.
        # All this timeout stuff justs safeguards against that eventuality - which is a hard thing
        #   to debug if it happens.
        self.rfile._sock.settimeout(3)  

    def handle(self):
        try:
            simple_server.WSGIRequestHandler.handle(self)
        except socket.timeout:
            message = 'Server socket timed out waiting to receive the request. This may happen if the server mistakenly deduced that there were requests waiting for it when there were not. Such as when chrome prefetches things, etc.'
            logging.getLogger(__name__).warn(message)

    def finish_response(self):
        try:
            simple_server.WSGIRequestHandler.finish_response()
        except socket.error as ex:
            import pdb; pdb.set_trace()


class SSLWSGIRequestHandler(LoggingRequestHandler):
    def get_environ(self):
        env = simple_server.WSGIRequestHandler.get_environ(self)
        env['HTTPS']='on'
        return env


class ReahlWSGIServer(simple_server.WSGIServer):
    @classmethod
    def make_server(cls, host, port, reahl_wsgi_app):
        httpd = simple_server.make_server(host, port, reahl_wsgi_app, server_class=cls, 
                                          handler_class=LoggingRequestHandler)
        return httpd

    def __init__(self, server_address, RequestHandlerClass):
        simple_server.WSGIServer.__init__(self, server_address, RequestHandlerClass)
        self.allow_reuse_address = True
        
    def serve_async(self):
        if self.requests_waiting(0.01):
            self.handle_waiting_request()

    def handle_waiting_request(self):
        self.handle_request()
        try:
            self.get_app().report_exception()
        finally:
            self.get_app().clear_exception()
    
    def requests_waiting(self, timeout):
        i, o, w = select.select([self.socket],[],[],timeout)
        return i


class SSLCapableWSGIServer(ReahlWSGIServer):
    @classmethod
    def make_server(cls, host, port, certfile, reahl_wsgi_app):
        cls.certfile = certfile
        httpd = simple_server.make_server(host, port, reahl_wsgi_app, server_class=cls, 
                                          handler_class=SSLWSGIRequestHandler)
        return httpd

    def __init__(self, server_address, RequestHandlerClass):
        ReahlWSGIServer.__init__(self, server_address, RequestHandlerClass)
        self.socket = ssl.wrap_socket(self.socket, certfile=self.certfile)
        
    def get_request(self):
        #This method is shamelessly copied from WerkZeug (and changed)
        class _SSLConnectionFix(object):
            #This class is shamelessly copied from WerkZeug
            """Wrapper around SSL connection to provide a working makefile()."""

            def __init__(self, con):
                self._con = con

            def makefile(self, mode, bufsize):
                return socket._fileobject(self._con, mode, bufsize)

            def __getattr__(self, attrib):
                return getattr(self._con, attrib)

        con, info = self.socket.accept()
        con = _SSLConnectionFix(con)
        return con, info

    def finish_request(self, request, client_address):
        try:
            ReahlWSGIServer.finish_request(self, request, client_address)
        except ssl.SSLError as ex:
            pass

class Handler(object):
    def __init__(self, command_executor):
        self.command_executor = command_executor
        self.original_execute = command_executor.execute
        self.reahl_server = None

    def uninstall(self):
        self.command_executor.execute = self.original_execute

    def reinstall(self):
        assert self.reahl_server, 'A handler can only be reinstalled if it was installed previously'
        self.install(self.reahl_server)

    def install(self, reahl_server):
        self.reahl_server = reahl_server
        def wrapped_execute(command, params):
            results = []
            started = Event()
            def doit():
                try:
                    started.set()
                    r = self.original_execute(command, params)
                    results.append(r)
                except Exception as e:
                    raise
                finally:
                    results.append(None)
            command_thread = Thread(target=doit)
            command_thread.start()
            started.wait()

            self.reahl_server.serve_until(lambda: not command_thread.is_alive())
            command_thread.join(5)
            return results[0]
        self.command_executor.execute = wrapped_execute


class ReahlWebServer(object):
    """A web server for testing purposes. This web server runs both an HTTP and HTTPS server. It can 
       be configured to handle requests in the same thread as the test itself, but it can also be run in a
       separate thread. The ReahlWebServer requires a certificate for use with HTTPS upon startup. A self signed
       certificate has been provided as part of the distribution for convenience.
    
       :param config: The :class:`reahl.component.config.Configuration` instance to use as config for this process.
       :param port: The HTTP port on which the server should be started. The HTTPS port is computed as this number + 363.
    """
    @classmethod
    def fromConfigDirectory(cls, directory, port):
        """Creates a new ReahlWebServer given a port and standard configuration directory for an application.
        
           :param directory: The directory from which configuration will be read.
           :param port: The HTTP port on which the server will be started.
        """
        config = StoredConfiguration(directory)
        config.configure()
        return cls(config, port)

    def set_app(self, new_wsgi_app):
        """Changes the currently served application to `new_wsgi_app`."""
        self.reahl_wsgi_app.set_new_wrapped(new_wsgi_app)

    def set_noop_app(self):
        self.set_app(NoopApp())

    def __init__(self, config, port):
        self.in_seperate_thread = None
        self.running = False
        self.handlers = {}
        self.httpd_thread = None
        certfile = pkg_resources.resource_filename(__name__, 'reahl_development_cert.pem')
        self.reahl_wsgi_app = WrappedApp(ReahlWSGIApplication(config))
        try:
            https_port = port+363
            self.httpd = ReahlWSGIServer.make_server('', port, self.reahl_wsgi_app)
            self.httpsd = SSLCapableWSGIServer.make_server('', https_port, certfile, self.reahl_wsgi_app)
        except socket.error as ex:
            message = ('Caught socket.error: %s\nThis means that another process is using one of these ports: %s, %s. ' % (ex, port, https_port)) \
                     +'\nIf this happens while running tests, it probably means that a browser client did not close its side of a connection to a previous server you had running - and that the server socket now sits in TIME_WAIT state. Is there perhaps a browser hanging around from a previous run? I have no idea how to fix this automatically... see http://hea-www.harvard.edu/~fine/Tech/addrinuse.html' \
                      
            raise AssertionError(message)

    def main_loop(self, context):
        with context:
            while self.running:
                self.httpd.serve_async()
                self.httpsd.serve_async()

    def start_thread(self):
        assert not self.running
        self.running = True
        self.httpd_thread = Thread(target=functools.partial(self.main_loop, ExecutionContext.get_context()))
        self.httpd_thread.daemon = True
        self.httpd_thread.start()

    def stop_thread(self, join=True):
        self.running = False
        if self.httpd_thread and join:
            self.httpd_thread.join(5)
            if self.httpd_thread.is_alive():
                raise ProgrammerError('Timed out after 5 seconds waiting for httpd serving thread to end')
        self.httpd_thread = None

    def start(self, in_seperate_thread=True, connect=False):
        """Starts the webserver and web application.
        
           :keyword in_seperate_thread: If False, the server handles requests in the same thread as your tests.
           :keyword connect: If True, also connects to the database.
        """
        self.reahl_wsgi_app.start(connect=connect)
        if in_seperate_thread:
            self.start_thread()
        self.in_seperate_thread = in_seperate_thread

    def stop(self):
        """Stops the webserver and web application from running."""
        if self.running:
            self.stop_thread()
        self.reahl_wsgi_app.stop()
        self.shutdown_socket(self.httpd.socket)
        self.shutdown_socket(self.httpsd.socket)
    
    def shutdown_socket(self, socket_to_shutdown):
        """ On windows, the shutdown of a socket does not work as we expect.
            http://stackoverflow.com/questions/409783/socket-shutdown-vs-socket-close
            This method tries the shutdown, and if it cannot, tries to close it.
        """
        try:
            socket_to_shutdown.shutdown(socket.SHUT_RDWR)
        except socket.error as e:
            if e.errno == 10057:
                socket_to_shutdown.close();
            else:
                raise
            
    def requests_waiting(self, timeout):
        return self.httpd.requests_waiting(timeout) or self.httpsd.requests_waiting(timeout/10)

    def serve_until(self, done):
        while not (done() or self.reahl_wsgi_app.has_uncaught_exception()):
            self.httpd.serve_async()
            self.httpsd.serve_async()

    def serve(self, timeout=0.01):
        """Call this method once to have the server handle all waiting requests in the calling thread."""
        def done():
            return not self.requests_waiting(timeout)
        self.serve_until(done)

    def install_handler(self, web_driver):
        """Installs this server's request handler into the given `web_driver`. This enables the
           server to serve requests from the web_driver in the current thread."""
        assert web_driver not in self.handlers.keys(), 'Handler already installed into %s' % web_driver
        new_handler = Handler(web_driver.command_executor)
        self.handlers[web_driver] = new_handler
        new_handler.install(self)

    def restore_handlers(self):
        for handler in self.handlers.values():
            handler.uninstall()

    def reinstall_handlers(self):
        for handler in self.handlers.values():
            handler.reinstall()

    @contextmanager
    def in_background(self, wait_till_done_serving=True):
        """Returns a context manager. Within the context of this context manager, the webserver is temporarily run
           in a separate thread. After the context managed by this context manager is exited, the server reverts to 
           handling requests in the current (test) thread.

           :keyword wait_till_done_serving: If True, wait for the server to finish its background job before exiting the context block.
        """
        self.restore_handlers()
        self.start_thread()
        try:
            yield
        finally:
            try:
                self.stop_thread(join=wait_till_done_serving)
            finally:
                self.reinstall_handlers()



