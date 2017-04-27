# Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.
#-*- encoding: utf-8 -*-
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
import six
import os
from six.moves import http_cookies 

from webob import Request, Response

from reahl.stubble import stubclass
from reahl.tofu import Fixture, set_up, uses

from reahl.webdev.tools import DriverBrowser
from reahl.webdeclarative.webdeclarative import UserSession, PersistedException, PersistedFile, UserInput

from reahl.domain.systemaccountmodel import LoginSession
from reahl.component.i18n import Translator
from reahl.component.py3compat import ascii_as_bytes_or_str
from reahl.component.context import ExecutionContext
from reahl.web.fw import ReahlWSGIApplication, UrlBoundView, UserInterface, Url, Widget
from reahl.web.ui import HTML5Page, Slot, Div
from reahl.web.layout import Layout
from reahl.web.egg import WebConfig


from reahl.dev.fixtures import ReahlSystemFixture
from reahl.webdev.fixtures import WebServerFixture
from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture
from reahl.domain_dev.fixtures import PartyAccountFixture


_ = Translator('reahl-webdev')

        
@stubclass(ReahlWSGIApplication)
class ReahlWSGIApplicationStub(ReahlWSGIApplication):
    def add_reahl_static_files(self):
        static_files = self.config.web.frontend_libraries.packaged_files()
        static_files_no_js = [packaged_file
                              for packaged_file in static_files if not packaged_file.relative_name.endswith('.js')]
        self.define_static_files('/static', static_files_no_js)


class BasicPageLayout(Layout):
    def __init__(self, slots=['main', 'footer']):
        super(BasicPageLayout, self).__init__()
        self.slots = slots

    def customise_widget(self):
        for slot_name in self.slots:
            slot_div = self.widget.body.add_child(Div(self.view))
            slot_div.append_class('column-%s' % slot_name)
            slot_div.add_child(Slot(self.view, slot_name))


@uses(reahl_system_fixture=ReahlSystemFixture, sql_alchemy_fixture=SqlAlchemyFixture,
      party_account_fixture=PartyAccountFixture, web_server_fixture=WebServerFixture)
class WebFixture(Fixture):

    @set_up
    def add_web_config(self):
        self.reahl_system_fixture.config.web = self.webconfig

    @set_up
    def add_request_to_context(self):
        self.reahl_system_fixture.context.request = self.request

    @property
    def context(self):
        return self.reahl_system_fixture.context

    @property
    def config(self):
        return self.reahl_system_fixture.config
    
    def new_webconfig(self):
        web = WebConfig()
        web.site_root = UserInterface
        web.static_root = os.path.join(os.getcwd(), 'static')
        web.session_class = UserSession
        web.persisted_exception_class = PersistedException
        web.persisted_file_class = PersistedFile
        web.persisted_userinput_class = UserInput
        return web

    def new_request(self, path=None, url_scheme=None):
        request = Request.blank(path or '/', charset='utf8')
        request.environ['wsgi.url_scheme'] = url_scheme or 'http'
        if request.scheme == 'http':
            request.environ['SERVER_PORT'] = '8000'
            request.host = 'localhost:8000'
        else:
            request.environ['SERVER_PORT'] = '8363'
            request.host = 'localhost:8363'
        return Request(request.environ, charset='utf8')

    def log_in(self, browser=None, session=None, system_account=None, stay_logged_in=False):
        session = session or self.party_account_fixture.session
        browser = browser or self.driver_browser
        login_session = LoginSession.for_session(session)
        login_session.set_as_logged_in(system_account or self.party_account_fixture.system_account, stay_logged_in)
        # quickly create a response so the fw sets the cookies, which we copy and explicitly set on selenium.
        response = Response()
        session.set_session_key(response)
        cookies = http_cookies.BaseCookie(ascii_as_bytes_or_str(', '.join(response.headers.getall('set-cookie'))))
        for name, morsel in cookies.items():
            cookie = {'name':name, 'value':morsel.value}
            cookie.update(dict([(key, value) for key, value in morsel.items() if value]))
            browser.create_cookie(cookie)

    def new_driver_browser(self, driver=None):
        driver = driver or self.web_driver
        return DriverBrowser(driver)

    @property
    def chrome_driver(self):
        return self.web_server_fixture.chrome_driver
    @property
    def firefox_driver(self):
        return self.web_server_fixture.firefox_driver
    @property
    def web_driver(self):
        return self.web_server_fixture.web_driver
    @property
    def reahl_server(self):
        return self.web_server_fixture.reahl_server

    def new_wsgi_app(self, site_root=None, enable_js=False, config=None, child_factory=None):
        wsgi_app_class = ReahlWSGIApplicationStub
        if enable_js:
            wsgi_app_class = ReahlWSGIApplication
        child_factory = child_factory or Widget.factory()
        config = config or self.config

        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(HTML5Page).use_layout(BasicPageLayout())
                view = self.define_view('/', title='Home page')
                view.set_slot('main', child_factory)

        site_root = site_root or MainUI
        config.web.site_root = site_root
        return wsgi_app_class(config)

    @property
    def current_location(self):
        return Url(self.driver_browser.get_location())

    def new_view(self):
        current_path = Url(ExecutionContext.get_context().request.url).path
        view = UrlBoundView(self.user_interface, current_path, 'A view')
        return view

    def new_user_interface(self):
        return UserInterface(None, '/', {}, False, 'test_ui')

