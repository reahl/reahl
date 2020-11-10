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

Carousel presents a slideshow of Widgets with captions on each slide.


"""

from reahl.web.fw import Widget, Url
from reahl.web.ui import HTMLAttributeValueOption, HTMLElement, Img
from reahl.web.bootstrap.ui import Div, A, Span, Li, Ol, TextNode
from reahl.component.i18n import Catalogue

_ = Catalogue('reahl-web')


class Slide(Div):
    def __init__(self, view, widget, caption_widget, index):
        super().__init__(view)
        self.index = index
        self.append_class('carousel-item')
        self.add_child(widget)
        if self.is_active:
            self.append_class('active')

        if isinstance(widget, Img):
            widget.append_class('d-block')
            widget.append_class('w-100')

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
    """
    A Widget that appears as having multiple panels of content of which
    only one panel is visible at a time. The visible panel is
    exchanged for another panel of content when prompted or
    automatically, at regular intervals, by visually sliding the new
    panel into position thus creating a slideshow effect.

    :param view: (See :class:`~reahl.web.fw.Widget`)
    :param css_id: (See :class:`~reahl.web.ui.HTMLElement`)
    :keyword show_indicators: If True (the default), includes indicators showing the number of slides and which one is visible.
    :keyword interval: The number (an int) of milliseconds to delay between cycling content. If not given (the default), the Carousel will not cycle automatically.
    :keyword pause: If set to 'false', hovering over the carousel will not pause it. Another option, 'hover' is supported.
    :keyword wrap: If True, the Carousel cycles contiuously, else it stops at the last slide.
    :keyword keyboard: If True, the Carousel reacts to keyboard events.
    :keyword min_height: If given, force slides to be at least this high (useful to prevent
             resizing of the Carousel between slides that are unequal in height). The value 
             is an int denoting a height in terms of the size of the font of the contents (em). 
    """
    def __init__(self, view, css_id, show_indicators=True, interval=5000, pause='hover', wrap=True, keyboard=True, min_height=None):
        super().__init__(view)
        self.carousel_panel = self.add_child(Div(view, css_id=css_id))
        self.carousel_panel.append_class('carousel')
        self.carousel_panel.append_class('slide')
        self.carousel_panel.set_attribute('data-ride', 'carousel')

        self.carousel_panel.set_attribute('data-interval', str(interval))
        pause_option = HTMLAttributeValueOption(pause or 'false', True, constrain_value_to=['hover', 'false'])
        self.carousel_panel.set_attribute('data-pause', pause_option.as_html_snippet())
        self.carousel_panel.set_attribute('data-wrap', 'true' if wrap else 'false')
        self.carousel_panel.set_attribute('data-keyboard', 'true' if keyboard else 'false')
        if min_height:
            style = self.carousel_panel.add_child(HTMLElement(self.view, 'style', children_allowed=True))
            css_id = self.carousel_panel.css_id
            style.add_child(TextNode(self.view, '#%s .carousel-item { min-height: %sem; }' % (css_id, min_height)))

        self.show_indicators = show_indicators
        if self.show_indicators:
            self.indicator_list = self.carousel_panel.add_child(self.create_indicator_list())
        self.inner = self.carousel_panel.add_child(self.create_inner())
        self.slides = []

        self.add_control(previous=True)
        self.add_control()

    def create_inner(self):
        inner = Div(self.view)
        inner.append_class('carousel-inner')
        return inner

    def add_slide(self, widget, caption_widget=None):
        """
        Adds a Slide for the given :class:`~reahl.web.fw.Widget`.

        :param widget: A :class:`~reahl.web.fw.Widget` to display in this slide. (See also :class:`~reahl.web.holder.holder.PlaceholderImage`)
        :keyword caption_widget: The :class:`~reahl.web.fw.Widget` to use as caption for the slide.

        """
        slide = self.inner.add_child(Slide(self.view, widget, caption_widget, len(self.slides)))

        self.slides.append(slide)

        if self.show_indicators:
            self.add_indicator_for(slide)

        return slide

    @property
    def url(self):
        return Url('#%s' % self.carousel_panel.css_id)

    def add_control(self, previous=False):
        control_a = self.carousel_panel.add_child(A(self.view, self.url))
        control_a.append_class('carousel-control-prev' if previous else 'carousel-control-next')
        control_a.set_attribute('role', 'button')
        control_a.set_attribute('data-slide', 'prev' if previous else 'next')

        span_icon = control_a.add_child(Span(self.view))
        span_icon.append_class('carousel-control-%s-icon' % ('prev' if previous else 'next'))
        span_icon.set_attribute('aria-hidden', 'true')

        span_text = control_a.add_child(Span(self.view, text=_('Previous') if previous else _('Next')))
        span_text.append_class('sr-only')

        return control_a

    def create_indicator_list(self):
        indicators = Ol(self.view)
        indicators.append_class('carousel-indicators')
        return indicators

    def add_indicator_for(self, item):
        li = self.indicator_list.add_child(Li(self.view))
        li.set_attribute('data-target', str(self.url))
        li.set_attribute('data-slide-to', '%s' % item.index)
        if item.is_active:
            li.append_class('active')
        return li
