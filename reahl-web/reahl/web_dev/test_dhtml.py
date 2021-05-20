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


from reahl.tofu import Fixture, set_up, temp_dir
from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import replaced

from reahl.browsertools.browsertools import Browser

from reahl.web.dhtml import DhtmlUI, DHTMLFile
from reahl.web.fw import UserInterface
from reahl.web.ui import HTML5Page

from reahl.web_dev.fixtures import WebFixture, BasicPageLayout
from reahl.component_dev.test_i18n import LocaleContextStub


class DhtmlFixture(Fixture):
    def new_static_dir(self):
        return temp_dir()
    
    div_internals = '<p>some stúff</p>'

    def new_dhtml_file(self):
        charset = 'UTF-8'
        contents = '<!DOCTYPE html><meta charset="%s"><html><head><title>â title</title></head>' \
                   '<body><div id="astatic">%s</div></body></html>' % (charset, self.div_internals)
        return self.static_dir.file_with('correctfile.d.html', contents.encode(charset), mode='w+b')

    def new_afrikaans_dhtml_file(self):
        contents = '<!DOCTYPE html><meta charset="UTF-8"><html><head><title>Afrikaans bo!</title></head><body></body></html>'
        return self.static_dir.file_with('correctfile.af.d.html', contents)

    def new_other_file(self):
        return self.static_dir.file_with('otherfile.txt', 'other')

    def get_inserted_html(self, browser):
        return browser.get_html_for('//div[contains(@class, "column-main")]/*')

    @set_up
    def create_files(self):
        self.dhtml_file
        self.afrikaans_dhtml_file
        self.other_file


@with_fixtures(WebFixture, DhtmlFixture)
def test_basic_workings(web_fixture, dhtml_fixture):
    """A DhtmlUI provides a UserInterface which maps to the filesystem where there may be
       a combination of .d.html and other files. When a d.html file is requested from
       it, the contents of the specified div from inside the d.html file is inserted
       into the specified Slot. When a normal file is requested, the file is sent verbatim."""

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            self.define_user_interface('/dhtml_ui', DhtmlUI, {'main_slot': 'main'},
                            name='test_ui', static_div_name='astatic')

    fixture = dhtml_fixture

    # Dhtml files should be located in the web.static_root
    web_fixture.config.web.static_root = fixture.static_dir.name

    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI, enable_js=True)
    browser = Browser(wsgi_app)

    # A dhtml file: HTML5Page's main_slot now contains the insides of the div in the dhtml file
    browser.open('/dhtml_ui/correctfile.d.html')
    html = fixture.get_inserted_html(browser)
    assert html == fixture.div_internals

    # A non-dhtml file is returned verbatim
    browser.open('/dhtml_ui/otherfile.txt')
    contents = browser.raw_html
    assert contents == 'other'

    # Files that do not exist are reported as such
    browser.open('/dhtml_ui/idonotexist.txt', status=404)
    browser.open('/dhtml_ui/idonotexist.d.html', status=404)


@with_fixtures(WebFixture, DhtmlFixture)
def test_i18n_dhtml(web_fixture, dhtml_fixture):
    """Dhtml files can have i18nsed versions, which would be served up if applicable."""

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            self.define_user_interface('/dhtml_ui', DhtmlUI, {'main_slot': 'main'},
                                       name='test_ui', static_div_name='astatic')

    fixture = dhtml_fixture

    # Dhtml files should be located in the web.static_root
    web_fixture.config.web.static_root = fixture.static_dir.name

    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)

    browser = Browser(wsgi_app)

    # request the file, but get the translated alternative for the locale
    def stubbed_create_context_for_request():
        return LocaleContextStub(locale='af')
    with replaced(wsgi_app.create_context_for_request, stubbed_create_context_for_request):
        browser.open('/dhtml_ui/correctfile.d.html')

    assert browser.title == 'Afrikaans bo!'


@with_fixtures(DhtmlFixture)
def test_encoding_dammit(dhtml_fixture):
    """ """
    dhtml_file = DHTMLFile(dhtml_fixture.dhtml_file.name, ['astatic'])
    dhtml_file.read()
    assert dhtml_file.title == 'â title'
    assert dhtml_file.elements == {'astatic': dhtml_fixture.div_internals}
    assert dhtml_file.original_encoding == 'utf-8'
