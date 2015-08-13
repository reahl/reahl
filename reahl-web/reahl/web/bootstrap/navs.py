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

from collections import OrderedDict
import copy

from reahl.web.fw import Layout, Widget
from reahl.web.ui import Form, Div, Header, Footer, Slot, HTML5Page, ValidationStateAttributes, AccessRightAttributes, \
                             Span, Input, TextInput, Label, TextNode, ButtonInput, P, WrappedInput

import reahl.web.layout
from reahl.component.exceptions import ProgrammerError, arg_checks, IsInstance
from reahl.web.ui import MenuItem



class Nav(reahl.web.ui.Menu):
    css_class = 'nav'
    
    def add_item(self, item):
        item.add_attribute_source(AccessRightAttributes(item.a, disabled_class='disabled'))
        return super(Nav, self).add_item(item)

    def add_dropdown(self, title, menu, drop_up=False, align_right=False):
        self.add_item(DropdownMenu(self.view, title, menu, drop_up, align_right))


class DropdownMenu(reahl.web.ui.SubMenu):
    def __init__(self, view, title, menu, drop_up, align_right, css_id=None):
        super(DropdownMenu, self).__init__(view, title, menu, css_id=css_id)
        self.append_class('drop%s' % ('up' if drop_up else 'down'))
        self.a.append_class('dropdown-toggle')
        self.a.set_attribute('data-toggle', 'dropdown')
        self.a.add_child(Span(view)).append_class('caret')
        menu.append_class('dropdown-menu')
        if align_right:
            menu.append_class('dropdown-menu-right')


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





