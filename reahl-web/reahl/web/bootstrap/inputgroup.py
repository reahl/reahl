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

from collections import OrderedDict
import copy

from reahl.web.fw import Layout, Widget
from reahl.web.ui import Form, Div, Header, Footer, Slot, HTML5Page, ValidationStateAttributes, AccessRightAttributes, \
                             Span, Input, TextInput, Label, TextNode, ButtonInput, P, WrappedInput

import reahl.web.layout
from reahl.component.exceptions import ProgrammerError, arg_checks, IsInstance
from reahl.web.ui import MenuItem


class InputGroup(WrappedInput):
    def __init__(self, prepend, input_widget, append):
        super(InputGroup, self).__init__(input_widget)

        self.div = self.add_child(Div(self.view))
        self.div.append_class('input-group')
        if prepend:
            self.add_as_addon(prepend)
        self.input_widget = self.div.add_child(input_widget)
        if append:
            self.add_as_addon(append)

    def add_as_addon(self, addon):
        if isinstance(addon, six.string_types):
            span = Span(self.view, text=addon)
        else:
            span = Span(self.view)
            span.add_child(addon)
        span.append_class('input-group-addon')
        return self.div.add_child(span)







