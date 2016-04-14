# Copyright 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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
Client-side popups and related utilities.

.. versionadded:: 3.2

"""
from __future__ import print_function, unicode_literals, absolute_import, division

import six
from reahl.component.i18n import Translator

import reahl.web.ui
from reahl.web.bootstrap.ui import A

_ = Translator('reahl-web')


class DialogButton(reahl.web.ui.DialogButton):
    def __init__(self, label):
        super(DialogButton, self).__init__(label)
        self.css_classes = []

    def append_class(self, css_class):
        self.css_classes.append(css_class)

    def as_jquery(self):
        return '"%s": function() { %s }' % (self.label, self.callback_js())


class CheckCheckboxButton(DialogButton):
    def __init__(self, label, checkbox):
        super(CheckCheckboxButton, self).__init__(label)
        self.checkbox_to_check = checkbox

    def callback_js(self):
        return '''$(%s).attr("checked", true);''' %  self.checkbox_to_check.jquery_selector



class PopupA(A):
    def __init__(self, view, target_bookmark, show_for_selector, close_button=True, css_id=None):
        super(PopupA, self).__init__(view, target_bookmark.href, target_bookmark.description, css_id=css_id)
        self.set_title(target_bookmark.description)
        self.title = target_bookmark.description
        self.append_class('reahl-bootstrappopupa')
        self.show_for_selector = show_for_selector
        self.buttons = []
        if close_button:
            self.add_button(DialogButton(_('Close')))

    def add_button(self, button):
        self.buttons.append(button)
        return button

    def buttons_as_jquery(self):
        return ', '.join([button.as_jquery() for button in self.buttons])

    @property
    def jquery_selector(self):
        return '"a.reahl-bootstrappopupa[href=\'%s\']"' % self.href

    def get_js(self, context=None):
        selector = self.contextualise_selector(self.jquery_selector, context)
        return ['$(%s).bootstrappopupa({showForSelector: "%s", buttons: { %s } , title: "%s" });' % \
              (selector, self.show_for_selector, self.buttons_as_jquery(), self.title)]


