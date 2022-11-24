# Copyright 2018-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from reahl.web.fw import UserInterface, Widget, Url
from reahl.web.layout import PageLayout
from reahl.web.bootstrap.page import HTML5Page
from reahl.web.bootstrap.ui import A, Alert
from reahl.web.bootstrap.forms import ButtonLayout
from reahl.web.bootstrap.grid import Container, ColumnLayout, ColumnOptions, ResponsiveSize
from reahl.web.libraries import Library


class ThemedUI(UserInterface):
    def assemble(self):
        self.define_page(HTML5Page).use_layout(
            PageLayout(document_layout=Container(),
                      contents_layout=ColumnLayout(ColumnOptions('main', size=ResponsiveSize(lg=6))).with_slots()))
        home = self.define_view('/', title='Themed example')
        home.set_slot('main', SomeWidget.factory())


class SomeWidget(Widget):
    def __init__(self, view):
        super().__init__(view)

        self.add_child(Alert(view, 'This is an alert in danger color', severity='danger'))
        self.add_child(Alert(view, 'This is an alert in primary color', severity='primary'))
        self.add_child(A(view, Url('#'), description='Link styled as button')).use_layout(ButtonLayout(style='primary'))


class CompiledBootstrap(Library):
    def __init__(self):
        super().__init__('custom')
        self.egg_name = 'bootstrapsass'
        self.shipped_in_package = 'dist'
        self.files = [
                      'theme.css',
                      'main.js'
                      ]


class CompiledBootstrap(Library):
    def __init__(self, force_theme=None):
        super().__init__('custom')
        self.force_theme = force_theme
        self.egg_name = 'bootstrapsassmultihomed'
        self.shipped_in_package = 'dist'
        self.files = [
                      'sitea.com.css',
                      'siteb.com.css',
                      'main.js'
                      ]

    def files_of_type(self, extension):
        if extension == '.css':
            from reahl.web.fw import Url
            hostname = self.force_theme or Url.get_current_url().hostname
            return ['%s.css' % hostname]
        else:
            return super().files_of_type(extension)
