# Copyright 2015-2020 Reahl Software Services (Pty) Ltd. All rights reserved.
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

This module contains tools for controlling how elements are positioned.

The main tool here is an invisible layout grid which changes depending
on the size of the device being used to browse. The module also contains
several other related tools.

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

from collections import OrderedDict
import copy

from reahl.component.exceptions import ProgrammerError
from reahl.component.exceptions import arg_checks, IsInstance
from reahl.web.fw import Layout
from reahl.web.ui import Div, Slot, HTMLAttributeValueOption


class Container(Layout):
    """A Container Layout manages the positioning of the main areas of
    a page. By default it ensures that the HTMLElement it is used with to be
    has a size that stays at a fixed width per device class and that it stays
    centered in the horizontal.

    Using a Container is compulsory if you want to make use of a
    ColumnLayout.

    :keyword fluid: If True, the container fills the entire available width. If a string denoting a device class, the container fills the entire width for smaller device classes only.

    .. versionchanged: 5.0
       Changed `fluid` to also take a device class string to make the Container responsive.
    """
    def __init__(self, fluid=False):
        super().__init__()
        self.fluid = fluid

    def customise_widget(self):
        container_class = 'container'
        if self.fluid is True:
            container_class = 'container-fluid'
        elif self.fluid:
            container_class = HTMLAttributeValueOption(self.fluid, True, prefix='container', constrain_value_to=DeviceClass.device_classes).as_html_snippet()

        self.widget.append_class(container_class)


class DeviceClass:
    device_classes = ['xs', 'sm', 'md', 'lg', 'xl']

    def __init__(self, name):
        self.name = name
        if not name in self.device_classes:
            raise ProgrammerError('Invalid device class name: %s, should be one of %s' % (name, ','.join(self.device_classes)))

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    @property
    def one_smaller(self):
        index_of_one_smaller_class = self.device_classes.index(self.name) - 1
        if index_of_one_smaller_class < 0:
            return None
        return DeviceClass(self.device_classes[index_of_one_smaller_class])

    @property
    def all_smaller(self):
        return [DeviceClass(i) for i in self.device_classes[:self.device_classes.index(self.name)]]

    @classmethod
    def all_classes(cls):
        return [DeviceClass(i) for i in DeviceClass.device_classes]

    def as_combined_css_class(self, before_parts, after_parts):
        parts = before_parts + list(filter(None, [None if self.name == 'xs' else self.name])) + after_parts
        return '-'.join(parts)


class ResponsiveOption:
    def __init__(self, allowed_options, prefix=None, xs=None, sm=None, md=None, lg=None, xl=None):
        self.prefix = prefix
        self.allowed_options = allowed_options
        all_options = {'xs':xs, 'sm':sm, 'md':md, 'lg':lg, 'xl':xl}
        self.device_options = {DeviceClass(device_class_name): option_value for (device_class_name, option_value) in all_options.items() if option_value}
        if not all([i in self.allowed_options for i in self.device_options.values()]):
            raise ProgrammerError('Illegal option. Allowed options: %s, got: %s' % (self.allowed_options, self.device_options))

    def __len__(self):
        return self.device_options.__len__()

    def add_css_classes(self, html_widget, prefix=None):
        classes = []
        for device_class, value in self.device_options.items():
            prefix_to_use = prefix or self.prefix
            css_class = device_class.as_combined_css_class([prefix_to_use] if prefix_to_use else [],
                                                           [str(value)] if value is not True else [])
            html_widget.append_class(css_class)
            classes.append(css_class)

        return classes


class ContentJustification(ResponsiveOption):
    """Specifies how elements should be spaced horizontally inside a parent.

    For each device size specify alignment as one of:
      * 'start': to align at the start.
      * 'end': to align at the end.
      * 'center': to align in the center of available space.
      * 'between': distribute all empty space evenly between items, but with no space before the first element or after the last element.
      * 'around': distribute all empty space evenly between items, including before the first element and after the last element.

    :keyword xs: Alignment to use if the device is extra small.
    :keyword sm: Alignment to use if the device is small.
    :keyword md: Alignment to use if the device is medium.
    :keyword lg: Alignment to use if the device is large.
    :keyword xl: Alignment to use if the device is extra large.

    .. versionadded:: 4.0
    """
    def __init__(self, **kwargs):
        super().__init__(['start', 'center', 'end', 'between', 'around'], prefix='justify-content', **kwargs)


