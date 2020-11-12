# Copyright 2015-2020 Reahl Software Services (Pty) Ltd. All rights reserved.
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

Generate images on the fly.


"""

from collections import OrderedDict

from reahl.web.fw import Url
from reahl.web.ui import Img, HTMLAttributeValueOption


class Theme(OrderedDict):
    def __init__(self):
        super().__init__()


class PredefinedTheme(Theme):
    """There are a few named, :class:`PredefinedTheme`\s you can choose from to
    control the look of a :class:`PlaceholderImage` .

    :param theme_name: One of: 'sky', 'vine', 'lava', 'gray', 'industrial', or 'social'.
    """
    def __init__(self, theme_name):
        super().__init__()
        theme_name_option = HTMLAttributeValueOption(theme_name, theme_name is not None,
                                                     constrain_value_to=['sky', 'vine', 'lava', 'gray', 'industrial', 'social'])
        self['theme'] = theme_name_option.as_html_snippet()


class CustomTheme(Theme):
    """A :class:`CustomTheme` allows one to control all the details of
    what a :class:`PlaceholderImage` should look like.

    :keyword bg: The background-colour (a string in CSS notation)
    :keyword fg: The foreground-colour (a string in CSS notation)
    :keyword text_size: The size of generated text (an int, denoted in pts)
    :keyword text_font: The name of the font to use for generated text.
    :keyword text_align: How to align the generated text (one of 'left' or 'right')
    :keyword line_wrap: A ratio (line length to image width) at which generated text should wrap.
    :keyword outline: Draws a border and diagonals in the image.
    """
    def __init__(self, bg=None, fg=None, text_size=None, text_font=None, text_align=None, line_wrap=None, outline=None):

        super().__init__()

        if bg is not None:
            self['bg'] = bg
        if fg is not None:
            self['fg'] = fg
        if text_size is not None:
            self['size'] = str(text_size)
        if text_font is not None:
            self['font'] = text_font
        if text_align is not None:
            text_align_option = HTMLAttributeValueOption(text_align,  text_align is not None,
                                                         constrain_value_to=['left', 'right'])
            self['align'] = text_align_option.as_html_snippet()
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

        super().__init__(view, alt=alt)
        image_url = Url('holder.js/%sx%s' % (x, y))
        options = theme or Theme()
        image_url.set_query_from(options)
        if text is not None:  
            # Our query string will url-escape text. Text often has spaces 
            # that would now become +. Holder does not do the reverse, so 
            # we have to add the text as an un-escaped query string argument 
            image_url = '%s%stext=%s' % (str(image_url), '?' if not options else '&', text)
        self.set_attribute('data-src', str(image_url))






