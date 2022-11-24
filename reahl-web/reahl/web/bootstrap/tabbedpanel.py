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

""".. versionadded:: 3.2

TabbedPanels are used to save space by stacking different panels on
top of one another. While each panel has its own contents only the
top panel is visible, thus taking up visual space of only one such
panel.

"""

# noinspection PyUnresolvedReferences

from reahl.component.modelinterface import ExposedNames, Field
from reahl.web.fw import Widget
from reahl.web.ui import Div, ActiveStateAttributes, DelegatedAttributes
from reahl.web.bootstrap.navs import Nav, TabLayout, DropdownMenu


class TabbedPanel(Widget):
    """A Widget that appears as having multiple panels of content stacked 
    on top of one another -- with only one panel visible at a time.

    Each content panel appears to have a label sticking out (its
    "tab").  When the user clicks on a different Tab, its panel is
    raised to the top and thus made visible. This is done without
    refreshing the entire page, provided that JavaScript is available
    on the user agent.

    :param view: (See :class:`reahl.web.fw.Widget`)
    :keyword nav_layout: Optionally, an :class:`~reahl.web.bootstrap.navs.PillLayout` or 
                  :class:`~reahl.web.bootstrap.navs.TabLayout` for fine-grained control over 
                  how the :class:`~reahl.web.bootstrap.navs.Nav` which represents the tabs is
                  displayed.
    """
    def __init__(self, view, nav_layout=None):
        super().__init__(view)
        self.tabs = []
        self.nav = self.add_child(Nav(view).use_layout(nav_layout or TabLayout()))
        self.content_panel = self.add_child(Div(view))
        self.content_panel.append_class('tab-content')

    query_fields = ExposedNames()
    query_fields.tab = lambda i: Field(required=False, default=None)

    @property
    def active_tab_set(self):
        return self.tab is not None

    def set_active(self, tab):
        # noinspection PyAttributeOutsideInit
        self.tab = tab.default_active_tab_key

    def is_currently_open(self, tab):
        return tab.tab_key == self.tab

    def add_tab(self, tab):
        """Add a panel for the given :class:`Tab` to this TabbedPanel.

        :param tab: The :class:`Tab` to be added.
        """
        if not self.active_tab_set:
            self.set_active(tab)
        tab.set_panel(self)

        self.tabs.append(tab)
        tab.add_to_menu(self.nav)
        tab.add_contents_to(self.content_panel)

        return tab


class TabContentAttributes(DelegatedAttributes):
    def __init__(self, tab):
        super().__init__()
        self.tab = tab

    def set_attributes(self, attributes):
        super().set_attributes(attributes)

        attributes.set_to('data-toggle', self.tab.data_toggle)
        attributes.set_to('data-target', '#%s' % self.tab.css_id)
        attributes.set_to('aria-controls', '%s' % self.tab.css_id)
        attributes.set_to('role', 'tab')


class Tab:
    """
    One Tab in a :class:`TabbedPanel`, including the contents that should be displayed for it.

    :param view: (See :class:`reahl.web.fw.Widget`)
    :param title: The label Text that is displayed inside the Tab itself.
    :param tab_key: A name for this tag identifying it uniquely amongst other Tabs in the same :class:`TabbedPanel`.
    :param contents_factory: A :class:`reahl.web.fw.WidgetFactory` specifying how to create the contents of this Tab, 
                            once selected.
    """
    def __init__(self, view, title, tab_key, contents_factory):
        self.title = title
        self.tab_key = tab_key
        self.contents_factory = contents_factory
        self.view = view
        self.panel = None
        self.menu_item = None

    def get_bookmark(self, view):
        return view.as_bookmark(description=self.title, query_arguments=self.query_arguments)

    @property
    def top_level_nav(self):
        return self.panel.nav

    @property
    def data_toggle(self):
        return self.top_level_nav.layout.key

    @property
    def default_active_tab_key(self):
        return self.tab_key

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
        menu_item.a.set_css_id('nav_%s_tab' % self.css_id)
        menu_item.a.add_attribute_source(TabContentAttributes(self))
        menu_item.a.add_attribute_source(ActiveStateAttributes(menu_item, attribute_name='aria-selected', active_value='true', inactive_value='false'))
        self.menu_item = menu_item
        return menu_item

    @property
    def css_id(self):
        return 'tab_%s' % self.tab_key

    def add_contents_to(self, content_panel):
        return self.add_contents_of_tab_to(content_panel, self)

    def add_contents_of_tab_to(self, content_panel, tab):
        assert tab.menu_item, 'add the tab to a menu first before adding its contents'
        div = content_panel.add_child(Div(self.view))
        div.add_child(tab.contents)
        div.append_class('tab-pane')
        div.set_attribute('role', 'tabpanel')
        div.set_id(tab.css_id)
        div.add_attribute_source(ActiveStateAttributes(tab, active_value='active'))
        div.set_attribute('aria-labelledby', '%s' % tab.menu_item.a.css_id)
        return div


class MultiTab(Tab):
    """
    A composite tab. Instead of a single choice for the user, clicking on a MultiTab
    results in a dropdown menu with more choices for the user. These second-level
    choices are navigable tabs.

    :param view: (See :class:`reahl.web.fw.Widget`)
    :param title: (See :class:`Tab`)
    :param tab_key: (See :class:`Tab`)
    """
    def __init__(self, view, title, tab_key):
        self.tabs = []
        self.menu = DropdownMenu(view)
        super().__init__(view, title, tab_key, None)
        
    def add_tab(self, tab):
        tab.add_to_menu(self.menu)
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
            self.add_contents_of_tab_to(content_panel, tab)

    def set_panel(self, tabbed_panel):
        super().set_panel(tabbed_panel)
        for tab in self.tabs:
            tab.set_panel(tabbed_panel)

    @property
    def default_active_tab_key(self):
        return self.first_tab.tab_key

    @property
    def is_active(self):
        return self.is_open or self.current_sub_tab.is_open

    def add_to_menu(self, menu):
        menu_item = menu.add_dropdown(self.title, self.menu, query_arguments=self.query_arguments)
        menu_item.determine_is_active_using(lambda: self.is_active)
        return menu_item