class Alignment(ResponsiveOption):
    """Specifies how elements should be aligned vertically inside a parent.

    For each device size specify alignment as one of:
      * 'start': to align at the top.
      * 'end': to align at the bottom.
      * 'center': to align in the center of available space.
      * 'baseline': to align with the bottom of the first text line of neighbouring elements.
      * 'stretch': stretches to fill all vertical space.

    :keyword xs: Alignment to use if the device is extra small.
    :keyword sm: Alignment to use if the device is small.
    :keyword md: Alignment to use if the device is medium.
    :keyword lg: Alignment to use if the device is large.
    :keyword xl: Alignment to use if the device is extra large.

    .. versionadded:: 4.0
    """
    def __init__(self, **kwargs):
        super().__init__(['start', 'end', 'center', 'baseline', 'stretch'], **kwargs)

    def add_css_classes(self, html_widget, prefix=None):
        if isinstance(html_widget.layout, ColumnLayout):
            scope = 'items'
        else:
            scope = 'self'

        return super().add_css_classes(html_widget, prefix=prefix or 'align-%s' % scope)


class ResponsiveSize(ResponsiveOption):
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
    def __init__(self, **sizes):
        super().__init__(range(1, 13), **sizes)

    def calculated_size_for(self, device_class):
        classes_that_impact = [device_class]+device_class.all_smaller
        for possible_class in reversed(classes_that_impact):
            try:
                return self.device_options[possible_class]
            except KeyError:
                pass
        return 0

    @classmethod
    def wraps_for_some_device_class(cls, all_options):
        return any([cls.wraps_for(device_class, all_options)
                   for device_class in DeviceClass.all_classes()])

    @classmethod
    def wraps_for(cls, device_class, all_options):
        return (cls.sum_sizes_for(device_class, all_options)) > 12

    @classmethod
    def sum_sizes_for(cls, device_class, all_options):
        total = 0
        for options in all_options:
            total += options.size.calculated_size_for(device_class)
            total += options.offsets.calculated_size_for(device_class)
        return total


class ColumnOptions:
    """Various options to change how a column should be displayed.

    :param name: The name of the column.
    :keyword size: The :class:`ResponsiveSize` of the column.
    :keyword offsets: A :class:`ResponsiveSize` representing extra space before the column.
    :keyword vertical_align: An :class:`Alignment` stating how this column should be aligned vertically in its container.

    .. versionadded:: 4.0

    """
    @arg_checks(size=IsInstance(ResponsiveSize, allow_none=True),
                offsets=IsInstance(ResponsiveSize, allow_none=True),
                vertical_align=IsInstance(Alignment, allow_none=True))
    def __init__(self, name, size=None, offsets=None, vertical_align=None):
        self.name = name
        self.size = size or ResponsiveSize(xs=True)
        self.offsets = offsets or ResponsiveSize()
        self.vertical_align = vertical_align or Alignment()


