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
from reahl.web.ui import AccessRightAttributes, ActiveStateAttributes, Div, Menu, MenuItem
from reahl.web.bootstrap.ui import Span, A

from reahl.component.exceptions import ProgrammerError




class NavLayout(Layout):
    def __init__(self, key=None, justified=False):
        super(NavLayout, self).__init__()
        self.justified = justified
        self.key = key

    @property
    def additional_css_class(self):
        return 'nav-%ss' % self.key

    def customise_widget(self):
        super(NavLayout, self).customise_widget()
        if self.key:
            self.widget.append_class(self.additional_css_class)
        if self.justified:
            self.widget.append_class('nav-justified')



class Nav(Menu):
    add_reahl_styling = False

    def __init__(self, view, a_list=None, css_id=None):
        self.open_item = None
        super(Nav, self).__init__(view, a_list=None, css_id=None)

    @exposed
    def query_fields(self, fields):
        fields.open_item = Field(required=False, default=None)

    def create_html_representation(self):
        li = super(Nav, self).create_html_representation()
        li.append_class('nav')
        return li
    
    def add_dropdown(self, title, dropdown_menu, drop_up=False, query_arguments={}):
        return self.add_submenu(title, dropdown_menu, extra_query_arguments=query_arguments, drop_up=drop_up)

    def add_html_for_item(self, item):
        li = super(Nav, self).add_html_for_item(item)
        li.append_class('nav-item')
        item.a.append_class('nav-link')
        item.a.add_attribute_source(ActiveStateAttributes(item, active_class='active'))
        item.a.add_attribute_source(AccessRightAttributes(item.a, disabled_class='disabled'))
        return li

    def add_submenu(self, title, menu, extra_query_arguments={}, **kwargs):
        if self.open_item == title:
            query_arguments={'open_item': ''}
        else:
            query_arguments={'open_item': title}
        query_arguments.update(extra_query_arguments)
        submenu = super(Nav, self).add_submenu(title, menu, query_arguments=query_arguments, **kwargs)
        return submenu
    
    def add_html_for_submenu(self, submenu, drop_up=False):
        li = super(Nav, self).add_html_for_submenu(submenu)
        if self.open_item == submenu.title:
            li.append_class('open')
        submenu.a.append_class('dropdown-toggle')
        submenu.a.set_attribute('data-toggle', 'dropdown')
        submenu.a.set_attribute('data-target', '-')
        submenu.a.add_child(Span(self.view)).append_class('caret')
        li.append_class('drop%s' % ('up' if drop_up else 'down'))
        return li



class DropdownMenuLayout(Layout):
    def __init__(self, align_right=False):
        super(DropdownMenuLayout, self).__init__()
        self.align_right = align_right

    def customise_widget(self):
        if self.align_right:
            self.widget.append_class('dropdown-menu-right')



class DropdownMenu(Menu):
    add_reahl_styling = False
    def create_html_representation(self):
        div = self.add_child(Div(self.view))
        self.set_html_representation(div)
        div.append_class('dropdown-menu')
        return div

    def add_html_for_item(self, item):
        self.html_representation.add_child(item.a)
        item.a.append_class('dropdown-item')
        item.a.add_attribute_source(ActiveStateAttributes(item, active_class='active'))
        item.a.add_attribute_source(AccessRightAttributes(item.a, disabled_class='disabled'))
        return item.a

    def add_submenu(self, menu, title):
        raise ProgrammerError('You cannot add a submenu to a %s.' % self.widget.__class__)



class PillLayout(NavLayout):
    def __init__(self, stacked=False, justified=False):
        super(PillLayout, self).__init__(key='pill', justified=justified)
        if all([stacked, justified]):
            raise ProgrammerError('Pills must be stacked or justified, but not both')
        self.stacked = stacked
        self.justified = justified

    def customise_widget(self):
        super(PillLayout, self).customise_widget()
        if self.stacked:
            self.widget.append_class('nav-stacked')


class TabLayout(NavLayout):
    def __init__(self, justified=False):
        super(TabLayout, self).__init__(key='tab', justified=justified)





