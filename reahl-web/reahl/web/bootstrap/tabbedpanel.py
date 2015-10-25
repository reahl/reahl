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
from reahl.web.bootstrap.navs import Nav, TabLayout, DropdownMenu, MenuItem


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

    def add_tab(self, tab):
        if not self.active_tab_set:
            self.set_active(tab)

        self.tabs.append(tab)
        menu_item = tab.add_to_menu(self.nav)

        if tab.is_active(self.tab):
            menu_item.set_active()

        self.add_pane_for(tab)
        return tab

    def add_pane_for(self, tab):
        return tab.add_contents_to(self.content_panel)



class Tab(object):
    def __init__(self, view, title, tab_key, contents_factory):
        self.title = title
        self.tab_key = tab_key
        self.contents_factory = contents_factory
        self.view = view

    def get_bookmark(self, view):
        return view.as_bookmark(description=self.title, query_arguments=self.query_arguments)

    @property
    def query_arguments(self):
        return {'tab': self.tab_key}

    @property
    def contents(self):
        return self.contents_factory.create(self.view)

    def is_active(self, tab_key):
        return self.tab_key == tab_key

    def add_to_menu(self, menu):
        menu_item = menu.add_bookmark(self.get_bookmark(menu.view))
        menu_item.a.set_attribute('data-toggle', menu.layout.key)
        menu_item.a.set_attribute('data-target', '#%s' % self.css_id)
        return menu_item

    @property
    def css_id(self):
        return 'tab_%s' % self.tab_key

    def add_contents_to(self, content_panel):
        self.add_pane(content_panel, self)

    def add_pane(self, content_panel, tab):
        div = content_panel.add_child(Div(self.view))
        div.add_child(tab.contents)
        div.append_class('tab-pane')
        div.set_id(tab.css_id)
#        if tab.is_active(self.tab):
#            div.append_class('active')
        return div


class MultiTab(Tab):
    def __init__(self, view, title, tab_key, contents_factory):
        self.tabs = []
        self.menu = DropdownMenu(view)
        super(MultiTab, self).__init__(view, title, tab_key, contents_factory)
        
    def add_tab(self, tab):
        menu_item = self.menu.add_bookmark(tab.get_bookmark(self.view))
        menu_item.a.set_attribute('data-toggle', 'tab')#self.menu.layout.key)
        menu_item.a.set_attribute('data-target', '#%s' % tab.css_id)
        self.tabs.append(tab)
        return tab

    @property
    def first_tab(self):
        return self.tabs[0]

    def current_sub_tab(self, tab_key):
        active_tab = [tab for tab in self.tabs
                      if tab.is_active(tab_key)]
        if len(active_tab) == 1:
            return active_tab[0]
        return self.first_tab

    def add_contents_to(self, content_panel):
        for tab in [self]+self.tabs:
            self.add_pane(content_panel, tab)

    def is_active(self, tab_key):
        if self.current_sub_tab(tab_key).is_active(tab_key):
            return True
        return super(MultiTab, self).is_active(tab_key)

    def add_to_menu(self, menu):
        return menu.add_dropdown(self.title, self.menu)
