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
Layout tools based on Pure (http://purecss.io/)
"""
from __future__ import print_function, unicode_literals, absolute_import, division

from collections import OrderedDict
from fractions import Fraction

from reahl.web.fw import Layout

from reahl.web.ui import Panel, Header, Footer, Slot


class UnitSize(object):
    def __init__(self, default=None, sm=None, md=None, lg=None, xl=None):
        self.default = default
        self.sm = sm
        self.md = md
        self.lg = lg
        self.xl = xl

    def as_dict(self):
        return dict(self.__dict__)


class ColumnLayout(Layout):
    def __init__(self, *column_definitions):
        super(ColumnLayout, self).__init__()
        self.columns = OrderedDict()
        self.column_sizes = OrderedDict()
        for column_definition in column_definitions:
            if isinstance(column_definition, tuple):
                name, fractions = column_definition
            else:
                name, fractions = column_definition, UnitSize()
            self.column_sizes[name] = fractions

    def customise_widget(self):
        self.widget.append_class('pure-g')
        for name, unit_size in self.column_sizes.items():
            panel = self.add_column(Slot(self.view, name), unit_size=unit_size)
            self.columns[name] = panel
            panel.append_class('column-%s' % name)

    def add_column(self, widget, unit_size=None):
        unit_size = unit_size or UnitSize()
        unit = self.widget.add_child(Panel(self.view))

        for label, value in unit_size.as_dict().items():
            if label == 'default':
                unit.append_class(self.fraction_css_class('pure-u', unit_size.default) if unit_size.default else 'pure-u')
            elif value:
                unit.append_class(self.fraction_css_class('pure-u-%s' % label, value))

        unit.add_child(widget)
        return unit

    def fraction_css_class(self, prefix, fraction_string):
        fraction = Fraction(fraction_string)
        return '%s-%s-%s' % (prefix,  fraction.numerator, fraction.denominator)


class PageColumnLayout(Layout):
    def __init__(self, *column_definitions):
        super(PageColumnLayout, self).__init__()
        self.document_layout = ColumnLayout(*column_definitions)
        self.header = None
        self.contents = None
        self.footer = None
        self.document = None

    def customise_widget(self): 
        self.document = self.widget.body.add_child(Panel(self.view))
        self.document.set_id('doc')
        
        self.header = self.document.add_child(Header(self.view))
        self.header.add_child(Slot(self.view, 'header'))
        self.header.set_id('hd')

        self.contents = self.document.add_child(Panel(self.view).use_layout(self.document_layout))
        self.contents.set_id('bd')
        self.contents.set_attribute('role', 'main')
        
        self.footer = self.document.add_child(Footer(self.view))
        self.footer.add_child(Slot(self.view, 'footer'))
        self.footer.set_id('ft')

    @property
    def columns(self):
        return self.contents.layout.columns









