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

.. versionadded:: 3.1

"""
from __future__ import print_function, unicode_literals, absolute_import, division

from collections import OrderedDict
from fractions import Fraction

from reahl.web.fw import Layout
import reahl.web.layout

from reahl.web.ui import Panel, Header, Footer, Slot, HTML5Page
from reahl.component.exceptions import ProgrammerError, arg_checks, IsInstance
from reahl.component.decorators import deprecated


class UnitSize(reahl.web.layout.ResponsiveSize):
    """Represents a set of relative sizes to be used for an element depending 
       on the size of the user's device, as defined by the Pure library.

       The Pure library sizes elements relative to their parent using
       fractions (1/2 or 3/4 or 1 are examples).  The size of an
       element relative to its parent can also vary, depending on the
       size of the device a user is using to view your web
       application.

       This class lets one specify the size to use for different sizes of
       display device.

       Sizes should be given as fractions in strings, such as the literal:

       .. code-block:: python

          UnitSize(sm='1', md='1/2', xl='1/4')

       Sizes can be given for sizes of device using the keyword arguments:

       :keyword default: If no other size is specified, or if the screen being used is smaller than the sizes given, this size is used.
       :keyword sm: For small screens (or larger).
       :keyword md: For medium-sized screen (or larger).
       :keyword lg: For large devices (or larger).
       :keyword xl: For extra-large devices (or larger).

       .. note::

          If a size is specified for `md`, for example, it will be used
          on all screens that are medium-sized or larger and Pure will fall
          back to using the `default` size for smaller screens.
    """
    def __init__(self, default=None, sm=None, md=None, lg=None, xl=None):
        super(UnitSize, self).__init__(default=default, sm=sm, md=md, lg=lg, xl=xl)


class ColumnLayout(reahl.web.layout.ColumnLayout):
    """A Layout that uses the Pure library to divides an element into a number of columns.

       .. seealso::

          :class:`~reahl.web.layout.ColumnLayout`

       To define a column without specifying a size, just pass a
       string containing the column name.
       
       To define a column with a given UnitSize, pass a tuple of which
       the first element is the column name, and the second an
       instance of :class:`UnitSize`

       .. code-block:: python

          ColumnLayout('column_a', ('column_b', UnitSize(default='1/2')))

       .. admonition:: Styling
       
          Each column added is a <div> which has has the css class
          'column-<column_name>' where <column_name> is the name as
          specified to the constructor.

    """
    def customise_widget(self):
        super(ColumnLayout, self).customise_widget()
        self.widget.append_class('pure-g')

    def add_column(self, unit_size=None):
        """Add an un-named column, optionally with the given :class:`UnitSize`.

           :keyword unit_size: The sizes to use for the column.

           Returns a :class:`reahl.web.ui.Panel` representing the added column.
        """
        unit_size = unit_size or UnitSize()
        unit = super(ColumnLayout, self).add_column(size=unit_size)

        if not unit_size:
            unit.append_class('pure-u')
        else:
            for label, value in unit_size.items():
                if label == 'default':
                    unit.append_class(self.fraction_css_class('pure-u', value))
                else:
                    unit.append_class(self.fraction_css_class('pure-u-%s' % label, value))

        return unit

    def fraction_css_class(self, prefix, fraction_string):
        fraction = Fraction(fraction_string)
        return '%s-%s-%s' % (prefix,  fraction.numerator, fraction.denominator)


@deprecated('Instead, please use reahl.web.layout.PageLayout combined with your choice of Layout for its contents', '3.2')
class PageColumnLayout(reahl.web.layout.PageLayout):
    """A Layout that provides the main layout for an :class:`reahl.web.ui.HTML5Page`.

       A PageColumnLayout adds a header and footer area to an HTML5Page, as well as 
       a number of columns between the header and footer area, as specified by the
       arguments to its constructor.
    
       All of these contents are also wrapped in a
       :class:`reahl.web.ui.Panel`, which is handy for styling.

       Specifying columns work exactly as for :class:`ColumnLayout`.

       Inside each added column, a :class:`reahl.web.ui.Slot` is added that is named
       after the column. 

       .. admonition:: Styling
       
          Adds a <div id="doc"> to the <body> of the page, which contains:

           - a <header id="hd">
           - a <div id="contents">
           - a <footer id="ft">

         The div#contents element is further set up as with a :class:`ColumnLayout` using the
         arguments passed as `column_definition`\ s.
    """
    def __init__(self, *column_definitions):
        super(PageColumnLayout, self).__init__(contents_layout=ColumnLayout(*column_definitions).with_slots())

    @property
    def columns(self):
        """A dictionary containing the added columns, keyed by column name."""
        return self.contents.layout.columns







