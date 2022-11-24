# Copyright 2015-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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



import webob

from reahl.tofu import Fixture
from reahl.tofu.pytestsupport import with_fixtures

from reahl.web.fw import Widget
from reahl.web.ui import Img
from reahl.web.bootstrap.carousel import Carousel

from reahl.web_dev.fixtures import WebFixture
from reahl.component_dev.test_i18n import LocaleContextStub


class CarouselFixture(Fixture):
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


@with_fixtures(WebFixture)
def test_carousel_basics(web_fixture):
    """A Carousel contains all the right classes and contents to act as a Bootstrap Carousel component."""

    widget = Carousel(web_fixture.view, 'my_carousel_id')

    [main_div] = widget.children

    # The main div
    assert main_div.get_attribute('id') == 'my_carousel_id'
    assert main_div.get_attribute('class') == 'carousel slide'

    [indicator_list, carousel_inner, left_control, right_control] = main_div.children

    # Indicators
    assert indicator_list.get_attribute('class') == 'carousel-indicators'

    # Inner (container of the images)
    assert carousel_inner.get_attribute('class') == 'carousel-inner'

    # Controls
    def check_control(control, action, label):
        assert control.get_attribute('class') == 'carousel-control-%s' % action
        assert control.get_attribute('role') == 'button'
        assert control.get_attribute('data-slide') == action

        [icon, text] = control.children
        assert icon.get_attribute('class') == 'carousel-control-%s-icon' % action
        assert icon.get_attribute('aria-hidden') == 'true'

        assert text.children[0].value == label
        assert text.get_attribute('class') == 'sr-only'

    check_control(left_control, 'prev', 'Previous')
    check_control(right_control, 'next', 'Next')


@with_fixtures(WebFixture)
def test_i18n(web_fixture):
    """User-visible labels are internationalised."""

    with LocaleContextStub(locale='af') as context:
        context.config = web_fixture.config
        context.session = web_fixture.context.session
        context.request = webob.Request.blank('/', charset='utf8')

        widget = Carousel(web_fixture.view, 'my_carousel_id')

        [main_div] = widget.children
        [indicator_list, carousel_inner, left_control, right_control] = main_div.children

        def check_control(control, label):
            [icon, text] = control.children
            assert text.children[0].value == label

        check_control(left_control, 'Vorige')
        check_control(right_control, 'Volgende')


@with_fixtures(WebFixture, CarouselFixture)
def test_carousel_has_options(web_fixture, carousel_fixture):
    """Constructor allows you to set certain customizing options"""

    carousel = Carousel(web_fixture.view, 'my_carousel_id', interval=1000, pause='hover', wrap=True, keyboard=True)
    main_div = carousel_fixture.get_main_div_for(carousel)

    assert main_div.get_attribute('data-interval') == '1000'
    assert main_div.get_attribute('data-pause') == 'hover'
    assert main_div.get_attribute('data-wrap') == 'true'
    assert main_div.get_attribute('data-keyboard') == 'true'


@with_fixtures(WebFixture, CarouselFixture)
def test_adding_items_to_carousel(web_fixture, carousel_fixture):
    """Images can be added to a Carousel."""

    fixture = carousel_fixture

    carousel = Carousel(web_fixture.view, 'my_carousel_id', show_indicators=True)
    main_div = fixture.get_main_div_for(carousel)
    [indicator_list, carousel_inner, left_control, right_control] = main_div.children

    # Initially, no items or indicators are present
    assert carousel_inner.children == []
    assert fixture.carousel_indicators_present(carousel)
    assert fixture.get_indicator_list_for(carousel) == []

    image = Img(web_fixture.view)
    added_item = carousel.add_slide(image)

    # A carousel item was added for the image
    [carousel_item] = carousel_inner.children
    assert carousel_item is added_item
    assert 'carousel-item' in carousel_item.get_attribute('class')

    [actual_image] = carousel_item.children
    assert actual_image is image

    # An indicator was added for the item
    [indicator] = fixture.get_indicator_list_for(carousel)

    assert indicator.get_attribute('data-target') == '#my_carousel_id'
    assert indicator.get_attribute('data-slide-to') == '0'


@with_fixtures(WebFixture, CarouselFixture)
def test_active_state_of_items(web_fixture, carousel_fixture):
    """The first item added is marked as active, and also its corresponding indicator."""

    fixture = carousel_fixture

    carousel = Carousel(web_fixture.view, 'my_carousel_id')
    carousel.add_slide(Img(web_fixture.view))
    carousel.add_slide(Img(web_fixture.view))

    main_div = fixture.get_main_div_for(carousel)
    [indicator_list, carousel_inner, left_control, right_control] = main_div.children

    #only the first item is active
    [carousel_item_1, carousel_item_2] = carousel_inner.children
    assert carousel_item_1.get_attribute('class') == 'active carousel-item'
    assert carousel_item_2.get_attribute('class') == 'carousel-item'

    #only the first indicator is active
    [indicator_0, indicator_1] = fixture.get_indicator_list_for(carousel)

    assert indicator_0.get_attribute('class') == 'active'
    assert not indicator_1.has_attribute('class')
    assert indicator_0.get_attribute('data-slide-to') == '0'
    assert indicator_1.get_attribute('data-slide-to') == '1'



@with_fixtures(WebFixture, CarouselFixture)
def test_item_indicators_are_optional(web_fixture, carousel_fixture):
    """With show_indicators=False, indicators are not added when adding items."""
    fixture = carousel_fixture

    carousel = Carousel(web_fixture.view, 'my_carousel_id', show_indicators=False)

    assert not fixture.carousel_indicators_present(carousel)

    carousel.add_slide(Img(web_fixture.view))

    #after adding the item, indicators shouldn't appear
    assert not fixture.carousel_indicators_present(carousel)



@with_fixtures(WebFixture)
def test_adding_items_with_captions(web_fixture):
    """A Widget can be supplied to be used caption for an added image."""

    carousel = Carousel(web_fixture.view, 'my_carousel_id')

    caption_widget = Widget(web_fixture.view)
    carousel_item = carousel.add_slide(Img(web_fixture.view), caption_widget=caption_widget)

    [image, div_containing_caption] = carousel_item.children
    assert div_containing_caption.get_attribute('class') == 'carousel-caption'

    [actual_caption_widget] = div_containing_caption.children
    assert actual_caption_widget is caption_widget


@with_fixtures(WebFixture)
def test_check_classes_added_for_images(web_fixture):
    """A Widget can be supplied to be used caption for an added image."""
    carousel = Carousel(web_fixture.view, 'my_carousel_id')

    img_widget = Img(web_fixture.view)
    carousel.add_slide(img_widget)
    assert img_widget.get_attribute('class') == 'd-block w-100'
