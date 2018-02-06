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
.. versionadded:: 3.2

Client-side popups and related utilities.


"""
from __future__ import print_function, unicode_literals, absolute_import, division

import six
import json

from reahl.component.i18n import Translator

from reahl.web.bootstrap.ui import A
from reahl.web.bootstrap.forms import ButtonStyle, ButtonSize

_ = Translator('reahl-web')


class JsObject(object):
    def __init__(self, **attributes):
        self.attributes = attributes

    def as_html_snippet(self):
        return '{%s}' % (','.join(['%s: %s' % (name, self.translate_to_js(value)) 
                                   for name, value in self.attributes.items()]))

    def translate_to_js(self, value):
        if hasattr(value, 'as_html_snippet'):
            return value.as_html_snippet()
        return json.dumps(value)

    def __setitem__(self, key, value):
        self.attributes[key] = value

    def __getitem__(self, key):
        return self.attributes[key]


class JsFunction(object):
    def __init__(self, body_text='', *args):
        self.args = args
        self.body_text = body_text
        
    def as_html_snippet(self):
        return 'function(%s){%s}' % (','.join(self.args), self.body_text)


class CheckCheckboxScript(JsFunction):
    def __init__(self, checkbox):
        self.checkbox = checkbox
        selector = self.checkbox.jquery_selector
        body_text = '''$(%s).filter("input").attr("checked", true);$(%s).find("input").attr("checked", true);''' % \
                               (selector, selector)
        super(CheckCheckboxScript, self).__init__(body_text=body_text)


class JsBooleanOption(object):
    def __init__(self, attribute_name, boolean_value=False):
        self.attribute_name = attribute_name
        self.boolean_value = boolean_value

    def as_html_snippet(self):
        return '%s: %s' % (self.attribute_name, 'true' if self.boolean_value else 'false')


class PopupA(A):
    def __init__(self, view, target_bookmark, show_for_selector, dismiss_label=None, close_button=True,
                 center_vertically=False, css_id=None):
        super(PopupA, self).__init__(view, target_bookmark.href, target_bookmark.description, css_id=css_id)
        self.set_title(target_bookmark.description)
        self.title = target_bookmark.description
        self.append_class('reahl-bootstrappopupa')
        self.show_for_selector = show_for_selector
        self.buttons = JsObject()
        self.dismiss_label = dismiss_label
        self.center_vertically = JsBooleanOption('center_vertically', center_vertically)
        if dismiss_label is None:
            self.dismiss_label = _('Close')
        if close_button:
            self.add_js_button(_('Close'))

    def add_js_button(self, label, js_function=None, style=None, size=None):
        options = [ButtonStyle(style) if style else None, ButtonSize(size) if size else None]

        js_function = js_function or JsFunction()
        css_classes = [option.as_html_snippet() for option in options if option]
        self.buttons[label] = JsObject(function=js_function, css_classes=css_classes)
        return self.buttons[label]

    def buttons_as_jquery(self):
        return self.buttons.as_html_snippet()

    @property
    def jquery_selector(self):
        return '"a.reahl-bootstrappopupa[href=\'%s\']"' % self.href

    def get_js(self, context=None):
        selector = self.contextualise_selector(self.jquery_selector, context)
        return ['$(%s).bootstrappopupa({showForSelector: "%s", buttons: %s, title: "%s", dismiss_label: "%s", %s });' % \
              (selector, self.show_for_selector, self.buttons_as_jquery(), self.title,
               self.dismiss_label, self.center_vertically.as_html_snippet())]


