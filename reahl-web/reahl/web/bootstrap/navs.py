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
from reahl.web.fw import Layout, Bookmark
from reahl.web.ui import AccessRightAttributes, ActiveStateAttributes, Div
import reahl.web.attic
from reahl.web.bootstrap.ui import Span, A

from reahl.component.exceptions import ProgrammerError

from reahl.web.attic.menu import MenuItem 


class NavMenuLayout(reahl.web.ui.MenuLayout):
    def customise_widget(self):
        self.widget.append_class('nav')

    def add_item(self, item):
        li = super(NavMenuLayout, self).add_item(item)
        li.append_class('nav-item')
        item.a.append_class('nav-link')
        item.a.add_attribute_source(ActiveStateAttributes(item, active_class='active'))
        item.a.add_attribute_source(AccessRightAttributes(item.a, disabled_class='disabled'))
        return li

    def add_submenu(self, dropdown, title):
        raise ProgrammerError('You cannot add a submenu to a %s, please use .add_dropdown() instead.' % self.widget.__class__)

    def get_bookmark(self, dropdown_key, title, opened):
        if opened:
            query_arguments={'open_dropdown': ''}
        else:
            query_arguments={'open_dropdown': dropdown_key}
        return Bookmark('', '', description=title, query_arguments=query_arguments, ajax=True)

    def add_dropdown(self, dropdown, title, drop_up, open_dropdown):
        opened = open_dropdown==dropdown.key
        menu_item = MenuItem(self.view, A.from_bookmark(self.view, self.get_bookmark(dropdown.key, title, opened)))
        li = self.add_item(menu_item)
        if opened:
            li.append_class('open')
        menu_item.a.append_class('dropdown-toggle')
        menu_item.a.set_attribute('data-toggle', 'dropdown')
        menu_item.a.set_attribute('data-target', '-')
        menu_item.a.add_child(Span(self.view)).append_class('caret')
        li.append_class('drop%s' % ('up' if drop_up else 'down'))
        li.add_child(dropdown)
        return menu_item


# To test:
#  That dropdown menus open/close when no javascript
#  and that they do not actually break in js when JS is on.


class Nav(reahl.web.attic.menu.Menu):
    def __init__(self, view, css_id=None):
        self.open_dropdown = None
        super(Nav, self).__init__(view, [], menu_layout=NavMenuLayout(), css_id=None)

    def add_dropdown(self, title, dropdown_menu, drop_up=False):
        return self.menu_layout.add_dropdown(dropdown_menu, title, drop_up, self.open_dropdown)

    @exposed
    def query_fields(self, fields):
        fields.open_dropdown = Field(required=False, default=None)



class NavItem(reahl.web.attic.menu.MenuItem):
    pass


class DropdownMenuLayout(reahl.web.ui.MenuLayout):
    def __init__(self, align_right):
        super(DropdownMenuLayout, self).__init__()
        self.align_right = align_right

    def customise_widget(self):
        self.widget.append_class('dropdown-menu')
        if self.align_right:
            self.widget.append_class('dropdown-menu-right')

    def add_item(self, item):
        self.widget.html_representation.add_child(item.a)
        item.a.append_class('dropdown-item')
        item.a.add_attribute_source(ActiveStateAttributes(item, active_class='active'))
        item.a.add_attribute_source(AccessRightAttributes(item.a, disabled_class='disabled'))
        return item

    def add_submenu(self, dropdown, title):
        raise ProgrammerError('You cannot add a submenu to a %s.' % self.widget.__class__)


class DropdownMenu(reahl.web.attic.menu.Menu):
    key = '1'
    def __init__(self, view, align_right=False, css_id=None):
        super(DropdownMenu, self).__init__(view, [], menu_layout=DropdownMenuLayout(align_right), css_id=css_id)

    def create_html_representation(self):
        div = self.add_child(Div(self.view))
        self.set_html_representation(div)
        return div




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





