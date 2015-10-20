# Copyright 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
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

"""
Widgets and Layouts that provide an abstraction on top of Bootstrap (http://getbootstrap.com/)

.. versionadded:: 3.2

"""
from __future__ import print_function, unicode_literals, absolute_import, division

import six

from reahl.component.modelinterface import exposed, Field
from reahl.web.fw import Widget, Bookmark
from reahl.web.ui import Div
from reahl.web.bootstrap.navs import Nav, TabLayout

"""
1) make MenuItems smarter, so you can say what other stuff to do (attribs, etc) when creating html representation
      MenuItem.from_bookmark(koos).with_class('asd')
2) make Layouts smarter so you can customise them to know about what types of things yu can add
      self.nav.layout.add_type(TabMenuItem)
3) make MenuItems know about their html_representation so we can get to it after the the layout added their html
"""

class TabbedPanel(Widget):
    def __init__(self, view, nav_layout=None):
        super(TabbedPanel, self).__init__(view)
        self.tabs = []
        self.nav = self.add_child(Nav(view).use_layout(nav_layout or TabLayout()))
        self.content_panel = self.add_child(Div(view))
        self.content_panel.append_class('tab-content')

    @exposed
    def query_fields(self, fields):
        fields.tab = Field(required=False, default=None)

    @property
    def active_tab_set(self):
        return self.tab is not None

    def set_active(self, tab):
        self.tab = tab.tab_key

    def is_active(self, tab):
        return self.tab == tab.tab_key

    def add_tab(self, tab):

        if not self.active_tab_set or self.is_active(tab):
            self.set_active(tab)

        self.tabs.append(tab)
        menu_item = self.nav.add_bookmark(tab.get_bookmark(self.view))
        menu_item.a.set_attribute('data-toggle', self.nav.layout.key)
        menu_item.a.set_attribute('data-target', '#%s' % tab.css_id)

        if self.is_active(tab):
            menu_item.set_active()

        self.add_pane_for(tab)
        return tab

    def add_pane_for(self, tab):
        div = self.content_panel.add_child(Div(self.view))
        div.add_child(tab.contents)
        div.append_class('tab-pane')
        div.set_id(tab.css_id)
        if tab.is_active:
            div.append_class('active')
        return div


class Tab(object):
    def __init__(self, title, tab_key, contents):
        self.title = title
        self.tab_key = tab_key
        self.contents = contents
        self.force_active = False

    @property
    def is_active(self):
        return self.force_active

    @property
    def css_id(self):
        return 'tab_%s' % self.tab_key

    def get_bookmark(self, view):
        return view.as_bookmark(description=self.title, query_arguments={'tab': self.tab_key})



