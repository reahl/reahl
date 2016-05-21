# Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from __future__ import print_function, unicode_literals, absolute_import, division
import os

from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from reahl.tofu import set_up
from reahl.tofu import tear_down

from reahl.dev.fixtures import CleanDatabase

from reahl.webdev.webserver import ReahlWebServer
from reahl.web.egg import WebConfig
from reahl.web.fw import UserInterface
from reahl.webdeclarative.webdeclarative import UserSession, PersistedException, PersistedFile, UserInput
from reahl.domain.systemaccountmodel import SystemAccountConfig


class BrowserSetup(CleanDatabase):
    """A Fixture to be used as run fixture. It inherits from :class:`reahl.dev.fixtures.CleanDatabase` and
       hence includes all its functionality, but adds a running, configured web server and more than one
       flavour of a `Selenium 2.x WebDriver <http://docs.seleniumhq.org/projects/webdriver/>`_. BrowserSetup
       also stops all the necessary servers upon tear down.
       
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
          
       .. data:: config
       
          A :class:`reahl.component.config.Configuration` class used for the test process
          and web server.
          
    """
    def new_reahl_server(self):
        server = ReahlWebServer(self.config, 8000)
#        with self.context:
#            server.start(in_separate_thread=False)
        return server

    @property 
    def web_driver(self):
        return self.chrome_driver

    def new_firefox_driver(self, javascript_enabled=True):
        assert javascript_enabled, 'Cannot disable javascript anymore, see: https://github.com/seleniumhq/selenium/issues/635'
        from selenium.webdriver import FirefoxProfile, DesiredCapabilities

        fp = FirefoxProfile()
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

    def new_chrome_driver(self):
        from selenium.webdriver.chrome.options import Options
        options = Options()
        options.add_argument('--disable-preconnect')
        options.add_argument('--dns-prefetch-disable')
        #--enable-http-pipelining
        #--learning
        #--single-process
        try:
            wd = webdriver.Chrome(chrome_options=options)
        except WebDriverException as ex:
            if ex.msg.startswith('Unable to either launch or connect to Chrome'):
                ex.msg += '  *****NOTE****: On linux, chrome needs write access to /dev/shm.'
                ex.msg += ' This is often not the case when you are running inside a *chroot*.'
                ex.msg += ' To fix, add the following line in the chroot\'s /etc/fstab: '
                ex.msg += ' "tmpfs /dev/shm tmpfs rw,noexec,nosuid,nodev 0 0" '
                ex.msg += ' .... and then run sudo mount /dev/shm '
                ex.msg += '\n\n ***ALTERNATIVE*** An alternative solution (when using schroot) is'
                ex.msg += ' to make sure that /etc/schroot/mount.defaults contain a line for /run/shm.'
                ex.msg += ' (usually it is commented out)'
            raise
        self.reahl_server.install_handler(wd)
        return wd

    def set_noop_app(self):
        # selenium.stop() hits the application its opened on again. NoopApp just ensures this does not break:
        class NoopApp(object):
            def __call__(self, environ, start_response):
                status = '200 OK'
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
        with self.context:
            # Create and start server
            self.reahl_server.start(in_separate_thread=False, connect=False)

    def restart_session(self, web_driver):
        web_driver.close()
        web_driver.start_session(web_driver.desired_capabilities)

    def is_instantiated(self, name):
        return name in self.__dict__

    @tear_down
    def stop_servers(self):
        if self.is_instantiated('reahl_server'):
            self.reahl_server.set_noop_app() # selenium.stop() hits the application its opened on again.
            self.reahl_server.restore_handlers()
        if self.is_instantiated('firefox_driver'):
            self.firefox_driver.quit()
        if self.is_instantiated('chrome_driver'):
            self.chrome_driver.quit()
        if self.is_instantiated('reahl_server'):
            self.reahl_server.stop()

    def new_test_dependencies(self):
        return ['reahl-web-declarative']

    def new_config(self):
        config = super(BrowserSetup, self).new_config()
        # These are dependencies we inject or that are only test dependencies and therfore not read
        config.web = WebConfig()
        config.web.site_root = UserInterface
        config.web.static_root = os.getcwd()
        config.web.session_class = UserSession
        config.web.persisted_exception_class = PersistedException
        config.web.persisted_userinput_class = UserInput
        config.web.persisted_file_class = PersistedFile

        config.accounts = SystemAccountConfig()
        config.accounts.admin_email = 'admin@example.org'
        
        return config
