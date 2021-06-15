# Copyright 2013-2021 Reahl Software Services (Pty) Ltd. All rights reserved.
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



from reahl.tofu.pytestsupport import with_fixtures

from reahl.component.i18n import Catalogue
from reahl.web.fw import UserInterface, IdentityDictionary, Bookmark
from reahl.web.ui import HTML5Page
from reahl.browsertools.browsertools import Browser

from reahl.web_dev.fixtures import WebFixture


@with_fixtures(WebFixture)
def test_i18n_urls(web_fixture):
    """The current locale is determined by reading the first segment of the path. If the locale is not present in the
    path, web.default_url_locale is used."""
    _ = Catalogue('reahl-web')

    class I18nUI(UserInterface):
        def assemble(self):
            view = self.define_view('/aview', title=_('A View'))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page)
            self.define_user_interface('/a_ui',  I18nUI,  IdentityDictionary(), name='test_ui')

    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    browser.open('/a_ui/aview')
    assert browser.title == 'A View'

    browser.open('/af/a_ui/aview')
    assert browser.title == '\'n Oogpunt'

    web_fixture.config.web.default_url_locale = 'af'
    browser.open('/a_ui/aview')
    assert browser.title == '\'n Oogpunt'

    browser.open('/en_gb/a_ui/aview')
    assert browser.title == 'A View'


@with_fixtures(WebFixture)
def test_bookmarks(web_fixture):
    """Bookmarks normally refer to the current locale. You can override that to be a specified locale instead.
    """


    bookmark = Bookmark('/base_path', '/relative_path', 'description')
    af_bookmark = Bookmark('/base_path', '/relative_path', 'description', locale='af')

    assert af_bookmark.locale == 'af'
    assert af_bookmark.href.path == '/af/base_path/relative_path'

    assert bookmark.locale is None
    assert bookmark.href.path == '/base_path/relative_path'
