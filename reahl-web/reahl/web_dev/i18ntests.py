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


from nose.tools import istest
from reahl.tofu import Fixture, test
from reahl.tofu import vassert

from reahl.web_dev.fixtures import WebFixture
from reahl.web.fw import Region, IdentityDictionary
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
        view = UrlBoundView(None, current_path, u'Harness view', {})
        return view

@istest
class XXTests(object):
    @test(XXFixture)
    def test(self, fixture):
        from reahl.web.ui import P

        p = P(fixture.view)
        tester = WidgetTester(p)
        rendered_html = tester.render_html()
        vassert( rendered_html == u'<p></p>' )


        
    
@test(WebFixture)
def i18n_urls(fixture):
    """The current locale is determined by reading the first segment of the path. If the locale is not present in the
    path, web.default_url_locale is used."""
    _ = Translator(u'reahl-web')

    class I18nRegion(Region):
        def assemble(self):
            view = self.define_view(u'/aview', title=_(u'A View'))

    class MainRegion(Region):
        def assemble(self):
            self.define_main_window(TwoColumnPage)
            self.define_region(u'/aregion',  I18nRegion,  IdentityDictionary(), name=u'testregion')
            
    webapp = fixture.new_webapp(site_root=MainRegion)
    browser = Browser(webapp)

    browser.open(u'/aregion/aview')
    vassert( browser.title == u'A View' )

    browser.open(u'/af/aregion/aview')
    vassert( browser.title == u'\'n Oogpunt' )

    fixture.context.config.web.default_url_locale = 'af'
    browser.open(u'/aregion/aview')
    vassert( browser.title == u'\'n Oogpunt' )
    
    browser.open(u'/en_gb/aregion/aview')
    vassert( browser.title == u'A View' )
