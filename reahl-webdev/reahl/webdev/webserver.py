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


import os
import time
import subprocess
import atexit
from threading import Event, Thread
import select
from wsgiref import simple_server
import sys
import traceback
import socket
import ssl
import contextlib
import logging
import functools
import pkg_resources

from http.client import CannotSendRequest

from webob import Request
from webob.exc import HTTPInternalServerError

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from reahl.component.exceptions import ProgrammerError
from reahl.component.context import ExecutionContext, NoContextFound
from reahl.component.config import StoredConfiguration
from reahl.component.shelltools import Executable
from reahl.component.decorators import deprecated
from reahl.web.fw import ReahlWSGIApplication


class WrappedApp:
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
                try:
                  to_return += i 
                except:
                    import pdb; pdb.set_trace()
        except:
            to_return = b''
            (_, self.exception, self.traceback) = sys.exc_info()
            traceback_html = str(traceback.format_exc())
            for i in HTTPInternalServerError(content_type='text/plain', charset='utf-8', unicode_body=traceback_html)(environ, start_response):
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
            raise self.exception.with_traceback(self.traceback)

    def clear_exception(self):
        self.exception = None


class NoopApp:
    def __init__(self, config=None):
        pass
    def start(self): pass
    def stop(self): pass
    def __call__(self, environ, start_response):
        status = '200 OK'
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        return [''.encode('utf-8')]
    def report_exception(self, *args, **kwargs):
        pass
    def clear_exception(self):
        pass

from wsgiref.simple_server import ServerHandler

class PatchedServerHandler(ServerHandler):
    # We modify simple_server.ServerHandler to work around some
    # problems experienced with it.
    def finish_response(self):
        # If the browser closes the connection while we still want to sen stuff back,
        # we want to fail silently and give up. This often happens in tests where the
        # browser may want to request embedded links (like stylesheets) too, yet the
        # test has already clicked on the next link.
        ssl_eof_error = ssl.SSLEOFError
        broken_pipe_error = BrokenPipeError
            
        try:
            ServerHandler.finish_response(self)
        except (ssl_eof_error,  broken_pipe_error):
            # Silently ignore it if it looks like the client browser closed the connection.
            pass


class SingleWSGIRequestHandler(simple_server.WSGIRequestHandler):
    # We modify simple_server.WSGIRequestHandler slightly to work around some
    # problems experienced with it.
    def handle(self):
        # A modified copy of simple_server.WSGIRequestHandler.handle
        #
        # We first check if there really IS something to read on the socket
        # because as soon as ReahlWSGIServer.connection_is_pending becomes
        # true, A SingleWSGIRequestHandler is created already. However, the
        # fact that the browser made a connection does not mean it has sent
        # HTTP requests yet. So, we cannot really serve yet.
        #
        # We first check whether something has actually arrived here by
        # temporarily setting a timeout on the socket to read the first byte.
        # We suspect that the browser connects eagerly (pre-connect) before it
        # has a request to send in order to gain a speed benefit. 
        #
        # We also use this override to use our PatchedServerHandler instead of
        # ServerHandler to handle HTTP requests.
        try:
            self.request.settimeout(0.1)
            self.raw_requestline = self.rfile.read(1)
        except (socket.timeout, ssl.SSLError):
            return
        finally:
            self.request.settimeout(None)

        self.raw_requestline = self.raw_requestline + self.rfile.readline(65536)
        if len(self.raw_requestline) > 65536:
            self.requestline = ''
            self.request_version = ''
            self.command = ''
            self.send_error(414)
            return

        if not self.parse_request(): # An error code has been sent, just exit
            return

        handler = PatchedServerHandler(
            self.rfile, self.wfile, self.get_stderr(), self.get_environ()
        )
        handler.request_handler = self      # backpointer for logging
        handler.run(self.server.get_app())

    def log_message(self, message_format, *args):
        message = message_format % args
        logging.getLogger(__name__).info(message)




