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

from collections import OrderedDict
import copy

from reahl.web.fw import Layout
from reahl.web.ui import Div, Header, Footer, Slot, HTML5Page
import reahl.web.layout
from reahl.component.exceptions import ProgrammerError, arg_checks, IsInstance



class Container(Layout):
    def __init__(self, fluid=False):
        super(Container, self).__init__()
        self.fluid = fluid

    def customise_widget(self):
        container_class = 'container'
        if self.fluid:
            container_class = 'container-fluid'
        self.widget.append_class(container_class)



class ResponsiveSize(reahl.web.layout.ResponsiveSize):
    def __init__(self, xs=None, sm=None, md=None, lg=None):
        super(ResponsiveSize, self).__init__(xs=xs, sm=sm, md=md, lg=lg)
        self.offsets = {}

    def set_offsets(self, xs=None, sm=None, md=None, lg=None):
        self.offsets = ResponsiveSize(xs=xs, sm=sm, md=md, lg=lg)

    def with_offset(self, xs=None, sm=None, md=None, lg=None):
        size_with_offsets = copy.deepcopy(self)
        size_with_offsets.set_offsets(xs=xs, sm=sm, md=md, lg=lg)
        return size_with_offsets


class ColumnLayout(reahl.web.layout.ColumnLayout):
    def __init__(self, *column_definitions):
        if not all([isinstance(column_definition, tuple) for column_definition in column_definitions]):
            raise ProgrammerError('All column definitions are expected a tuple of the form (name, %s), got %s' %\
                                  (ResponsiveSize, column_definitions))
        self.added_sizes = []
        super(ColumnLayout, self).__init__(*column_definitions)

    def customise_widget(self):
        super(ColumnLayout, self).customise_widget()
        self.widget.append_class('row')
    
    def add_column(self, column_size):
        for device_class in ['xs', 'sm', 'md', 'lg']:
            if self.row_will_wrap_when_added(device_class, column_size):
                clearfix = self.widget.add_child(Div(self.view))
                clearfix.append_class('clearfix')
                clearfix.append_class('visible-%s' % device_class)
            
        column = super(ColumnLayout, self).add_column(column_size)

        for device_class, value in column_size.items():
            column.append_class('col-%s-%s' % (device_class, value))
        for device_class, value in column_size.offsets.items():
            column.append_class('col-%s-offset-%s' % (device_class, value))

        self.added_sizes.append(column_size)
        return column

    def row_will_wrap_when_added(self, device_class, to_add):
        return (self.total_width_for(device_class, self.added_sizes) + \
                self.total_width_for(device_class, [to_add]        )) > 12

    def total_width_for(self, device_class, sizes):
        total = 0
        for size in sizes:
            if device_class in size:
                total += size[device_class]
            if device_class in size.offsets:
                total += size.offsets[device_class]
        return total

