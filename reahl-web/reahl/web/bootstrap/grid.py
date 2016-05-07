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
.. versionadded:: 3.2

This module contains tools for laying out a page or part of a page
using a grid which resizes depending on the size of the device being
used to browse.


When creating a visual layout it is often useful to arrange elements
on an invisible grid. The tools here allows building such a grid, but
with a twist: the grid can resize depending on the size of the device
that is used to view it.

User devices come in a wide range of sizes. In order to be able
to change a layout depending on the size of a device, devices are classified
into several device classes: 'xs' (extra small), 'sm' (small), 'md'(medium),
'lg' (large), 'xl' (extra large).

Whenever you need to specify a size for Bootstrap grid element, you 
can specify the size that element should have *for each class of device*.

Bootstrap's grid system works on units of 1/12th the size of a given
parent width. A size for a particular device class is thus an integer
denoting a size in 1/12ths of its container's width.


"""
from __future__ import print_function, unicode_literals, absolute_import, division

import six

from reahl.component.exceptions import arg_checks, IsInstance
from reahl.web.fw import Layout
from reahl.web.ui import  Div
import reahl.web.layout
from reahl.component.exceptions import ProgrammerError


class Container(Layout):
    """A Container Layout sets up the HTMLElement it is used with to be
    centered and have some padding. It is mostly used only once on a
    page -- for the entire page, but can be nested too.

    Using a Container is compulsory if you want to make use of a
    ColumnLayout.

    :keyword fluid: If True, the container will fill the entire available width, else 
         it will be a fixed size adjusted only when the size of the current browser 
         changes past a device class threshhold.
    """
    def __init__(self, fluid=False):
        super(Container, self).__init__()
        self.fluid = fluid

    def customise_widget(self):
        container_class = 'container'
        if self.fluid:
            container_class = 'container-fluid'
        self.widget.append_class(container_class)


class PageLayout(reahl.web.layout.PageLayout):
    """A PageLayout adds a header and footer area to an
    :class:`reahl.web.ui.HTML5Page`, as well as a content area between
    the header and footer areas.  All of these contents are also
    wrapped in a :class:`~reahl.web.ui.Div`, which is handy for
    styling.

    This is a styled version of :class:`reahl.web.layout.PageLayout` which
    additionally ensures the containing
    :attr:`~reahl.web.bootstrap.grid.HTML5Page.document` is set up to
    use a :class:`Container` layout.

    See :class:`reahl.web.ui.HTML5Page` for the names of these stored
    as attributes.

    :keyword fluid: If True, the page will be take up all available width. (See :class:`Container`)
    :keyword contents_layout: A :class:`~reahl.web.ui.Layout` that will be applied to the content area.

    .. versionadded:: 3.2

    """
    @arg_checks(fluid=IsInstance(bool), contents_layout=IsInstance(Layout, allow_none=True))
    def __init__(self, fluid=False, contents_layout=None):
        super(PageLayout, self).__init__(contents_layout=contents_layout)
        self.fluid = fluid

    def customise_widget(self):
        super(PageLayout, self).customise_widget()
        self.document.use_layout(Container(fluid=self.fluid))


class HTMLAttributeValueOption(object):
    def __init__(self, option_string, is_set, prefix='', constrain_value_to=None):
        if is_set and (constrain_value_to and option_string not in constrain_value_to):
            raise ProgrammerError('"%s" should be one of %s' % (option_string, constrain_value_to))
        self.is_set = is_set
        self.prefix = prefix
        self.option_string = option_string
    
    def as_html_snippet(self):
        if not self.is_set:
            raise ProgrammerError('Attempt to add %s to html despite it not being set' % self)
        prefix_with_delimiter = '%s-' % self.prefix if self.prefix else ''
        return '%s%s' % (prefix_with_delimiter, self.option_string)


class DeviceClass(HTMLAttributeValueOption):
    device_classes = ['xs', 'sm', 'md', 'lg', 'xl']

    def __init__(self, class_label):
        super(DeviceClass, self).__init__(class_label, class_label is not None, constrain_value_to=self.device_classes)

    @property
    def class_label(self):
        return self.option_string

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
    """A size used for layouts that can adapt depending on how big the user device is.

    Sizes kwargs for each device class are given as integers that denote a number of 12ths
    of the size of the container of the element being sized. Eg: 6 would mean 6 12ths, or 
    1/2 the size of the container.

    If you specify a size for a device class, that size will be used for all devices of that
    class or bigger.

    It is not necessary to specify a size for every device class. By default, if a device
    class is omitted, it is assumed to be sized as per the nearest specified smaller device 
    class. If there is no smaller device class, a value of 12/12ths is assumed.

    :keyword xs: Size to use if the device is extra small.
    :keyword sm: Size to use if the device is small.
    :keyword md: Size to use if the device is medium.
    :keyword lg: Size to use if the device is large.
    :keyword xl: Size to use if the device is extra large.

    """
    def __init__(self, xs=None, sm=None, md=None, lg=None, xl=None):
        super(ResponsiveSize, self).__init__(xs=xs, sm=sm, md=md, lg=lg, xl=xl)
        self.offsets = {}

    def offset(self, xs=None, sm=None, md=None, lg=None, xl=None):
        self.offsets = ResponsiveSize(xs=xs, sm=sm, md=md, lg=lg, xl=xl)
        return self

    def calculated_size_for(self, device_class):
        classes_that_impact = [device_class]+device_class.all_smaller
        for possible_class in reversed(classes_that_impact):
            try:
                return self[possible_class.class_label]
            except KeyError:
                pass
        return 0

    def total_width_for(self, device_class):
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
    """A Layout that divides an element into a number of columns.

    Each argument passed to the constructor defines a column. Columns
    are added to the element using this Layout in the order they
    are passed to the constructor. Columns can also be added to the
    Widget later, by calling :meth:`ColumnLayout.add_column`.

    To define a column with a given :class:`ResponsiveSize`, pass a tuple of which
    the first element is the column name, and the second an
    instance of :class:`ResponsiveSize`.

    If an element is divided into a number of columns whose current 
    combined width is wider than 12/12ths, the overrun flows to make
    an additional row.

    It is customary, for example to specify smaller sizes (ito 12ths)
    for bigger devices where you want the columns to fit in next to each
    other, but use BIGGER sizes (such as 12/12ths) for the columns for
    smaller sized devices. This has the effect that what was displayed
    as columns next to each other on the bigger device is displayed
    as "stacked" cells on a smaller device.

    By default, the smallest device classes are sized 12/12ths.
    """
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
        """Called to add a column of given size.

        :param column_size: A :class:`ResponsiveSize`, used to size the column.
        """
        if ResponsiveSize.wraps_for_some_device_class(self.added_sizes+[column_size]):
            self.add_clearfix(column_size)
            
        column = super(ColumnLayout, self).add_column(column_size)
        
        for device_class, value in column_size.items():
            column.append_class('col-%s-%s' % (device_class, value))
        for device_class, value in column_size.offsets.items():
            column.append_class('col-%s-offset-%s' % (device_class, value))

        self.added_sizes.append(column_size)
        return column




