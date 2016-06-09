# Copyright 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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

This module houses stylised versions of very basic user interface
elements -- user interface elements that have a one-to-one
correspondence to HTML elements (or are of similar simplicity).



"""
from __future__ import print_function, unicode_literals, absolute_import, division

import six

from copy import copy

from reahl.component.exceptions import ProgrammerError, arg_checks, IsInstance
from reahl.component.i18n import Translator

import reahl.web.ui
from reahl.web.ui import A, Article, Body, Br, Div, Footer, H, Head, Header, Img, \
    Li, Link, LiteralHTML, Meta, Nav, Ol, OptGroup, P, RunningOnBadge, Slot, Span, TextNode, \
    Title, Ul, WrappedInput, FieldSet, Legend, HTMLAttributeValueOption

from reahl.web.bootstrap.grid import Container, ColumnLayout, ResponsiveSize


_ = Translator('reahl-web')


class HTML5Page(reahl.web.ui.HTML5Page):
    """A web page that may be used as the page of a web application. It ensures that everything needed by
       the framework (linked CSS and JavaScript, etc) is available on such a page.

       .. admonition:: Styling
       
          Renders as an HTML5 page with customised <head> and an empty <body>.
       
       :param view: (See :class:`reahl.web.fw.Widget`)
       :keyword title: (See :class:`reahl.web.ui.HTML5Page`)
       :keyword css_id: (See :class:`reahl.web.ui.HTMLElement`)
       
    """
    def __init__(self, view, title='$current_title', css_id=None):
        super(HTML5Page, self).__init__(view, title=title, css_id=css_id)

    def check_form_related_programmer_errors(self):
        super(HTML5Page, self).check_form_related_programmer_errors()
        self.check_grids_nesting()
        
    def check_grids_nesting(self):
        for widget, parents_set in self.parent_widget_pairs(set([])):
            if isinstance(widget.layout, ColumnLayout):
                if not any(isinstance(parent.layout, Container) for parent in parents_set):
                    raise ProgrammerError(('%s does not have a parent with Layout of type %s.' % (widget, Container))+\
                      ' %s has a ColumnLayout, and thus needs to have an anchestor with a Container Layout.' % widget)



class Alert(Div):
    """A message box meant to alert the user of some message.

    :param view: (See :class:`reahl.web.fw.Widget`)
    :param message: The message to display inside the Alert.
    :param severity: One of 'success', 'info', 'warning', 'danger' to indicate the color scheme to be used for the Alert.

    """
    def __init__(self, view, message, severity):
        super(Alert, self).__init__(view)
        severity_option = HTMLAttributeValueOption(severity, severity, prefix='alert', 
                                                   constrain_value_to=['success', 'info', 'warning', 'danger'])
        self.add_child(TextNode(view, message))
        self.append_class('alert')
        self.append_class(severity_option.as_html_snippet())
        self.set_attribute('role', 'alert')


