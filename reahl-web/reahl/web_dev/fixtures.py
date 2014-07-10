# Copyright 2010-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from __future__ import unicode_literals
from __future__ import print_function
import six
import os
from six.moves import http_cookies 

from webob import Request, Response

from reahl.stubble import stubclass
from reahl.tofu import Fixture
from reahl.web.fw import ComposedPage, ReahlWSGIApplication, WebExecutionContext, \
                         UserInterfaceFactory, IdentityDictionary, FactoryDict, UrlBoundView, UserInterface, \
                         WidgetList, Url, Widget, RegexPath
from reahl.web.ui import TwoColumnPage
from reahl.component.i18n import Translator
from reahl.domain_dev.fixtures import PartyModelZooMixin
from reahl.web.egg import WebConfig
from reahl.webelixirimpl import WebUserSession, PersistedException, PersistedFile, UserInput
from reahl.webdev.tools import DriverBrowser


_ = Translator('reahl-webdev')

        
@stubclass(ReahlWSGIApplication)
class ReahlWSGIApplicationStub(ReahlWSGIApplication):
    def add_reahl_static_files(self): # To save time, this is costly...
        pass  

    
class WebBasicsMixin(PartyModelZooMixin):
    def log_in(self, browser=None, session=None, system_account=None, stay_logged_in=False):
        session = session or self.session
        browser = browser or self.driver_browser
        session.set_as_logged_in(system_account or self.system_account, stay_logged_in)
        # quickly create a response so the fw sets the cookies, which we copy and explicitly set on selenium.
        response = Response()
        self.session.set_session_key(response)
        cookies = http_cookies.BaseCookie((', '.join(response.headers.getall('set-cookie'))).encode('utf-8'))
        for name, morsel in cookies.items():
            cookie = {'name':name, 'value':morsel.value}
            cookie.update(dict([(key, value) for key, value in morsel.items() if value]))
            browser.create_cookie(cookie)
    
    def new_driver_browser(self, driver=None):
        driver = driver or self.web_driver
        return DriverBrowser(driver)

    @property
    def chrome_driver(self):
        return self.run_fixture.chrome_driver
    @property
    def firefox_driver(self):
        return self.run_fixture.firefox_driver
    @property
    def web_driver(self):
        return self.run_fixture.web_driver
    @property
    def reahl_server(self):
        return self.run_fixture.reahl_server

    def new_webconfig(self, wsgi_app=None):
        web = WebConfig()
        web.site_root = UserInterface
        web.static_root = os.path.join(os.getcwd(), 'static')
        web.session_class = WebUserSession
        web.persisted_exception_class = PersistedException
        web.persisted_file_class = PersistedFile
        web.persisted_userinput_class = UserInput
        return web

    def new_config(self, reahlsystem=None, accounts=None, web=None):
        config = super(WebBasicsMixin, self).new_config(reahlsystem=reahlsystem, accounts=accounts)
        config.web = web or self.new_webconfig()
        return config
        
    def new_context(self, request=None, config=None, session=None):
        context = WebExecutionContext()
        context.set_config( config or self.config )
        context.set_system_control( self.system_control )
        context.set_request( request or self.request )
        with context:
            context.set_session( session or self.session )
        return context
        
    def new_session(self, system_account=None):
        return WebUserSession(account=system_account)

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

    def new_wsgi_app(self, site_root=None, enable_js=False, 
                         config=None, view_slots=None, child_factory=None):
        wsgi_app_class = ReahlWSGIApplicationStub
        if enable_js:
            wsgi_app_class = ReahlWSGIApplication
        view_slots = view_slots or {}
        child_factory = child_factory or Widget.factory()
        if 'main' not in view_slots:
            view_slots['main'] = child_factory
        config = config or self.config

        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                self.define_view('/', title='Home page', slot_definitions=view_slots)

        site_root = site_root or MainUI
        config.web.site_root = site_root
        return wsgi_app_class(config)

    @property
    def current_location(self):
        return Url(self.driver_browser.get_location())

    def new_view(self):
        current_path = Url(WebExecutionContext.get_context().request.url).path
        view = UrlBoundView(self.user_interface, current_path, 'A view', {})
        return view

    def new_user_interface(self):
        return UserInterface(None, '/', {}, False, 'test_ui')


class WebFixture(Fixture, WebBasicsMixin):
    pass



