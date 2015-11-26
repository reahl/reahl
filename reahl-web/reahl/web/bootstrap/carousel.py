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
Widgets and Layouts that provide an abstraction on top of Bootstrap (http://getbootstrap.com/)

.. versionadded:: 3.2

"""
from __future__ import print_function, unicode_literals, absolute_import, division

import six
from reahl.web.fw import Widget, Url
from reahl.web.ui import Div, A, Span, Li, Img, HTMLElement, Ol
from reahl.component.i18n import Translator

_ = Translator('reahl-web')


class CarouselItem(Div):
    def __init__(self, view, image, caption_widget, index):
        super(CarouselItem, self).__init__(view)
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
    def __init__(self, view, css_id, show_indicators=True, interval=None, pause=None, wrap=False, keyboard=False):
        super(Carousel, self).__init__(view)
        self.carousel_panel = self.add_child(Div(view, css_id=css_id))
        self.carousel_panel.append_class('carousel')
        self.carousel_panel.append_class('slide')
        self.carousel_panel.set_attribute('data-ride', 'carousel')
        if interval:
            self.carousel_panel.set_attribute('data-interval', six.text_type(interval))
        if pause:
            self.carousel_panel.set_attribute('data-pause', six.text_type(pause))
        if wrap:
            self.carousel_panel.set_attribute('data-wrap', 'true' if wrap else 'false')
        if keyboard:
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

    def add_item(self, image, caption_widget=None):
        item = self.inner.add_child(CarouselItem(self.view, image, caption_widget, len(self.items)))

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