class ReahlWSGIServer(simple_server.WSGIServer):
    @classmethod
    def make_server(cls, host, port, reahl_wsgi_app):
        httpd = simple_server.make_server(host, port, reahl_wsgi_app, server_class=cls, 
                                          handler_class=SingleWSGIRequestHandler)
        return httpd

    def __init__(self, server_address, RequestHandlerClass):
        simple_server.WSGIServer.__init__(self, server_address, RequestHandlerClass)
        self.allow_reuse_address = True
        
    def serve_async(self, in_separate_thread=False):
        if self.connection_is_pending(0.01):
            self.handle_waiting_request(in_separate_thread)

    def handle_waiting_request(self, in_separate_thread):
        self.in_separate_thread = in_separate_thread
        self.handle_request()
        try:
            self.get_app().report_exception()
        finally:
            self.get_app().clear_exception()
    
    def connection_is_pending(self, timeout):
        i, o, w = select.select([self],[],[],timeout)
        return i

    def handle_error(self, request, client_address):
        exc_type, exc, tb = sys.exc_info()
        if isinstance(exc, socket.error) and exc.errno == 32:
            # PY2: Silently ignore it if it looks like the client browser closed the socket.
            pass
        else:
            simple_server.WSGIServer.handle_error(self, request, client_address)
                


class SSLCapableWSGIServer(ReahlWSGIServer):
    @classmethod
    def make_server(cls, host, port, certfile, reahl_wsgi_app):
        cls.certfile = certfile
        httpd = simple_server.make_server(host, port, reahl_wsgi_app, server_class=cls, 
                                          handler_class=SingleWSGIRequestHandler)
        return httpd

    def setup_environ(self):
        ReahlWSGIServer.setup_environ(self)
        self.base_environ['HTTPS']='on'

    def server_bind(self):
        self.socket = ssl.wrap_socket(self.socket, server_side=True, certfile=self.certfile)
        super().server_bind()



class WebDriverHandler:
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
            exceptions=[]
            results = []
            started = Event()
            def doit():
                try:
                    started.set()
                    try:
                        r = self.original_execute(command, params)
                    except CannotSendRequest:
                        # Retry in case the keep-alive connection state got mixed up
                        # by, eg, the browser requesting a new url before all the
                        # styleseets etc have loaded on the current one.
                        r = self.original_execute(command, params)
                    results.append(r)
                except Exception as e:
                    exceptions.append(e)
                    raise
                finally:
                    results.append(None)
            command_thread = Thread(target=doit)
            command_thread.start()
            started.wait()

            self.reahl_server.serve_until(lambda: not command_thread.is_alive() and not self.reahl_server.connection_is_pending(0.01))
            if exceptions:
                raise Exception(exceptions[0])
            command_thread.join(5)
            return results[0]
        self.command_executor.execute = wrapped_execute


class Py2TimeoutExpired(Exception):
    pass

class SlaveProcess:
    def __init__(self, command, args):
        self.process = None
        self.args = args
        self.executable = Executable(command)

    def terminate(self, timeout=5):
        logging.getLogger(__name__).debug('Terminating process with PID[%s]' % self.process.pid)
        self.process.terminate()
        self.wait_to_die(timeout=timeout)

    def wait_to_die(self, timeout):
        try:
            self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.process.kill()

    def spawn_new_process(self):
        return self.executable.Popen(self.args, env=os.environ.copy())

    def is_running(self):
        return self.process.poll() is None

    def start(self):
        self.process = self.spawn_new_process()
        self.register_orphan_killer(self.create_orphan_killer(self.process))
        logging.getLogger(__name__).debug('Starting process with PID[%s]' % self.process.pid)

    def create_orphan_killer(self, process):
        def kill_orphan_on_exit(possible_orphan_process):
            logging.getLogger(__name__).debug('Cleanup: ensuring process with PID[%s] has terminated' % possible_orphan_process.pid)
            try:
                possible_orphan_process.kill()
                logging.getLogger(__name__).debug('Had to kill process(orphan) with PID[%s]' % possible_orphan_process.pid)
            except (ProcessLookupError):
                logging.getLogger(__name__).debug('Process with PID[%s] seems terminated already, no need to kill it' % possible_orphan_process.pid)
        return functools.partial(kill_orphan_on_exit, process)

    def register_orphan_killer(self, kill_function):
        atexit.register(kill_function)

    def restart(self):
        self.terminate()
        self.start()


