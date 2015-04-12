# Copyright 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
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
"""
Utilities to deal with layout.

.. versionadded:: 3.2

"""

import copy
from collections import OrderedDict
from collections.abc import Mapping

from reahl.component.exceptions import arg_checks, IsInstance
from reahl.web.fw import Layout
from reahl.web.ui import Div, HTML5Page, Slot, Header, Footer

class ResponsiveSize(Mapping):
    """Represents a set of relative sizes to be used for an element depending on the size of the user's device.

       This class lets one specify the size to use for different sizes of display device.

       Each kwarg of the constructor is a size and the name of the kwarg is the device class for which
       that size applies.

       Values for sizes and device classes are as defined by the underlying layout library.

       .. versionadded:: 3.2

    """
    def __init__(self, **sizes):
        self.sizes = {size_name: size_value for (size_name, size_value) in sizes.items() if size_value}

    def __getitem__(self, item):
        return self.sizes.__getitem__(item)
        
    def __iter__(self):
        return self.sizes.__iter__()
        
    def __len__(self):
        return self.sizes.__len__()
        
        
class ColumnLayout(Layout):
    """A Layout that divides an element into a number of columns.

       Each argument passed to the constructor defines a
       column. Columns are added to the element using this Layout in
       the order they are passed to the constructor. Columns can also 
       be added to the Widget later, by calling :meth:`ColumnLayout.add_column`.

       To define a column with a given :class:`ResponsiveSize`, pass a tuple of which
       the first element is the column name, and the second an
       instance of :class:`ResponsiveSize`.

       .. versionadded:: 3.2

    """
    def __init__(self, *column_definitions):
        super(ColumnLayout, self).__init__()
        self.add_slots = False
        self.columns = OrderedDict()  #: A dictionary containing the added columns, keyed by column name.
        self.column_sizes = OrderedDict()
        for column_definition in column_definitions:
            if isinstance(column_definition, tuple):
                name, size = column_definition
            else:
                name, size = column_definition, ResponsiveSize()
            self.column_sizes[name] = size

    def with_slots(self):
        """Returns a copy of this ColumnLayout which will additionally add a Slot inside each added column,
           named for that column.
        """
        copy_with_slots = copy.deepcopy(self)
        copy_with_slots.add_slots = True
        return copy_with_slots

    def customise_widget(self):
        for name, size in self.column_sizes.items():
             column = self.add_column(size)
             self.columns[name] = column
             column.append_class('column-%s' % name)
             if self.add_slots:
                 column.add_child(Slot(self.view, name))
                 
    def add_column(self, size):
        """Add an un-named column, with the given :class:`ResponsiveSize`.

           :keyword size: The sizes to use for the column.

           Returns a :class:`reahl.web.ui.Div` representing the added column.
        """
        return self.widget.add_child(Div(self.view))



class PageLayout(Layout):
    """A PageLayout adds a header and footer area to an :class:`reahl.web.ui.HTML5Page`, as well as 
       a content area between the header and footer areas.
    
       All of these contents are also wrapped in a
       :class:`reahl.web.ui.Div`, which is handy for styling.

       .. admonition:: Styling
       
          Adds a <div id="doc"> to the <body> of the page, which contains:

           - a <header id="hd">
           - a <div id="contents">
           - a <footer id="ft">

         The div#contents element is further set up to use the :class:`Layout` passed
         to the constructor.

       .. versionadded:: 3.2

    """
    def __init__(self, contents_layout=None):
        super(PageLayout, self).__init__()
        self.header = None    #: The :class:`reahl.web.ui.Header` of the page.
        self.contents = None  #: The :class:`reahl.web.ui.Div` containing the contents.
        self.contents_layout = contents_layout #: A :class:`reahl.web.fw.Layout` to be used for the contents div of the page.
        self.footer = None    #: The :class:`reahl.web.ui.Footer` of the page.
        self.document = None  #: The :class:`reahl.web.ui.Div` containing the entire page.

    @arg_checks(widget=IsInstance(HTML5Page))
    def apply_to_widget(self, widget):
        super(PageLayout, self).apply_to_widget(widget)

    def customise_widget(self):
        self.document = self.widget.body.add_child(Div(self.view))
        self.document.set_id('doc')
        
        self.header = self.document.add_child(Header(self.view))
        self.header.add_child(Slot(self.view, 'header'))
        self.header.set_id('hd')

        self.contents = self.document.add_child(Div(self.view))
        if self.contents_layout:
            self.contents.use_layout(self.contents_layout)

        self.contents.set_id('bd')
        self.contents.set_attribute('role', 'main')
        
        self.footer = self.document.add_child(Footer(self.view))
        self.footer.add_child(Slot(self.view, 'footer'))
        self.footer.set_id('ft')

