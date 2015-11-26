# Copyright 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from __future__ import print_function, unicode_literals, absolute_import, division
import six


from reahl.web.fw import Url
from reahl.web.ui import Img


class Theme(object):
    def __init__(self, bg=None, fg=None, text_size=None, text_font=None, text_align=None):
        assert text_align in ['left', 'right', None]
        self.bg = bg
        self.fg = fg
        self.text_size = text_size
        self.text_font = text_font
        self.text_align = text_align

    def as_options(self):
        options = {}
        if self.bg is not None:
            options['bg'] = self.bg
        if self.fg is not None:
            options['fg'] = self.fg
        if self.text_size is not None:
            options['size'] = str(self.text_size)
        if self.text_font is not None:
            options['font'] = self.text_font
        if self.text_align is not None:
            options['align'] = self.text_align
        return options
        

class PlaceholderImage(Img):
    def __init__(self, view, x, y, alt=None, css_id=None, text=None, theme=None):
        super(PlaceholderImage, self).__init__(view, alt=alt, css_id=css_id)
        image_url = Url('holder.js/%sx%s' % (x, y))
        options = (theme or Theme()).as_options()
        if text is not None:
            options['text'] = text
        image_url.set_query_from(options)
        self.set_attribute('data-src', str(image_url))






