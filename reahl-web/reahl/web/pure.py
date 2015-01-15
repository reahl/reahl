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


class GridLayout(Layout):
    def customise_widget(self):
        self.widget.append_class('pure-g')

    def add_unit(self, widget, size=None):
        size = size or UnitSize()
        unit = self.widget.add_child(Panel(self.view))

        for label, value in size.as_dict().items():
            if label == 'default':
                unit.append_class(self.fraction_css_class('pure-u', size.default) if size.default else 'pure-u')
            elif value:
                unit.append_class(self.fraction_css_class('pure-u-%s' % label, value))

        unit.add_child(widget)
        return widget

    def fraction_css_class(self, prefix, fraction_string):
        fraction = Fraction(fraction_string)
        return '%s-%s-%s' % (prefix,  fraction.numerator, fraction.denominator)


class PageColumnLayout(Layout):
    def __init__(self, *column_definitions):
        super(PageColumnLayout, self).__init__()
        self.body_layout = ColumnLayout(*column_definitions)
        self.body = None

    def customise_widget(self): 
        self.body = self.widget.body
        self.body.using_layout(self.body_layout)
        self.header.set_id('hd')
        self.body.layout.contents.set_id('bd')
        self.footer.set_id('ft')

    @property
    def header(self):
        return self.body.layout.header
        
    @property
    def footer(self):
        return self.body.layout.footer

    @property
    def columns(self):
        return self.body.layout.columns


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
        self.header = self.widget.add_child(Header(self.view))
        self.header.add_child(Slot(self.view, 'header'))
        
        self.contents = self.widget.add_child(Panel(self.view).using_layout(GridLayout()))
        for name, size in self.column_sizes.items():
            panel = self.contents.layout.add_unit(Panel(self.view), size=size)
            slot = panel.add_child(Slot(self.view, name))
            self.columns[name] = panel

        self.footer = self.widget.add_child(Footer(self.view))
        self.footer.add_child(Slot(self.view, 'footer'))