class ServerSupervisor(PatternMatchingEventHandler):
    def __init__(self, slave_process_args, max_seconds_between_restarts, directories_to_monitor=['.']):
        super().__init__(ignore_patterns=['.git', '.floo', '*.pyc', '*.pyo', '*/__pycache__/*', '*.db-*', '*.db'], ignore_directories=True)
        self.serving_process = SlaveProcess(sys.argv[0], slave_process_args)
        self.max_seconds_between_restarts = max_seconds_between_restarts
        self.directories_to_monitor = directories_to_monitor
        self.directory_observers = []
        self.files_changed = Event()
        self.request_stop_running = Event()

    #override for PatternMatchingEventHandler
    def on_any_event(self, event):
        self.files_changed.set()

    def start_observing_directories(self):
        for directory in self.directories_to_monitor:
            directory_observer = Observer()
            directory_observer.schedule(self, directory, recursive=True)
            directory_observer.start()
            self.directory_observers.append(directory_observer)

    def stop_observing_directories(self):
        for directory_observer in self.directory_observers:
            directory_observer.stop()
            directory_observer.join()

    def pause(self):
        time.sleep(self.max_seconds_between_restarts)

    def stop(self):
        self.request_stop_running.set()

    def stop_serving(self):
        if self.serving_process.is_running():
            self.serving_process.terminate()
        self.stop_observing_directories()

    def run(self):
        self.files_changed.clear()
        self.start_observing_directories()
        self.serving_process.start()

        while not self.request_stop_running.is_set():
            try:
                self.pause()
                if self.files_changed.is_set():
                    logging.getLogger(__name__).debug('Changes to filesystem detected, scheduling a restart...')
                    self.files_changed.clear()
                    if self.serving_process.is_running():
                        self.serving_process.restart()
                    else:
                        self.serving_process.start()
            except KeyboardInterrupt:
                self.stop()

        self.stop_serving()


