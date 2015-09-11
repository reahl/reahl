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

from reahl.web.fw import Layout
from reahl.web.ui import AccessRightAttributes, ActiveStateAttributes, Div
import reahl.web.attic
from reahl.web.bootstrap.ui import Span, A

from reahl.component.exceptions import ProgrammerError

from reahl.web.attic.menu import MenuItem 

class Nav(reahl.web.attic.menu.Menu):
    css_class = 'nav'
    
    def add_item(self, item):
        super(Nav, self).add_item(item)
        item.append_class('nav-item')
        item.a.append_class('nav-link')
        return item

    def add_dropdown(self, title, dropdown_menu, drop_up=False):
        dropdown = NavItem(self.view, A(self.view, None, description=title))
        dropdown.append_class('drop%s' % ('up' if drop_up else 'down'))
        dropdown.a.append_class('dropdown-toggle')
        dropdown.a.set_attribute('data-toggle', 'dropdown')
        dropdown.a.add_child(Span(self.view)).append_class('caret')
        dropdown.html_representation.add_child(dropdown_menu)
        return self.add_item(dropdown)

    def add_item_from_bookmark(self, bookmark):
        return self.add_item(NavItem.from_bookmark(self.view, bookmark))


class NavItem(reahl.web.attic.menu.MenuItem):
    def __init__(self, view, a, active_regex=None, exact_match=False, css_id=None):
        super(NavItem, self).__init__(view, a, active_regex=active_regex, exact_match=exact_match, css_id=css_id)
        self.a.add_attribute_source(ActiveStateAttributes(self, active_class='active'))
        self.a.add_attribute_source(AccessRightAttributes(self.a, disabled_class='disabled'))



class DropdownMenu(reahl.web.attic.menu.Menu):
    def __init__(self, view, a_list, align_right=False, css_id=None):
        super(DropdownMenu, self).__init__(view, a_list, css_id=css_id)
        self.append_class('dropdown-menu')
        if align_right:
            self.append_class('dropdown-menu-right')

    def create_html_representation(self):
        div = self.add_child(Div(self.view))
        self.set_html_representation(div)
        return div

    def add_item(self, item):
        """Adds MenuItem `item` to this Menu."""
        self.menu_items.append(item)
        self.html_representation.add_child(item.a)
        item.a.append_class('dropdown-item')
        return item

    def add_item_from_bookmark(self, bookmark):
        return self.add_item(NavItem.from_bookmark(self.view, bookmark))


class NavLayout(Layout):
    def __init__(self, justified=False):
        super(NavLayout, self).__init__()
        self.justified = justified

    def customise_widget(self):
        self.widget.append_class('nav')
        if self.justified:
            self.widget.append_class('nav-justified')


class PillLayout(NavLayout):
    def __init__(self, stacked=False, justified=False):
        super(PillLayout, self).__init__(justified=justified)
        if all([stacked, justified]):
            raise ProgrammerError('Pills must be stacked or justified, but not both')
        self.stacked = stacked
        self.justified = justified

    def customise_widget(self):
        super(PillLayout, self).customise_widget()
        self.widget.append_class('nav-pills')
        if self.stacked:
            self.widget.append_class('nav-stacked')


class TabLayout(NavLayout):
    def customise_widget(self):
        super(TabLayout, self).customise_widget()
        self.widget.append_class('nav-tabs')





