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
from reahl.web.ui import  Div

import reahl.web.layout
from reahl.component.exceptions import ProgrammerError



class Container(Layout):
    def __init__(self, fluid=False):
        super(Container, self).__init__()
        self.fluid = fluid

    def customise_widget(self):
        container_class = 'container'
        if self.fluid:
            container_class = 'container-fluid'
        self.widget.append_class(container_class)


class DeviceClass(object):
    device_classes = ['xs', 'sm', 'md', 'lg', 'xl']

    def __init__(self, class_label):
        assert class_label in self.device_classes, '%s is not a supported DeviceClass. Should be one of: %s' % (class_label, ','.join(self.device_classes))
        self.class_label = class_label

    @property
    def one_smaller(self):
        index_of_one_smaller_class = self.device_classes.index(self.class_label) - 1
        if index_of_one_smaller_class < 0:
            return None
        return DeviceClass(self.device_classes[index_of_one_smaller_class])

    @property
    def all_smaller(self):
        return [DeviceClass(i) for i in self.device_classes[:self.device_classes.index(self.class_label)]]

    @classmethod
    def all_classes(cls):
        return [DeviceClass(i) for i in DeviceClass.device_classes]


class ResponsiveSize(reahl.web.layout.ResponsiveSize):
    def __init__(self, xs=None, sm=None, md=None, lg=None, xl=None):
        super(ResponsiveSize, self).__init__(xs=xs, sm=sm, md=md, lg=lg, xl=xl)
        self.offsets = {}

    def offset(self, xs=None, sm=None, md=None, lg=None, xl=None):
        self.offsets = ResponsiveSize(xs=xs, sm=sm, md=md, lg=lg, xl=xl)
        return self

    def calculated_size_for(self, device_class):
        assert isinstance(device_class, DeviceClass), 'Incorrect type %s, expected %s' % (type(device_class), type(DeviceClass))
        classes_that_impact = [device_class]+device_class.all_smaller
        for possible_class in reversed(classes_that_impact):
            try:
                return self[possible_class.class_label]
            except KeyError:
                pass
        return 0

    def total_width_for(self, device_class):
        assert isinstance(device_class, DeviceClass), 'Incorrect type %s, expected %s' % (type(device_class), type(DeviceClass))
        total = self.calculated_size_for(device_class)
        if self.offsets:
            total += self.offsets.calculated_size_for(device_class)
        return total

    @classmethod
    def wraps_for_some_device_class(cls, sizes):
        return any([cls.wraps_for(device_class, sizes)
                   for device_class in DeviceClass.all_classes()])

    @classmethod    
    def wraps_for(cls, device_class, sizes):
        return (cls.sum_sizes_for(device_class, sizes)) > 12

    @classmethod    
    def sum_sizes_for(cls, device_class, sizes):
        total = 0
        for size in sizes:
            total += size.total_width_for(device_class)
        return total



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

    def add_clearfix(self, column_size):
        clearfix = self.widget.add_child(Div(self.view))
        clearfix.append_class('clearfix')
        for device_class in DeviceClass.all_classes():
            if ResponsiveSize.wraps_for(device_class, self.added_sizes+[column_size]):
                clearfix.append_class('visible-%s-block' % device_class.class_label)

    def add_column(self, column_size):
        if ResponsiveSize.wraps_for_some_device_class(self.added_sizes+[column_size]):
            self.add_clearfix(column_size)
            
        column = super(ColumnLayout, self).add_column(column_size)

        #TODO: these device_class'es are strings - need to ensure they are valid device classes
        for device_class, value in column_size.items():
            column.append_class('col-%s-%s' % (device_class, value))
        for device_class, value in column_size.offsets.items():
            column.append_class('col-%s-offset-%s' % (device_class, value))

        self.added_sizes.append(column_size)
        return column