class ReahlWebServer:
    """A web server for testing purposes. This web server runs both an HTTP and HTTPS server. It can 
       be configured to handle requests in the same thread as the test itself, but it can also be run in a
       separate thread. The ReahlWebServer requires a certificate for use with HTTPS upon startup. A self signed
       certificate has been provided as part of the distribution for convenience.
    
       :param config: The :class:`reahl.component.config.Configuration` instance to use as config for this process.
    """
    @classmethod
    def from_config_directory(cls, directory):
        """Creates a new ReahlWebServer given a port and standard configuration directory for an application.
        
           :param directory: The directory from which configuration will be read.

           ..versionchanged:: 5.1
             Removed port keyword argument, port and encrypted port will be set from the config found in the directory argument.

           ..versionchanged:: 5.1
             Renamed from camel case name.

        """
        config = StoredConfiguration(directory)
        config.configure()

        return cls(config)

    @classmethod
    @deprecated('renamed to from_config_directory','5.1')
    def fromConfigDirectory(cls, directory, port):
        return cls.from_config_directory(directory)

    def set_app(self, new_wsgi_app):
        """Changes the currently served application to `new_wsgi_app`."""
        self.reahl_wsgi_app.set_new_wrapped(new_wsgi_app)

    def set_noop_app(self):
        self.set_app(NoopApp())

    def __init__(self, config):
        super().__init__()
        self.in_separate_thread = None
        self.running = False
        self.handlers = {}
        self.httpd_thread = None

        self.port = int(config.web.default_http_port)
        self.encrypted_port = int(config.web.encrypted_http_port)
        certfile = pkg_resources.resource_filename(__name__, 'reahl_development_cert.pem')
        self.reahl_wsgi_app = WrappedApp(ReahlWSGIApplication(config, start_on_first_request=True))
        try:
            self.httpd = ReahlWSGIServer.make_server('', self.port, self.reahl_wsgi_app)
            self.httpsd = SSLCapableWSGIServer.make_server('', self.encrypted_port, certfile, self.reahl_wsgi_app)
        except socket.error as ex:
            message = ('Caught socket.error: %s\nThis means that another process is using one of these ports: %s, %s. ' % (ex, self.port, self.encrypted_port)) \
                     +'\nIf this happens while running tests, it probably means that a browser client did not close its side of a connection to a previous server you had running - and that the server socket now sits in TIME_WAIT state. Is there perhaps a browser hanging around from a previous run? I have no idea how to fix this automatically... see http://hea-www.harvard.edu/~fine/Tech/addrinuse.html'

            raise AssertionError(message)

    def main_loop(self, context=None):

        context = context or contextlib.nullcontext()
        with context:
            while self.running:
                try:
                    self.httpd.serve_async(in_separate_thread=self.in_separate_thread)
                    self.httpsd.serve_async(in_separate_thread=self.in_separate_thread)
                except:
                    # When running as a stand-alone server, we keep the server running, but else break so tests break
                    if self.in_separate_thread and self.running:
                        print(traceback.format_exc(), file=sys.stderr)
                    else:
                        raise

    def start_thread(self):
        assert not self.running
        self.running = True
        try:
            context = ExecutionContext.get_context().copy()
        except NoContextFound:
            context = None
        self.httpd_thread = Thread(target=functools.partial(self.main_loop, context))
        self.httpd_thread.daemon = True
        self.httpd_thread.start()

    def stop_thread(self, join=True):
        self.running = False
        if self.httpd_thread and join:
            self.httpd_thread.join(5)
            if self.httpd_thread.is_alive():
                raise ProgrammerError('Timed out after 5 seconds waiting for httpd serving thread to end')
        self.httpd_thread = None

    def wait_for_server_to_complete(self):
        try:
            self.httpd_thread.join()
        finally:
            self.stop()

    def start(self, in_separate_thread=True):
        """Starts the webserver and web application.
        
           :keyword in_separate_thread: If False, the server handles requests in the same thread as your tests.

           .. versionchanged:: 6.1 
              Removed connect= kwarg - the ReahlWSGIApplication is now responsible for connecting when it is started which it will do if it detects that is not connected
        """
        self.in_separate_thread = in_separate_thread

        if self.in_separate_thread:
            self.start_thread()

    def stop(self):
        """Stops the webserver and web application from running."""
        if self.running:
            self.stop_thread()
        self.reahl_wsgi_app.stop()
        self.httpd.server_close()
        self.httpsd.server_close()

    def connection_is_pending(self, timeout):
        return self.httpd.connection_is_pending(timeout) or self.httpsd.connection_is_pending(timeout/10)

    def serve_until(self, done):
        while not (done() or self.reahl_wsgi_app.has_uncaught_exception()):
            self.httpd.serve_async(in_separate_thread=self.in_separate_thread)
            self.httpsd.serve_async(in_separate_thread=self.in_separate_thread)

    def serve(self, timeout=0.01):
        """Call this method once to have the server handle all waiting requests in the calling thread."""
        def done():
            return not self.connection_is_pending(timeout)
        self.serve_until(done)

    def install_handler(self, web_driver):
        """Installs this server's request handler into the given `web_driver`. This enables the
           server to serve requests from the web_driver in the current thread."""
        assert web_driver not in self.handlers.keys(), 'WebDriverHandler already installed into %s' % web_driver
        new_handler = WebDriverHandler(web_driver.command_executor)
        self.handlers[web_driver] = new_handler
        new_handler.install(self)

    def restore_handlers(self):
        for handler in self.handlers.values():
            handler.uninstall()

    def reinstall_handlers(self):
        for handler in self.handlers.values():
            handler.reinstall()

    @contextlib.contextmanager
    def paused(self, wait_till_done_serving=True):
        self.restore_handlers()
        try:
            yield
        finally:
            try:
                if wait_till_done_serving:
                    self.serve()
            finally:
                self.reinstall_handlers()

    @contextlib.contextmanager
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



