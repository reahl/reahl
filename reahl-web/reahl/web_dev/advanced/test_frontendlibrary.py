# Copyright 2015-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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



import pkg_resources

from reahl.tofu import temp_dir, Fixture, set_up, uses
from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import easter_egg

from reahl.browsertools.browsertools import Browser

from reahl.web.fw import ReahlWSGIApplication, UserInterface
from reahl.web.ui import HTML5Page
from reahl.web.libraries import Library

from reahl.web_dev.fixtures import WebFixture


@uses(web_fixture=WebFixture)
class LibraryFixture(Fixture):

    def new_egg_dir(self):
        egg_dir = temp_dir()
        package_dir = egg_dir.sub_dir('static_files')
        init_file = package_dir.file_with('__init__.py', '')
        js_file = package_dir.file_with('somefile.js', 'contents - js')
        css_file = package_dir.file_with('somefile.css', 'contents - css')
        return egg_dir

    def new_MyLibrary(self):
        easter_egg.clear()
        pkg_resources.working_set.add(easter_egg)
        easter_egg.location = self.egg_dir.name

        class MyLibrary(Library):
            def __init__(self):
                super().__init__('mylib')
                self.files = ['somefile.js', 'somefile.css']
                self.shipped_in_package = 'static_files'
                self.egg_name = easter_egg.project_name

        return MyLibrary

    @set_up
    def configure_site_root(self):
        self.web_fixture.webconfig.site_root = self.MainUI

    def new_MainUI(self):
        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(HTML5Page)
                self.define_view('/', title='Home page')
        return MainUI


@with_fixtures(WebFixture, LibraryFixture)
def test_configuring_libraries(web_fixture, library_fixture):
    """Reahl can be configured to expose frontend libraries (libraries of js and css files)."""

    web = web_fixture.webconfig
    assert 'mylib' not in web.frontend_libraries
    web.frontend_libraries.add(library_fixture.MyLibrary())
    assert 'mylib' in web.frontend_libraries


@with_fixtures(WebFixture, LibraryFixture)
def test_library_files(web_fixture, library_fixture):
    """The files part of configured frontend libraries are (a) added to /static and also (b) included on any page."""

    config = web_fixture.config
    config.web.frontend_libraries.clear()
    config.web.frontend_libraries.add(library_fixture.MyLibrary())

    with easter_egg.active():
        browser = Browser(ReahlWSGIApplication(config))

        browser.open('/static/somefile.js')
        assert browser.raw_html == 'contents - js'

        browser.open('/static/somefile.css')
        assert browser.raw_html == 'contents - css'

        browser.open('/')
        script_added = browser.get_html_for('//script[@src]')
        assert script_added == '<script type="text/javascript" src="/static/somefile.js"></script>'

        link_added = browser.get_html_for('//link')
        assert link_added == '<link rel="stylesheet" href="/static/somefile.css" type="text/css">'


@with_fixtures(WebFixture)
def test_standard_reahl_files(web_fixture):
    """The framework includes certain frontent frameworks by default."""

    config = web_fixture.config
    wsgi_app = ReahlWSGIApplication(config)
    browser = Browser(wsgi_app)

    browser.open('/static/html5shiv-printshiv-3.7.3.js')
    assert browser.last_response.content_length > 0

    browser.open('/static/IE9.js')
    assert browser.last_response.content_length > 0

    browser.open('/static/reahl.validate.js')
    assert browser.last_response.content_length > 0

    browser.open('/static/reahl.css')
    assert browser.last_response.content_length > 0

    browser.open('/static/runningon.png')
    assert browser.last_response.content_length > 0

    browser.open('/static/reahl.runningonbadge.css')
    assert browser.last_response.content_length > 0
