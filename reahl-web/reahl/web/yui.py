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
Layout tools based on YUI
"""
from __future__ import print_function, unicode_literals, absolute_import, division

from reahl.web.ui import  Layout, YuiDoc
from reahl.component.decorators import memoized



class YUITwoColumnPageLayout(Layout):

    @property
    @memoized
    def yui_page(self):
        return self.widget.body.add_child(YuiDoc(self.widget.view, 'doc', 'yui-t2'))

    @property
    def footer(self):
        """The Panel used as footer area."""
        return self.yui_page.footer

    @property
    def header(self):
        """The Panel used as header area."""
        return self.yui_page.header

    @property
    def main_block(self):
        """The Panel used as main column."""
        return self.yui_page.main_block

    @property
    def secondary_block(self):
        """The Panel used as secondary column."""
        return self.yui_page.secondary_block
