# Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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
from nose.tools import istest
from reahl.tofu import Fixture, test
from reahl.tofu import vassert

from reahl.web_dev.fixtures import WebFixture
from reahl.web.fw import UserInterface, IdentityDictionary
from reahl.web.ui import TwoColumnPage
from reahl.webdev.tools import Browser
from reahl.component.i18n import Translator


from reahl.web_dev.fixtures import WebBasicsMixin
from reahl.web.fw import UrlBoundView, Url
from reahl.component.context import ExecutionContext
from reahl.webdev.tools import WidgetTester

class XXFixture(Fixture, WebBasicsMixin):
    def new_view(self):
        current_path = Url(ExecutionContext.get_context().request.url).path
        view = UrlBoundView(None, current_path, 'Harness view', {})
        return view

@istest
class XXTests(object):
    @test(XXFixture)
    def test(self, fixture):
        from reahl.web.ui import P

        p = P(fixture.view)
        tester = WidgetTester(p)
        rendered_html = tester.render_html()
        vassert( rendered_html == '<p></p>' )


        
    
@test(WebFixture)
def i18n_urls(fixture):
    """The current locale is determined by reading the first segment of the path. If the locale is not present in the
    path, web.default_url_locale is used."""
    _ = Translator('reahl-web')

    class I18nUI(UserInterface):
        def assemble(self):
            view = self.define_view('/aview', title=_('A View'))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(TwoColumnPage)
            self.define_user_interface('/a_ui',  I18nUI,  IdentityDictionary(), name='test_ui')
            
    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    browser.open('/a_ui/aview')
    vassert( browser.title == 'A View' )

    browser.open('/af/a_ui/aview')
    vassert( browser.title == '\'n Oogpunt' )

    fixture.context.config.web.default_url_locale = 'af'
    browser.open('/a_ui/aview')
    vassert( browser.title == '\'n Oogpunt' )
    
    browser.open('/en_gb/a_ui/aview')
    vassert( browser.title == 'A View' )
