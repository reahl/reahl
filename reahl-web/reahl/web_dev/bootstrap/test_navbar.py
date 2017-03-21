# Copyright 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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
import time


from reahl.tofu import vassert, scenario, expected, test, Fixture

from reahl.webdev.tools import XPath
from reahl.web_dev.fixtures import WebFixture, WebBasicsMixin
from reahl.component.exceptions import IsInstance

from reahl.web.fw import Bookmark
from reahl.web.bootstrap.ui import A, Div, P, TextNode, Span
from reahl.web.bootstrap.forms import Form
from reahl.web.bootstrap.navbar import Navbar, NavbarLayout, ResponsiveLayout
from reahl.web.bootstrap.navs import Nav

from reahl.component.exceptions import ProgrammerError


class NavbarFixture(WebFixture):
    def new_navbar(self):
        return Navbar(self.view)

    def new_navbar_with_layout(self):
        return self.navbar.use_layout(NavbarLayout())

    def new_bookmarks(self):
        return [Bookmark('', '/one', 'One')]

    def new_nav(self):
        return Nav(self.view).with_bookmarks(self.bookmarks)

    def new_form(self):
        return Form(self.view, 'myform')

    def new_textnode(self):
        return TextNode(self.view, 'mytext')


@test(NavbarFixture)
def navbar_basics(fixture):
    """A typical Navbar is created by using its layout to add some brand text, a nav and form in it."""

    navbar = Navbar(fixture.view).use_layout(NavbarLayout())

    navbar.layout.set_brand_text('Brandy')
    navbar.layout.add(fixture.nav)
    navbar.layout.add(fixture.form)

    [brand, nav, form] = navbar.children[0].children
    [ul] = nav.children

    # The Navbar itself
    vassert( navbar.children[0].tag_name == 'nav' )
    vassert( 'navbar' in navbar.children[0].get_attribute('class').split(' ') )

    # The added contents
    vassert( isinstance(brand, A) )
    vassert( 'navbar-brand' in brand.get_attribute('class') )

    vassert( 'navbar-nav' in ul.get_attribute('class') )

    vassert( isinstance(form, Form))
    vassert( 'form-inline' in form.get_attribute('class') )


class LayoutScenarios(NavbarFixture):
    @scenario
    def fixed_top(self):
        self.layout = NavbarLayout(fixed_to='fixed-top')
        self.expected_css_class = 'fixed-top'

    @scenario
    def fixed_bottom(self):
        self.layout = NavbarLayout(fixed_to='fixed-bottom')
        self.expected_css_class = 'fixed-bottom'

    @scenario
    def sticky_top(self):
        self.layout = NavbarLayout(fixed_to='sticky-top')
        self.expected_css_class = 'sticky-top'

    @scenario
    def default(self):
        self.layout = NavbarLayout()
        self.expected_css_class = None


@test(LayoutScenarios)
def navbar_can_have_layout(fixture):
    """NavbarLayout is used to define the placement of a Navbar."""

    widget = Navbar(fixture.view).use_layout(fixture.layout)

    [navbar] = widget.children
    all_classes = ['fixed-bottom', 'fixed-top', 'sticky-top']
    if fixture.expected_css_class:
        vassert( fixture.expected_css_class in navbar.get_attribute('class').split(' ') )
    
    for not_expected_class in [i for i in all_classes if i != fixture.expected_css_class]:
        vassert( not_expected_class not in navbar.get_attribute('class').split(' ') )


@test(NavbarFixture)
def customised_colour_scheme(fixture):
    """A ColourScheme is used to determine link colours and/or optionally a standard bootstrap background color."""

    layout = NavbarLayout(colour_theme='light', bg_scheme='inverse')
    widget = Navbar(fixture.view).use_layout(layout)

    [navbar] = widget.children

    vassert( 'navbar-light' in navbar.get_attribute('class') )
    vassert( 'bg-inverse' in navbar.get_attribute('class') )


@test(NavbarFixture)
def adding_brand_widget(fixture):
    """Brand content can also be added as a Widget, instead of only text."""

    navbar_widget = fixture.navbar.use_layout(NavbarLayout())
    custom_brand = Div(fixture.view)
    navbar_widget.layout.set_brand(custom_brand)

    [navbar] = navbar_widget.children
    [actual_brand_widget] = navbar.children

    vassert( actual_brand_widget is custom_brand )
    vassert( 'navbar-brand' in actual_brand_widget.get_attribute('class') )


