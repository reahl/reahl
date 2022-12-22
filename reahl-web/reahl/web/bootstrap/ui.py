# Copyright 2015-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from reahl.component.exceptions import ProgrammerError
from reahl.component.i18n import Catalogue

import reahl.web.ui
# These are imported here for convenience so they can be imported from reahl.web.bootstrap.ui:
from reahl.web.ui import A, Article, Body, Br, Div, Footer, H, Head, Header, Img, \
    Li, Link, LiteralHTML, Meta, Nav, Ol, OptGroup, P, Small, RunningOnBadge, Slot, Span, TextNode, \
    Title, Ul, WrappedInput, FieldSet, Legend, HTMLAttributeValueOption, Widget, HTMLElement, HTMLWidget, \
    Br, Hr

_ = Catalogue('reahl-web')


class Alert(Div):
    """A message box meant to alert the user of some message.

    See also: :class:`Badge`.

    :param view: (See :class:`reahl.web.fw.Widget`)
    :param message_or_widget: Message text or a Widget to display inside the Alert.
    :param severity: One of 'primary', 'secondary', 'success', 'info', 'warning', 'danger', 'light', 'dark'
        to indicate the color scheme for the Alert.

    """
    def __init__(self, view, message_or_widget, severity):
        super().__init__(view)
        severity_option = HTMLAttributeValueOption(severity, severity, prefix='alert', 
                                                   constrain_value_to=['primary', 'secondary',
                                                                       'success', 'info', 'warning', 'danger',
                                                                       'light', 'dark'])
        child_widget = message_or_widget
        if isinstance(message_or_widget, str):
            child_widget = TextNode(view, message_or_widget)
        self.add_child(child_widget)
        self.append_class('alert')
        self.append_class(severity_option.as_html_snippet())
        self.set_attribute('role', 'alert') 


class Badge(Span):
    """An inline, visually highlighted message.

    See also: :class:`Alert`.

    :param view: (See :class:`reahl.web.fw.Widget`)
    :param message: The message for the badge.
    :param level: One of 'primary', 'secondary', 'success', 'info', 'warning', 'danger', 'light', 'dark' to indicate
                  the color scheme to be used for the Badge.
    :keyword pill: Defaults to False. If set to True the badge will look like a pill.
    """
    def __init__(self, view, message, level, pill=False):
        super().__init__(view)
        severity_option = HTMLAttributeValueOption(level, level, prefix='badge',
                                                   constrain_value_to=['primary', 'secondary',
                                                                       'success', 'info', 'warning', 'danger',
                                                                       'light', 'dark'])
        self.add_child(TextNode(view, message))
        self.append_class('badge')
        if pill:
            self.append_class('badge-pill')
        self.append_class(severity_option.as_html_snippet())
