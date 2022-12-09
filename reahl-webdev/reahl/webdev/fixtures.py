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

# Copyright (C) 2006 Reahl Software Services (Pty) Ltd.  All rights reserved. (www.reahl.org)


from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from reahl.tofu import Fixture, set_up, tear_down, scope, uses

from reahl.component.shelltools import Executable
from reahl.webdev.webserver import ReahlWebServer


from reahl.dev.fixtures import ReahlSystemSessionFixture

@uses(reahl_system_fixture=ReahlSystemSessionFixture)
@scope('session')
class WebServerFixture(Fixture):
    """A Fixture to be used as session fixture.
       It sets up a running, configured web server before any test runs, and more than one
       flavour of a `Selenium 2.x WebDriver <http://docs.seleniumhq.org/projects/webdriver/>`_.
       WebServerFixture also stops all the necessary servers upon tear down.

       The web server started runs in the same thread as your tests, making debugging easier.

       .. data:: reahl_server

          The :class:`reahl.webdev.webserver.ReahlWebServer` for this test process.

       .. data:: firefox_driver

          A WebDriver instance set up to work with the running `reahl_server`, via Firefox.

       .. data:: chrome_driver

          A WebDriver instance set up to work with the running `reahl_server`, via Chrome.
          Note that this expects a Chrome binary to be present at /usr/lib/chromium-browser/chromium-browser

       .. data:: web_driver

          The default WebDriver instance (Chrome, by default).

    """

    def new_reahl_server(self):
        return ReahlWebServer(self.reahl_system_fixture.config)

    @property
    def web_driver(self):
#        return self.chrome_driver
#        return self.phantomjs_driver
        return self.firefox_driver

    def new_phantomjs_driver(self):
        driver = webdriver.PhantomJS() # or add to your PATH
        driver.set_window_size(1024, 768) # optional
        self.reahl_server.install_handler(driver)
        return driver

    def quit_drivers(self):
        for driver_name in ['firefox_driver', 'chrome_driver']:
            if self.is_instantiated(driver_name):
                driver = getattr(self, driver_name)
                delattr(self, driver_name)
                driver.quit()

    def new_firefox_driver(self, javascript_enabled=True):
        assert javascript_enabled, 'Cannot disable javascript anymore, see: https://github.com/seleniumhq/selenium/issues/635'
        from selenium.webdriver import FirefoxProfile, DesiredCapabilities

        # FF does not fire events when its window is not in focus.
        # Native events used to fix this.
        # After FF34 FF does not support native events anymore

        fp = FirefoxProfile()
##        fp.set_preference("focusmanager.testmode", False)
##        fp.set_preference('plugins.testmode', False)
#        fp.set_preference('webdriver_enable_native_events', True)
#        fp.set_preference('webdriver.enable.native.events', True)
#        fp.set_preference('enable.native.events', True)
#        fp.native_events_enabled = True

        fp.set_preference('webdriver.log.file', '/tmp/firefox.webdriver.log')
        fp.set_preference('webdriver.firefox.logfile', '/tmp/firefox.log')
        fp.set_preference('network.http.max-connections-per-server', 1)
        fp.set_preference('network.http.max-persistent-connections-per-server', 0)
        fp.set_preference('network.http.spdy.enabled', False)
        fp.set_preference('network.http.pipelining', True)
        fp.set_preference('network.http.pipelining.maxrequests', 8)
        fp.set_preference('network.http.pipelining.ssl', True)
        fp.set_preference('html5.offmainthread', False)

        dc = DesiredCapabilities.FIREFOX.copy()

        if not javascript_enabled:
            fp.set_preference('javascript.enabled', False)
            dc['javascriptEnabled'] = False

        wd = webdriver.Firefox(firefox_profile=fp, capabilities=dc)
        self.reahl_server.install_handler(wd)
        return wd


    def new_chrome_options(self):
        from selenium.webdriver.chrome.options import Options
        options = Options()
        options.add_argument('--disable-preconnect')
        options.add_argument('--dns-prefetch-disable')
#        options.add_argument('--start-maximized')  # This breaks xpra pair programming currently.
        options.add_argument('--no-sandbox')  # Needed to be able to run a user-installed version of chromium on travis
        options.binary_location = Executable('chromium-browser').executable_file  # To run a custom-installed chromium as picked up by the PATH
        #--enable-http-pipelining
        #--learning
        #--single-process
        return options

    def new_chrome_driver(self):
        try:
            wd = webdriver.Chrome(chrome_options=self.chrome_options) #, service_args=["--verbose", "--log-path=/tmp/chromedriver.log"]
        except WebDriverException as ex:
            if ex.msg.startswith('Unable to either launch or connect to Chrome'):
                ex.msg += '  *****NOTE****: On linux, chrome needs write access to /dev/shm.'
                ex.msg += ' This is often not the case when you are running inside a *chroot*.'
                ex.msg += ' To fix, add the following line in the chroot\'s /etc/fstab: '
                ex.msg += ' "tmpfs /dev/shm tmpfs rw,noexec,nosuid,nodev 0 0" '
                ex.msg += ' .... and then run sudo mount /dev/shm '
                ex.msg += '\n\n ***ALTERNATIVE*** An alternative solution (when using schroot) is'
                ex.msg += ' to make sure that /etc/schroot/default/fstab contain a line for /dev/shm.'
                ex.msg += ' (usually it is commented out)'
            raise
        self.reahl_server.install_handler(wd)
        return wd

    def restart_chrome_session(self):
        self.chrome_driver.close()
        self.chrome_driver.start_session(self.chrome_options.to_capabilities())


    def set_noop_app(self):
        # selenium.stop() hits the application its opened on again. NoopApp just ensures this does not break:
        class NoopApp:
            def __call__(self, environ, start_response):
                status = '403 Forbidden'
                response_headers = [('Content-type','text/plain')]
                start_response(status, response_headers)
                return ['']
            def report_exception(self, *args, **kwargs):
                pass
        self.reahl_server.httpd.set_app(NoopApp())
        self.reahl_server.httpsd.set_app(NoopApp())

    @set_up
    def start_servers(self):
        self.reahl_server.start(in_separate_thread=False)

    def is_instantiated(self, name):
        return name in self.__dict__

    @tear_down
    def stop_servers(self):
        if self.is_instantiated('reahl_server'):
            self.reahl_server.set_noop_app() # selenium.stop() hits the application its opened on again.
        self.quit_drivers()
        if self.is_instantiated('reahl_server'):
            self.reahl_server.restore_handlers()
            self.reahl_server.stop()

    def new_test_dependencies(self):
        return ['reahl-web-declarative']