@test(NavbarFixture)
def adding_other_than_form_nav_or_text_is_not_allowed(fixture):
    """Only Navs, Forms and Text may be added."""

    navbar = fixture.navbar.use_layout(NavbarLayout())
    not_a_form_or_nav = Div(fixture.view)

    with expected(IsInstance):
        navbar.layout.add(not_a_form_or_nav)

    # Case: Form
    navbar = fixture.new_navbar().use_layout(NavbarLayout())
    navbar.layout.add(fixture.form)
    [added_widget] = navbar.children[0].children
    vassert( added_widget is fixture.form )
    vassert( 'form-inline' in fixture.form.get_attribute('class') )

    # Case: Nav
    navbar = fixture.new_navbar().use_layout(NavbarLayout())
    vassert( 'navbar-nav' not in fixture.nav.html_representation.get_attribute('class').split(' ') )
    navbar.layout.add(fixture.nav)
    [added_widget] = navbar.children[0].children
    vassert( added_widget is fixture.nav )
    vassert( 'navbar-nav' in fixture.nav.html_representation.get_attribute('class').split(' ') )

    # Case: Text
    navbar = fixture.new_navbar().use_layout(NavbarLayout())
    navbar.layout.add(fixture.textnode)
    [added_widget] = navbar.children[0].children
    [textnode] = added_widget.children
    vassert( isinstance(added_widget, Span) )
    vassert( textnode is fixture.textnode )
    vassert( 'navbar-text' in added_widget.get_attribute('class').split(' ') )



@test(NavbarFixture)
def test_navbar_with_centered_contents(fixture):
    """Contents of a Navbar appears centered when center_contents is set to True"""

    navbar_widget = fixture.navbar
    navbar_widget.use_layout(NavbarLayout(center_contents=True))
    navbar_widget.layout.set_brand_text('Brandy') #adding something to illustrate the structure change

    [navbar] = navbar_widget.children
    [centering_div] = navbar.children
    [brand_widget] = centering_div.children

    vassert( 'container' in centering_div.get_attribute('class') )
    vassert( 'navbar-brand' in brand_widget.get_attribute('class') )


class CenteredResponsiveLayoutScenarios(NavbarFixture):

    @scenario
    def non_collapse_brand(self):
        self.collapse_brand = False

    @scenario
    def collapse_brand(self):
        self.collapse_brand = True


@test(CenteredResponsiveLayoutScenarios)
def test_responsive_navbar_with_centered_contents_brand_collapse(fixture):
    """Contents of a Navbar appears centered when center_contents is set to True"""

    navbar_widget = fixture.navbar
    navbar_widget.set_id('my_navbar_id')
    navbar_widget.use_layout(ResponsiveLayout('md', center_contents=True,
                                              collapse_brand_with_content=fixture.collapse_brand))
    navbar_widget.layout.set_brand_text('Brandy') #adding something to illustrate the structure change

    [navbar] = navbar_widget.children
    if not fixture.collapse_brand:
        [toggle, brand_widget, centering_div] = navbar.children
    else:
        [toggle, centering_div] = navbar.children
        [collapsable] = centering_div.children
        [brand_widget] = collapsable.children
        vassert( 'navbar-collapse' in collapsable.get_attribute('class'))

    vassert( 'navbar-toggler' in toggle.get_attribute('class'))
    vassert( 'container' in centering_div.get_attribute('class') )
    vassert( 'navbar-brand' in brand_widget.get_attribute('class') )


class NavbarToggleFixture(Fixture, WebBasicsMixin):

    def is_expanded(self, locator):
        return self.driver_browser.is_visible(locator) and \
               self.driver_browser.does_element_have_attribute(locator, 'aria-expanded', value='true') and\
               self.driver_browser.does_element_have_attribute(locator, 'class', value='collapse in') 

    def panel_is_expanded(self):
        return self.is_expanded(XPath.paragraph_containing('Peek-A-Boo'))

    def panel_is_visible(self):
        return self.driver_browser.is_visible(XPath.paragraph_containing('Peek-A-Boo'))

    def xpath_to_locate_toggle(self):
        return XPath('//span[contains(@class,"navbar-toggler-icon")]')

    def new_MainWidget(self):
        fixture = self
        class MainWidget(Div):
            def __init__(self, view):
                super(MainWidget, self).__init__(view)

                navbar = Navbar(view)
                navbar.use_layout(NavbarLayout())
                fixture.element_to_collapse = P(view, text='Peek-A-Boo', css_id='my_id')
                navbar.layout.add_toggle(fixture.element_to_collapse)

                self.add_child(fixture.element_to_collapse)
                self.add_child(navbar)
        return MainWidget

    def new_wsgi_app(self):
        return super(NavbarToggleFixture, self).new_wsgi_app(enable_js=True,
                                                             child_factory=self.MainWidget.factory())


@test(NavbarFixture)
def navbar_toggle_basics(fixture):
    """The default bootstrap toggle icon is used when no text is given"""

    element_to_collapse = Div(fixture.view, css_id='my_id')
    toggle = fixture.navbar_with_layout.layout.add_toggle(element_to_collapse, text=None)

    [toggle_span] = toggle.children

    vassert( isinstance(toggle_span, Span) )
    vassert( 'navbar-toggler-icon' in toggle_span.get_attribute('class') )
    vassert( 'navbar-toggler' in toggle.get_attribute('class').split() )


