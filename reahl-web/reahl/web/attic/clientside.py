# Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.component.i18n import Translator
from reahl.web.ui import A

_ = Translator('reahl-web')

#AppliedPendingMove: In future this class may be renamed to: reahl.web.attic.clientside:DialogButton
class DialogButton(object):
    def __init__(self, label):
        self.label = label

    def callback_js(self):
        return ''

    def as_jquery(self):
        return '"%s": function() { %s }' % (self.label, self.callback_js())


#AppliedPendingMove: In future this class may be renamed to: reahl.web.attic.clientside:CheckCheckboxButton
class CheckCheckboxButton(DialogButton):
    def __init__(self, label, checkbox):
        super(CheckCheckboxButton, self).__init__(label)
        self.checkbox_to_check = checkbox

    def callback_js(self):
        return '''$(%s).attr("checked", true);''' %  self.checkbox_to_check.jquery_selector


#AppliedPendingMove: In future this class may be renamed to: reahl.web.attic.clientside:PopupA
# Uses: reahl/web/reahl.popupa.js
class PopupA(A):
    # Implements:
    # http://blog.nemikor.com/category/jquery-ui/jquery-ui-dialog/
    # ... with buttons added
    def __init__(self, view, target_bookmark, show_for_selector, close_button=True, css_id=None):
        super(PopupA, self).__init__(view, target_bookmark.href, target_bookmark.description, css_id=css_id)
        self.set_title(target_bookmark.description)
        self.append_class('reahl-popupa')
        self.show_for_selector = show_for_selector
        self.buttons = []
        if close_button:
            self.add_button(DialogButton(_('Close')))

    def add_button(self, button):
        self.buttons.append(button)

    def buttons_as_jquery(self):
        return ', '.join([button.as_jquery() for button in self.buttons])

    @property
    def jquery_selector(self):
        return '"a.reahl-popupa[href=\'%s\']"' % self.href

    def get_js(self, context=None):
        selector = self.contextualise_selector(self.jquery_selector, context)
        return ['$(%s).popupa({showForSelector: "%s", buttons: { %s }  });' % \
              (selector, self.show_for_selector, self.buttons_as_jquery())]