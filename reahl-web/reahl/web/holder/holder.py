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
"""

.. sidebar:: Behind the scenes

   This module uses `Holder.js <http://imsky.github.io/holder/>`_ to
   provide its functionality.

.. versionadded:: 3.2

Generate images on the fly.


"""
from __future__ import print_function, unicode_literals, absolute_import, division
import six

from collections import OrderedDict

from reahl.component.exceptions import ProgrammerError

from reahl.web.fw import Url
from reahl.web.ui import Img


class Theme(OrderedDict):
    def __init__(self):
        super(Theme, self).__init__()


class PredefinedTheme(Theme):
    """There are a few named, :class:`PredefinedTheme`\s you can choose from to
    control the look of a :class:`Placeholder` image.

    :param theme_name: One of: 'sky', 'vine', 'lava', 'gray', 'industrial', or 'social'.
    """
    def __init__(self, theme_name):
        super(PredefinedTheme, self).__init__()

        self['theme'] = theme_name


class CustomTheme(Theme):
    """A :class:`CustomTheme` allows one to control all the details of
    what a :class:`Placeholder` should look like.

    :keyword bg: The background-colour (a string in CSS notation)
    :keyword fg: The foreground-colour (a string in CSS notation)
    :keyword text_size: The size of generated text (an int, denoted in pts)
    :keyword text_font: The name of the font to use for generated text.
    :keyword text_align: How to align the generated text (one of 'left' or 'right')
    :keyword line_wrap: A ratio (line length to image width) at which generated text should wrap.
    :keyword outline: Draws a border and diagonals in the image.
    """
    def __init__(self, bg=None, fg=None, text_size=None, text_font=None, text_align=None, line_wrap=None, outline=None):

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
    """A :class:`PlaceholderImage` is an image generated on the client browser using SVG.

    :param view: (See :class:`~reahl.web.fw.Widget`)
    :param x: The width of the image (defaults to pixels, can be a string using CSS notation).
    :param y: The height of the image (defaults to pixels, can be a string using CSS notation).
    :keyword alt: Text to be displayed when the browser cannot handle images.
    :keyword text: Text to be generated on the image itself.
    :keyword theme: A :class:`PredefinedTheme` or :class:`CustomTheme` to control what the image should look like.
    """
    def __init__(self, view, x, y, alt=None, text=None, theme=None):

        super(PlaceholderImage, self).__init__(view, alt=alt)
        image_url = Url('holder.js/%sx%s' % (x, y))
        options = theme or Theme()
        if text is not None:
            options['text'] = text
        image_url.set_query_from(options)
        self.set_attribute('data-src', str(image_url))






