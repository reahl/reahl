
# Copyright 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
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

import pkg_resources

from reahl.tofu import test
from reahl.tofu import temp_dir
from reahl.tofu import temp_file_with
from reahl.tofu import vassert
from reahl.stubble import easter_egg, stubclass

from reahl.web.fw import ReahlWSGIApplication, UserInterface
from reahl.web.ui import HTML5Page
from reahl.web.libraries import Library
from reahl.web.egg import WebConfig
from reahl.component.config import Configuration, ReahlSystemConfig
from reahl.sqlalchemysupport import SqlAlchemyControl
from reahl.webdev.tools import Browser
from reahl.web_dev.fixtures import WebFixture


class LibraryFixture(WebFixture):
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
        easter_egg.set_module_path(self.egg_dir.name)

        class MyLibrary(Library):
            def __init__(self):
                super(MyLibrary, self).__init__('mylib')
                self.files = ['somefile.js', 'somefile.css']
                self.shipped_in_directory = '/static_files'
                self.egg_name = easter_egg.project_name

        return MyLibrary

    def new_config(self):
        config = Configuration()
        config.reahlsystem = self.new_reahlsystem()
        config.web = self.new_webconfig()
        config.web.site_root = self.MainUI
        return config

    def new_MainUI(self):
        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(HTML5Page)
                self.define_view('/', title='Home page')
        return MainUI



@test(LibraryFixture)
def configuring_libraries(fixture):
    """Reahl can be configured to expose frontend libraries (libraries of js and css files)."""
    web = fixture.config.web
    vassert( 'mylib' not in web.frontend_libraries )
    web.frontend_libraries.add(fixture.MyLibrary())
    vassert( 'mylib' in web.frontend_libraries )


@test(LibraryFixture)
def library_files(fixture):
    """The files part of configured frontend libraries are (a) added to /static and also (b) included on any page."""
    fixture.config.web.frontend_libraries.clear()
    fixture.config.web.frontend_libraries.add(fixture.MyLibrary())

    browser = Browser(ReahlWSGIApplication(fixture.config))

    browser.open('/static/somefile.js')
    vassert( browser.raw_html == 'contents - js' )

    browser.open('/static/somefile.css')
    vassert( browser.raw_html == 'contents - css' )

    browser.open('/')
    script_added = browser.get_html_for('//script')
    vassert( script_added == '<script type="text/javascript" src="/static/somefile.js"></script>\n' )

    link_added = browser.get_html_for('//link')
    vassert( link_added == '<link rel="stylesheet" href="/static/somefile.css" type="text/css">\n' )

@test(WebFixture)
def standard_reahl_files(fixture):
    """The framework includes certain frontent frameworks by default."""
    wsgi_app = ReahlWSGIApplication(fixture.config)
    browser = Browser(wsgi_app)

    browser.open('/static/html5shiv-printshiv-3.6.3.js')
    vassert( browser.last_response.content_length > 0 )

    browser.open('/static/IE9.js')
    vassert( browser.last_response.content_length > 0 )

    browser.open('/static/reahl.js')
    vassert( browser.last_response.content_length > 0 )

    browser.open('/static/reahl.css')
    vassert( browser.last_response.content_length > 0 )

    browser.open('/static/runningon.png')
    vassert( browser.last_response.content_length > 0 )

