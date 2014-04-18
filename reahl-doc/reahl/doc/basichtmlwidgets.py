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


from reahl.web.fw import UserInterface
from reahl.web.ui import TwoColumnPage, Panel, P


class BasicHTMLWidgetsUI(UserInterface):
    def assemble(self):
        self.define_page(TwoColumnPage, style=u'basic')  

        home = self.define_view(u'/', title=u'Basic HTML Widgets demo')
        home.set_slot(u'main', WidgetPanel.factory())


class WidgetPanel(Panel):
    def __init__(self, view):
        super(WidgetPanel, self).__init__(view)
        self.add_child(P(view, text=u'A paragraph'))

