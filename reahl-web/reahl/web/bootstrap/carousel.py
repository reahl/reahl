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
.. versionadded:: 3.2

Carousel presents a slideshow of Widgets with captions on each slide.


"""
from __future__ import print_function, unicode_literals, absolute_import, division

import six
from reahl.web.fw import Widget, Url
from reahl.web.ui import HTMLAttributeValueOption
from reahl.web.bootstrap.ui import Div, A, Span, Li, Ol
from reahl.component.i18n import Translator

_ = Translator('reahl-web')


class Slide(Div):
    def __init__(self, view, image, caption_widget, index):
        super(Slide, self).__init__(view)
        self.index = index
        self.append_class('carousel-item')
        self.add_child(image)
        if self.is_active:
            self.append_class('active')

        if caption_widget:
            self.add_child(self.create_caption(caption_widget))

    @property
    def is_active(self):
        return self.index == 0

    def create_caption(self, caption_widget):
        div = Div(self.view)
        div.append_class('carousel-caption')
        div.add_child(caption_widget)
        return div


class Carousel(Widget):
    """A Widget that appears as having multiple panels of content of which
    only one panel is visible at a time. The visible panel is
    exchanged for another panel of content when prompted or
    automatically, at regular intervals, by visually sliding the new
    panel into position thus creating a slideshow effect.

    :param view: (See :class:`~reahl.web.fw.Widget`)
    :param css_id: ((See :class:`~reahl.web.ui.HTMLElement`)
    :keyword show_indicators: If True (the default), includes indicators showing the number of slides and which one is visible.
    :keyword interval: The number (an int) of milliseconds to delay between cycling content. If not given (the default), the Carousel will not cycle automatically.
    :keyword pause: If not None, a string stating when to pause the cycling. Currently only 'hover' is supported.
    :keyword wrap: If True, the Carousel cycles contiuously, else it stops at the last slide.
    :keyword keyboard:If True, the Carousel reacts to keyboard events.

    """
    def __init__(self, view, css_id, show_indicators=True, interval=5000, pause='hover', wrap=True, keyboard=True):
        super(Carousel, self).__init__(view)
        self.carousel_panel = self.add_child(Div(view, css_id=css_id))
        self.carousel_panel.append_class('carousel')
        self.carousel_panel.append_class('slide')
        self.carousel_panel.set_attribute('data-ride', 'carousel')

        self.carousel_panel.set_attribute('data-interval', six.text_type(interval))
        pause_option = HTMLAttributeValueOption(pause or 'false', True, constrain_value_to=['hover','false'])
        self.carousel_panel.set_attribute('data-pause', pause_option.as_html_snippet())
        self.carousel_panel.set_attribute('data-wrap', 'true' if wrap else 'false')
        self.carousel_panel.set_attribute('data-keyboard', 'true' if keyboard else 'false')

        self.show_indicators = show_indicators
        if self.show_indicators:
            self.indicator_list = self.carousel_panel.add_child(self.create_indicator_list())
        self.inner = self.carousel_panel.add_child(self.create_inner())
        self.items = []

        self.add_control(left=True)
        self.add_control()

    def create_inner(self):
        inner = Div(self.view)
        inner.append_class('carousel-inner')
        inner.set_attribute('role', 'listbox')
        return inner

    def add_slide(self, image, caption_widget=None):
        """
        Adds a Slide for the given image.

        :param image: An image to display (See also :class:`~reahl.web.holder.holder.PlaceholderImage`)
        :param caption_widget: The :class:`~reahl.web.fw.Widget` to use as caption for the slide.
        :return:
        """
        item = self.inner.add_child(Slide(self.view, image, caption_widget, len(self.items)))

        self.items.append(item)

        if self.show_indicators:
            self.add_indicator_for(item)

        return item

    @property
    def url(self):
        return Url('#%s' % self.carousel_panel.css_id)

    def add_control(self, left=False):
        control_a = self.carousel_panel.add_child(A(self.view, self.url))
        control_a.append_class('carousel-control')
        control_a.append_class('left' if left else 'right')
        control_a.set_attribute('role', 'button')
        control_a.set_attribute('data-slide', 'prev' if left else 'next')

        span_icon = control_a.add_child(Span(self.view))
        span_icon.append_class('icon-%s' % ('prev' if left else 'next'))
        span_icon.set_attribute('aria-hidden', 'true')

        span_text = control_a.add_child(Span(self.view, text=_('Previous') if left else _('Next')))
        span_text.append_class('sr-only')

        return control_a

    def create_indicator_list(self):
        indicators = Ol(self.view)
        indicators.append_class('carousel-indicators')
        return indicators

    def add_indicator_for(self, item):
        li = self.indicator_list.add_child(Li(self.view))
        li.set_attribute('data-target', six.text_type(self.url))
        li.set_attribute('data-slide-to', '%s' % item.index)
        if item.is_active:
            li.append_class('active')
        return li
