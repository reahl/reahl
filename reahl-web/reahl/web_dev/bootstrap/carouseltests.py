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

from __future__ import print_function, unicode_literals, absolute_import, division

import six

import webob

from reahl.tofu import vassert, scenario, expected, test
from reahl.stubble import stubclass

from reahl.web.fw import Widget, WebExecutionContext
from reahl.web.ui import Img
from reahl.web_dev.fixtures import WebFixture
from reahl.web.bootstrap.carousel import Carousel




class CarouselFixture(WebFixture):
    def get_main_div_for(self, carousel):
        return carousel.children[0]

    def get_indicator_list_for(self, carousel):
        ol = self.get_main_div_for(carousel).children[0]
        assert self.is_carousel_indicator(ol)
        return ol.children

    def is_carousel_indicator(self, element):
        return 'carousel-indicators' in element.get_attribute('class')

    def carousel_indicators_present(self, carousel):
        return any([self.is_carousel_indicator(child) 
                    for child in self.get_main_div_for(carousel).children])


@test(CarouselFixture)
def carousel_basics(fixture):
    """A Carousel contains all the right classes and contents to act as a Bootstrap Carousel component."""

    widget = Carousel(fixture.view, 'my_carousel_id')

    [main_div] = widget.children

    # The main div
    vassert( main_div.get_attribute('id') == 'my_carousel_id' )
    vassert( main_div.get_attribute('class') == 'carousel slide' )

    [indicator_list, carousel_inner, left_control, right_control] = main_div.children

    # Indicators
    vassert( indicator_list.get_attribute('class') == 'carousel-indicators' )

    # Inner (container of the images)
    vassert( carousel_inner.get_attribute('class') == 'carousel-inner' )
    vassert( carousel_inner.get_attribute('role') == 'listbox' )

    # Controls
    def check_control(control, position, action, label):
        vassert( control.get_attribute('class') == 'carousel-control %s' % position )
        vassert( control.get_attribute('role') == 'button' )
        vassert( control.get_attribute('data-slide') == action )

        [icon, text] = control.children
        vassert( icon.get_attribute('class') == 'icon-%s' % action )
        vassert( icon.get_attribute('aria-hidden') == 'true' )
        
        vassert( text.children[0].value == label)
        vassert( text.get_attribute('class') == 'sr-only')

    check_control(left_control, 'left', 'prev', 'Previous')
    check_control(right_control, 'right', 'next', 'Next')


@test(CarouselFixture)
def i18n(fixture):
    """User-visible labels are internationalised."""
    @stubclass(WebExecutionContext)
    class AfrikaansContext(WebExecutionContext):
        request = webob.Request.blank('/', charset='utf8')
        @property
        def interface_locale(self):
            return 'af'

    with AfrikaansContext():
        widget = Carousel(fixture.view, 'my_carousel_id')

        [main_div] = widget.children
        [indicator_list, carousel_inner, left_control, right_control] = main_div.children

        def check_control(control, label):
            [icon, text] = control.children
            vassert( text.children[0].value == label)

        check_control(left_control, 'Vorige')
        check_control(right_control, 'Volgende')



@test(CarouselFixture)
def carousel_has_options(fixture):
    """Constructor allows you to set certain customizing options"""

    carousel = Carousel(fixture.view, 'my_carousel_id', interval=1000, pause='hover', wrap=True, keyboard=True)
    main_div = fixture.get_main_div_for(carousel)

    vassert( main_div.get_attribute('data-interval') == '1000' )
    vassert( main_div.get_attribute('data-pause') == 'hover' )
    vassert( main_div.get_attribute('data-wrap') == 'true' )
    vassert( main_div.get_attribute('data-keyboard') == 'true' )

    #when options are 'empty'
    carousel = Carousel(fixture.view, 'my_carousel_id')
    main_div = fixture.get_main_div_for(carousel)

    vassert( not main_div.has_attribute('data-interval') )
    vassert( not main_div.has_attribute('data-pause') )
    vassert( not main_div.has_attribute('data-wrap') )
    vassert( not main_div.has_attribute('data-keyboard') )


@test(CarouselFixture)
def adding_items_to_carousel(fixture):
    """Images can be added to a Carousel."""

    carousel = Carousel(fixture.view, 'my_carousel_id', show_indicators=True)
    main_div = fixture.get_main_div_for(carousel)
    [indicator_list, carousel_inner, left_control, right_control] = main_div.children

    # Initially, no items or indicators are present
    vassert( carousel_inner.children == [])
    vassert( fixture.carousel_indicators_present(carousel) )
    vassert( fixture.get_indicator_list_for(carousel) == [] )

    image = Img(fixture.view)
    added_item = carousel.add_item(image)

    # A carousel item was added for the image
    [carousel_item] = carousel_inner.children
    vassert( carousel_item is added_item )
    vassert( 'carousel-item' in carousel_item.get_attribute('class') )

    [actual_image] = carousel_item.children
    vassert( actual_image is image )

    # An indicator was added for the item
    [indicator] = fixture.get_indicator_list_for(carousel)

    vassert( indicator.get_attribute('data-target') == '#my_carousel_id' )
    vassert( indicator.get_attribute('data-slide-to') == '0' )


@test(CarouselFixture)
def active_state_of_items(fixture):
    """The first item added is marked as active, and also its corresponding indicator."""
    
    carousel = Carousel(fixture.view, 'my_carousel_id')
    carousel.add_item(Img(fixture.view))
    carousel.add_item(Img(fixture.view))

    main_div = fixture.get_main_div_for(carousel)
    [indicator_list, carousel_inner, left_control, right_control] = main_div.children
    
    #only the first item is active
    [carousel_item_1, carousel_item_2] = carousel_inner.children
    vassert( carousel_item_1.get_attribute('class') == 'active carousel-item' )
    vassert( carousel_item_2.get_attribute('class') == 'carousel-item' )

    #only the first indicator is active
    [indicator_0, indicator_1] = fixture.get_indicator_list_for(carousel)

    vassert( indicator_0.get_attribute('class') == 'active' )
    vassert( not indicator_1.has_attribute('class') )
    vassert( indicator_0.get_attribute('data-slide-to') == '0' )
    vassert( indicator_1.get_attribute('data-slide-to') == '1' )


@test(CarouselFixture)
def item_indicators_are_optional(fixture):
    """With show_indicators=False, indicators are not added when adding items."""
    carousel = Carousel(fixture.view, 'my_carousel_id', show_indicators=False)

    vassert( not fixture.carousel_indicators_present(carousel) )

    carousel.add_item(Img(fixture.view))

    #after adding the item, indicators shouldn't appear
    vassert( not fixture.carousel_indicators_present(carousel) )


@test(CarouselFixture)
def adding_items_with_captions(fixture):
    """A Widget can be supplied to be used caption for an added image."""
    carousel = Carousel(fixture.view, 'my_carousel_id')

    caption_widget = Widget(fixture.view)
    carousel_item = carousel.add_item(Img(fixture.view), caption_widget=caption_widget)

    [image, div_containing_caption] = carousel_item.children
    vassert( div_containing_caption.get_attribute('class') == 'carousel-caption' )

    [actual_caption_widget] = div_containing_caption.children
    vassert( actual_caption_widget is caption_widget )

