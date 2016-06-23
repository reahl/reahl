# Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.
# -*- encoding: utf-8 -*-
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

import warnings

from reahl.component.modelinterface import exposed, Field
from reahl.web.attic.layout import VerticalLayout, HorizontalLayout
from reahl.web.attic.menu import Menu
from reahl.web.fw import Bookmark
from reahl.web.ui import Div

#AppliedPendingMove: In future this class may be renamed to: reahl.web.attic.tabbedpanel:Tab
class Tab(object):
    """One Tab in a :class:`TabbedPanel`.

       .. admonition:: Styling

          Rendered like a :class:`MenuItem`, with the <a> containing `title`.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param title: Text that is displayed inside the Tab itself.
       :param tab_key: A name for this tag identifying it uniquely amongst other Tabs in the same :class:`TabbedPanel`.
       :param contents_factory: A :class:`WidgetFactory` specifying how to create the contents of this Tab, once selected.
       :keyword css_id: (Deprecated)

       .. versionchanged: 3.2
          Deprecated css_id keyword argument.
    """
    def __init__(self, view, title, tab_key, contents_factory, css_id=None):
        super(Tab, self).__init__()
        self.title = title
        self.tab_key = tab_key
        self.contents_factory = contents_factory
        self.view = view
        self.panel = None

    def get_bookmark(self, view):
        return Bookmark.for_widget(self.title, query_arguments=self.query_arguments).on_view(view)

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
        menu_item = menu.add_bookmark(self.get_bookmark(self.view))
        menu_item.determine_is_active_using(lambda: self.is_active)
        return menu_item


#AppliedPendingMove: In future this class may be renamed to: reahl.web.attic.tabbedpanel:MultiTab
class MultiTab(Tab):
    """A composite tab. Instead of a single choice for the user, clicking on a MultiTab
       results in a dropdown menu with more choices for the user.

       .. admonition:: Styling

          Rendered like a :class:`Tab`, but with more contents. The usual <a> containing the title
          is followed by an &nbsp; and an <a class="dropdown-handle">. This is followed by a
          normal :class:`VMenu`.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param title: (See :class:`Tab`)
       :param tab_key: (See :class:`Tab`)
       :param contents_factory: (See :class:`Tab`)
       :keyword css_id: (Deprecated)

       .. versionchanged: 3.2
          Deprecated css_id keyword argument.
    """
    def __init__(self, view, title, tab_key, contents_factory, css_id=None):
        if css_id:
            self.set_id(css_id)
            warnings.warn('DEPRECATED: Passing a css_id upon construction. ' \
                          'This ability will be removed in future versions.',
                          DeprecationWarning, stacklevel=2)
        self.tabs = []
        self.menu = Menu(view).use_layout(VerticalLayout())
        super(MultiTab, self).__init__(view, title, tab_key, contents_factory)

    def add_tab(self, tab):
        tab.add_to_menu(self.menu)
        self.tabs.append(tab)
        tab.set_panel(self.panel)
        return tab

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

    @property
    def is_active(self):
        return self.is_open or self.current_sub_tab.is_open

    @property
    def contents(self):
        if self.is_open:
            return super(MultiTab, self).contents
        else:
            return self.current_sub_tab.contents

    def set_panel(self, tabbed_panel):
        super(MultiTab, self).set_panel(tabbed_panel)
        for tab in self.tabs:
            tab.set_panel(tabbed_panel)

    def add_to_menu(self, menu):
        menu_item = menu.add_submenu(self.title, self.menu, query_arguments=self.query_arguments, add_dropdown_handle=True)
        menu_item.determine_is_active_using(lambda: self.is_active)
        return menu_item


#AppliedPendingMove: In future this class may be renamed to: reahl.web.attic.tabbedpanel:TabbedPanel
# Uses: reahl/web/reahl.tabbedpanel.css
# Uses: reahl/web/reahl.tabbedpanel.js
class TabbedPanel(Div):
    """A Div sporting different Tabs which the user can select to change what is displayed. The contents
       of a TabbedPanel are changed when the user clicks on a different Tab without refreshing the entire
       page, provided that JavaScript is available on the user agent.

       .. admonition:: Styling

          Rendered as a <div class="reahl-tabbedpanel"> which contains two children: an :class:`HMenu`
          containing instances of :class:`Tab` for MenuItems, followed by a <div> that will be populated
          by the current contents of the TabbedPanel.

       :param view: (See :class:`reahl.web.fw.Widget`)
       :param css_id: (Deprecated) (See :class:`reahl.web.ui.HTMLElement`)

       .. versionchanged: 3.2
          Deprecated use css_id keyword argument.
    """
    def __init__(self, view, css_id):
        super(TabbedPanel, self).__init__(view, css_id=css_id)
        self.append_class('reahl-tabbedpanel')
        self.tabs = []
        self.menu = self.add_child(Menu(view).use_layout(HorizontalLayout()))
        self.content_panel = self.add_child(Div(view))
        self.enable_refresh()
        if css_id:
            warnings.warn('DEPRECATED: Passing css_id upon construction. '  \
                          'Instead, construct, then call .set_id().',
                          DeprecationWarning, stacklevel=2)

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
        """Adds the Tab `tab` to this TabbedPanel."""
        if not self.active_tab_set:
            self.set_active(tab)
        tab.set_panel(self)

        self.tabs.append(tab)
        tab.add_to_menu(self.menu)

        self.add_pane_for(tab)
        return tab

    def add_pane_for(self, tab):
        if tab.is_active:
            self.content_panel.add_child(tab.contents)


