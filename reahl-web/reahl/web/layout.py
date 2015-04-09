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
"""

from collections import OrderedDict
from collections.abc import Mapping

from reahl.web.fw import Layout
from reahl.web.ui import Div

class ResponsiveSize(Mapping):
    def __init__(self, **sizes):
        self.sizes = {size_name: size_value for (size_name, size_value) in sizes.items() if size_value}

    def __getitem__(self, item):
        return self.sizes.__getitem__(item)
        
    def __iter__(self):
        return self.sizes.__iter__()
        
    def __len__(self):
        return self.sizes.__len__()
        
        
class ColumnLayout(Layout):
    def __init__(self, *column_definitions):
        super(ColumnLayout, self).__init__()
        self.columns = OrderedDict()  #: A dictionary containing the added columns, keyed by column name.
        self.column_sizes = OrderedDict()
        for column_definition in column_definitions:
            if isinstance(column_definition, tuple):
                name, size = column_definition
            else:
                name, size = column_definition, ResponsiveSize()
            self.column_sizes[name] = size

    def customise_widget(self):
        for name, size in self.column_sizes.items():
             column = self.add_column(size)
             self.columns[name] = column
             column.append_class('column-%s' % name)

    def add_column(self, size):
        return self.widget.add_child(Div(self.view))



