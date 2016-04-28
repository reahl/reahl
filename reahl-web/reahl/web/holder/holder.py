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

from collections import OrderedDict

from reahl.component.exceptions import ProgrammerError

from reahl.web.fw import Url
from reahl.web.ui import Img


class Theme(OrderedDict):
    """A :class:`Theme` is used as argument to :class:`Placeholder` that influences what the placeholder will look like.
        Refer: https://github.com/imsky/holder
    """
    def __init__(self):
        super(Theme, self).__init__()


class PredefinedTheme(Theme):
    """
        :param theme_name:
    """
    def __init__(self, theme_name):
        super(PredefinedTheme, self).__init__()
        self['theme'] = theme_name


class CustomTheme(Theme):
    """
        :keyword bg:
        :keyword fg:
        :keyword text_size:
        :keyword text_font:
        :keyword text_align:
        :keyword outline:
        :keyword line_wrap:
    """
    def __init__(self, bg=None, fg=None, text_size=None, text_font=None, text_align=None, outline=None, line_wrap=None):

        super(CustomTheme, self).__init__()
        if text_align not in ['left', 'right', None]:
            raise ProgrammerError('text_align cannot be "%s", it should be one of %s' % (text_align, ','.join(['left', 'right', 'None'])))

        if bg is not None:
            self['bg'] = bg
        if fg is not None:
            self['fg'] = fg
        if text_size is not None:
            self['size'] = str(text_size)
        if text_font is not None:
            self['font'] = text_font
        if text_align is not None:
            self['align'] = text_align
        if outline is not None:
            self['outline'] = outline
        if line_wrap is not None:
            self['lineWrap'] = str(line_wrap)


class PlaceholderImage(Img):
    """A :class:`PlaceholderImage` renders image placeholders on the client side using SVG.
        Refer: https://github.com/imsky/holder

        :param x:
        :param y:
        :keyword alt:
        :keyword css_id:
        :keyword text:
        :keyword theme:
    """
    def __init__(self, view, x, y, alt=None, css_id=None, text=None, theme=None):

        super(PlaceholderImage, self).__init__(view, alt=alt, css_id=css_id)
        image_url = Url('holder.js/%sx%s' % (x, y))
        options = theme or Theme()
        if text is not None:
            options['text'] = text
        image_url.set_query_from(options)
        self.set_attribute('data-src', str(image_url))






