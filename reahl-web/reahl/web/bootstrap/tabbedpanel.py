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
from reahl.web.ui import Div, ActiveStateAttributes
from reahl.web.bootstrap.navs import Nav, TabLayout, DropdownMenu, MenuItem



assert True, '''TODO: open_item does not work w/o javascript & MultiTab should not have content & bring in here the ideas of Tabs holding on to their TabbedPanel & deciding on the fly whether they are active; the additions to MenuItem;


set_active (self.force_active is dead on menuitem?)
and the active_regex & exact_match - so... delete them and always delagate to the a unless determine_is_active_using is used...

'''

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

    def is_currently_open(self, tab):
        return tab.tab_key == self.tab

    def add_tab(self, tab):
        if not self.active_tab_set:
            self.set_active(tab)
        tab.set_panel(self)

        self.tabs.append(tab)
        tab.add_to_menu(self.nav)

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
        self.panel = None

    def get_bookmark(self, view):
        return view.as_bookmark(description=self.title, query_arguments=self.query_arguments)

    @property
    def query_arguments(self):
        return {'tab': self.tab_key}

    @property
    def contents(self):
        return self.contents_factory.create(self.view)

    def set_panel(self, tabbed_panel):
        self.panel = tabbed_panel

    @property
    def is_open(self):
        return self.panel.is_currently_open(self)

    @property
    def is_active(self):
        return self.is_open

    def add_to_menu(self, menu):
        menu_item = menu.add_bookmark(self.get_bookmark(menu.view))
        menu_item.determine_is_active_using(lambda: self.is_active)
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
        div.add_attribute_source(ActiveStateAttributes(tab, active_class='active'))
        return div


class MultiTab(Tab):
    def __init__(self, view, title, tab_key):
        self.tabs = []
        self.menu = DropdownMenu(view)
        super(MultiTab, self).__init__(view, title, tab_key, None)
        
    def add_tab(self, tab):
        menu_item = self.menu.add_bookmark(tab.get_bookmark(self.view))
        menu_item.a.set_attribute('data-toggle', 'tab')#self.menu.layout.key)
        menu_item.a.set_attribute('data-target', '#%s' % tab.css_id)
        tab.set_panel(self.panel)
        self.tabs.append(tab)
        return tab

    @property
    def query_arguments(self):
        return {'tab': self.panel.tab}

    @property
    def first_tab(self):
        return self.tabs[0]

    @property
    def current_sub_tab(self):
        open_tab = [tab for tab in self.tabs
                    if tab.is_open]
        if len(open_tab) == 1:
            return open_tab[0]
        return self.first_tab

    def add_contents_to(self, content_panel):
        for tab in self.tabs:
            self.add_pane(content_panel, tab)

    def set_panel(self, tabbed_panel):
        super(MultiTab, self).set_panel(tabbed_panel)
        for tab in self.tabs:
            tab.set_panel(tabbed_panel)

    @property
    def is_active(self):
        return self.is_open or self.current_sub_tab.is_open

    def add_to_menu(self, menu):
        menu_item = menu.add_dropdown(self.title, self.menu, query_arguments=self.query_arguments)
        menu_item.determine_is_active_using(lambda: self.is_active)
        return menu_item