@test(NavbarFixture)
def navbar_toggle_customised(fixture):
    """The text on a toggle that hides an element is customisable"""

    element_to_collapse = Div(fixture.view, css_id='my_id')
    toggle = fixture.navbar_with_layout.layout.add_toggle(element_to_collapse, text='≎')

    [toggle_text_node] = toggle.children

    vassert( '≎' == toggle_text_node.value )


@test(NavbarToggleFixture)
def navbar_toggle_collapses_html_element(fixture):
    """You can add a toggle to the navbar that hides another element on the page."""

    fixture.reahl_server.set_app(fixture.wsgi_app)
    browser = fixture.driver_browser
    browser.open('/')

    # case: by default, the element to hide is not visible
    vassert( browser.wait_for_not(fixture.panel_is_visible) )

    # case: clicking on the toggle, causes the panel to appear
    browser.click(fixture.xpath_to_locate_toggle())
    browser.wait_for(fixture.panel_is_expanded)

    # case: clicking on the toggle again, causes the panel to disappear
    time.sleep(0.5)
    browser.click(fixture.xpath_to_locate_toggle())
    browser.wait_for_not(fixture.panel_is_visible)


@test(NavbarFixture)
def navbar_toggle_requires_target_id(fixture):
    """To be able to hide an element, it is required to have an id"""

    navbar = fixture.navbar
    navbar.use_layout(NavbarLayout())
    element_without_id = P(fixture.view, text='Peek-A-Boo')

    def check_ex(ex):
        vassert( 'has no css_id set' in six.text_type(ex))

    with expected(ProgrammerError, test=check_ex):
        navbar.layout.add_toggle(element_without_id)


@test(NavbarFixture)
def responsive_navbar_basics(fixture):
    """A ResponsiveLayout hides its Navbar when the viewport becomes smaller than a given device size"""
    navbar_widget = fixture.navbar
    navbar_widget.set_id('my_navbar_id')
    navbar_widget.use_layout(ResponsiveLayout('sm'))

    [navbar] = navbar_widget.children
    [toggle, collapse_div] = navbar.children

    vassert( 'navbar-toggler' in toggle.get_attribute('class') )
    vassert( 'button' in toggle.get_attribute('type') )
    vassert( 'collapse' in toggle.get_attribute('data-toggle') )
    vassert( 'my_navbar_id' in toggle.get_attribute('data-target') )

    vassert( 'my_navbar_id' in collapse_div.get_attribute('id') )
    vassert( 'collapse' in collapse_div.get_attribute('class').split() )
    vassert( 'navbar-collapse' in collapse_div.get_attribute('class').split() )

    vassert( 'navbar-toggleable-xs' in navbar.get_attribute('class') )


class ToggleAlignmentScenarios(NavbarFixture):
    @scenario
    def aligned_right(self):
        self.layout = ResponsiveLayout('sm', toggle_button_alignment='right')
        self.expected_css_class = 'navbar-toggler-right'

    @scenario
    def aligned_left(self):
        self.layout = ResponsiveLayout('sm', toggle_button_alignment='left')
        self.expected_css_class = 'navbar-toggler-left'


@test(ToggleAlignmentScenarios)
def responsive_navbar_toggle_alignment(fixture):
    """A ResponsiveLayout hides its Navbar when the viewport becomes smaller than a given device size"""
    navbar_widget = fixture.navbar
    navbar_widget.set_id('my_navbar_id')
    navbar_widget.use_layout(fixture.layout)

    [navbar] = navbar_widget.children
    [toggle, collapse_div] = navbar.children

    vassert( fixture.expected_css_class in toggle.get_attribute('class') )


class BrandCollapseScenarios(NavbarFixture):

    @scenario
    def brand_does_not_collapse_with_content(self):
        self.brand_collapse = False

    @scenario
    def brand_does_collapse_with_content(self):
        self.brand_collapse = True


@test(BrandCollapseScenarios)
def test_brand_may_be_collapsed_with_toggleable_content(fixture):
    """Brands may be collapse along with the other content."""

    responsive_navbar = fixture.navbar
    responsive_navbar.set_id('my_navbar_id')
    responsive_navbar.use_layout(ResponsiveLayout('md',
                                                  collapse_brand_with_content=fixture.brand_collapse))
    responsive_navbar.layout.add(fixture.nav)

    brand_widget = Div(fixture.view)
    responsive_navbar.layout.set_brand(brand_widget)

    if fixture.brand_collapse:
        [toggle, collapse_div] = responsive_navbar.children[0].children
        [brand, navbar_nav] = collapse_div.children
    else:
        [toggle, brand, collapse_div] = responsive_navbar.children[0].children
        [navbar_nav] = collapse_div.children

    vassert( brand is brand_widget )
    vassert( 'navbar-collapse' in collapse_div.get_attribute('class') )
    vassert( 'navbar-nav' in navbar_nav.html_representation.get_attribute('class') )
    vassert( 'navbar-toggler' in toggle.get_attribute('class') )