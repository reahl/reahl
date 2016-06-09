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


from __future__ import print_function, unicode_literals, absolute_import, division
from reahl.web.fw import UserInterface
from reahl.web.ui import HTML5Page, Div, P
from reahl.web.layout import PageLayout
from reahl.web.pure import ColumnLayout


class BasicHTMLWidgetsUI(UserInterface):
    def assemble(self):
        page_layout = PageLayout(contents_layout=ColumnLayout('main').with_slots())
        self.define_page(HTML5Page, style='basic').use_layout(page_layout)

        home = self.define_view('/', title='Basic HTML Widgets demo')
        home.set_slot('main', WidgetPanel.factory())


class WidgetPanel(Div):
    def __init__(self, view):
        super(WidgetPanel, self).__init__(view)
        self.add_child(P(view, text='A paragraph'))