class ColumnLayout(Layout):
    """A Layout that divides an element into a number of columns.

    Each positional argument passed to the constructor defines a
    column. Columns are added to the element using this Layout in the
    order they are passed to the constructor. Columns can also be
    added to the Widget later, by calling
    :meth:`ColumnLayout.add_column`.

    Each such column-defining argument to the constructor is a tuple
    of which the first element is the column name, and the second an
    instance of :class:`ColumnOptions`. Besides the size of the column,
    other adjustments can be made via :class:`ColumnOptions`.

    You can also pass the column name only (no tuple) in which case
    a default :class:`ColumnOptions` will be used.

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

    By default, if you specify smaller column sizes for larger devices,
    but omit specifying a size for extra small (xs) devices, columns for xs
    devices are full width and thus stacked.

    .. versionchanged:: 4.0
       Each item in column_definitions can be just a string (the column name) or a tuple mapping a name to a :class:`ColumnOptions`.

    """
    def __init__(self, *column_definitions):
        super().__init__()
        if not all([isinstance(column_definition, (str, ColumnOptions)) for column_definition in column_definitions]):
            raise ProgrammerError('All column definitions are expected be either a ColumnOptions object of a column name, got %s' % str(column_definitions))
        self.added_column_definitions = []
        self.add_slots = False
        self.add_gutters = True
        self.alignment = Alignment()
        self.content_justification = ContentJustification()
        self.columns = OrderedDict()  #: A dictionary containing the added columns, keyed by column name.
        self.column_definitions = OrderedDict()
        for column_definition in column_definitions:
            if isinstance(column_definition, str):
                name, options = column_definition, ColumnOptions(column_definition)
            else:
                name, options = column_definition.name, column_definition
            self.column_definitions[name] = options

    def with_slots(self):
        """Returns a copy of this ColumnLayout which will additionally add a Slot inside each added column,
           named for that column.
        """
        copy_with_slots = copy.deepcopy(self)
        copy_with_slots.add_slots = True
        return copy_with_slots

    def without_gutters(self):
        """Returns a copy of this ColumnLayout which will not display whitespace between columns.

           .. versionadded:: 4.0
        """
        copy_without_gutters = copy.deepcopy(self)
        copy_without_gutters.add_gutters = False
        return copy_without_gutters

    @arg_checks(content_justification=IsInstance(ContentJustification))
    def with_justified_content(self, content_justification):
        """Returns a copy of this ColumnLayout with justification options set on it.

           .. versionadded:: 4.0
        """
        copy_with_content_justification = copy.deepcopy(self)
        copy_with_content_justification.content_justification = content_justification
        return copy_with_content_justification

    @arg_checks(vertical_alignment=IsInstance(Alignment))
    def with_vertical_alignment(self, vertical_alignment):
        """Returns a copy of this ColumnLayout with the column alignment options set on it.

           .. versionadded:: 4.0
        """
        copy_with_alignment = copy.deepcopy(self)
        copy_with_alignment.alignment = vertical_alignment
        return copy_with_alignment

    def customise_widget(self):
        for name, options in self.column_definitions.items():
            self.add_column(options.name, size=options.size, offsets=options.offsets, vertical_align=options.vertical_align)
        self.widget.append_class('row')
        if not self.add_gutters:
            self.widget.append_class('no-gutters')
        self.alignment.add_css_classes(self.widget)
        self.content_justification.add_css_classes(self.widget)

    def add_clearfix(self, column_options):
        clearfix = self.widget.add_child(Div(self.view))
        clearfix.append_class('clearfix')
        wrapping_classes = [device_class for device_class in DeviceClass.all_classes()
                            if ResponsiveSize.wraps_for(device_class, self.added_column_definitions + [column_options])]
        if wrapping_classes:
            device_class = wrapping_classes[0]
            if device_class.one_smaller:
                clearfix.append_class(device_class.one_smaller.as_combined_css_class(['hidden'], []))
        return clearfix

    def add_column(self, name, size=None, offsets=None, vertical_align=None, column_widget=None):
        """Called to add a column with given options.

        :param name: (See :class:`ColumnOptions`)
        :keyword size: (See :class:`ColumnOptions`)
        :keyword offsets: (See :class:`ColumnOptions`)
        :keyword vertical_align: (See :class:`ColumnOptions`)
        :keyword column_widget: If given, this Widget is added as the column instead of a Div (the default).

        .. versionchanged:: 4.0
           Changed to create a named column with all possible options.
        """
        column_options = ColumnOptions(name, size=size, offsets=offsets, vertical_align=vertical_align)
        if ResponsiveSize.wraps_for_some_device_class(self.added_column_definitions+[column_options]):
            self.add_clearfix(column_options)

        column = self.widget.add_child(column_widget or Div(self.view))

        column_options.size.add_css_classes(column, prefix='col')
        column_options.offsets.add_css_classes(column, prefix='offset')
        column_options.vertical_align.add_css_classes(column)

        self.added_column_definitions.append(column_options)
        self.columns[column_options.name] = column
        column.append_class('column-%s' % column_options.name)
        if self.add_slots:
            column.add_child(Slot(self.view, column_options.name))
        return column

