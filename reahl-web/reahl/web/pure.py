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

from fractions import Fraction

from reahl.web.fw import Layout

from reahl.web.ui import Panel


class PureGridLayout(Layout):
    def initialise_widget(self, widget):
        super(PureGridLayout, self).initialise_widget(widget)
        self.widget.append_class('pure-g')

    def add_unit(self, widget, default=None, sm=None, md=None, lg=None, xl=None):
        unit = self.widget.add_child(Panel(self.view))
        unit.append_class(self.fraction_css_class('pure-u', default) if default else 'pure-u')
        
        for label, value in [('sm', sm), ('md', md), ('lg', lg), ('xl', xl)]:
            if value:
                unit.append_class(self.fraction_css_class('pure-u-%s' % label, value))
        unit.add_child(widget)
        return widget

    def fraction_css_class(self, prefix, fraction_string):
        fraction = Fraction(fraction_string)
        return '%s-%s-%s' % (prefix,  fraction.numerator, fraction.denominator)


