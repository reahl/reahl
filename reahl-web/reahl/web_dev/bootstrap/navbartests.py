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
import time


# brand link to home page of site, in correct language
# When collapsed, internal nav should stack like on bs3 examples

#collapse looks like a bootsrap component, not necessarily a navbar thing
#--- see things below scenarioify
#file upload multiple files
#dialog button and friends (popupA etc)
# PopupA - "Modal" in Bootstrap / or Popover / or Card?
#

#paged table
#reahl-domainui - bootstrap"ify" worklow, register user

#thhrow ProgrammerError instead of assertion

from reahl.tofu import vassert, scenario, expected, test, Fixture
from reahl.stubble import stubclass

from reahl.webdev.tools import XPath
from reahl.web_dev.fixtures import WebFixture, WebBasicsMixin

from reahl.web.fw import Bookmark

from reahl.web.bootstrap.navbar import Navbar, ColourScheme, NavbarLayout, ResponsiveLayout
from reahl.web.bootstrap.navs import Nav
from reahl.web.bootstrap.ui import A, Form, Div, P
from reahl.web.bootstrap.libraries import Bootstrap4, ReahlBootstrap4Additions

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



class LayoutScenarios(NavbarFixture):
    @scenario
    def fixed_top(self):
        self.layout = NavbarLayout(fixed_top=True)
        self.expected_css_class = 'navbar-fixed-top'

    @scenario
    def fixed_bottom(self):
        self.layout = NavbarLayout(fixed_bottom=True)
        self.expected_css_class = 'navbar-fixed-bottom'

    @scenario
    def full(self):
        self.layout = NavbarLayout(full=True)
        self.expected_css_class = 'navbar-full'

    @scenario
    def default(self):
        self.layout = NavbarLayout()
        self.expected_css_class = None


@test(LayoutScenarios)
def navbar_can_have_layout(fixture):
    """NavbarLayout is used to define the placement of a Navbar."""

    widget = Navbar(fixture.view).use_layout(fixture.layout)

    [navbar] = widget.children
    all_classes = ['navbar-fixed-bottom','navbar-fixed-top','navbar-full']
    if fixture.expected_css_class:
        vassert( fixture.expected_css_class in navbar.get_attribute('class').split(' ') )
    
    for not_expected_class in [i for i in all_classes if i != fixture.expected_css_class]:
        vassert( not_expected_class not in navbar.get_attribute('class').split(' ') )


@test(NavbarFixture)
def customised_colour_scheme(fixture):
    """A ColourScheme is used to determine link colours and/or optionally a standard bootstrap background color."""

    layout = NavbarLayout(colour_scheme=ColourScheme(colour_theme='light', bg_scheme='inverse'))
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


class SpecifyPlacementScenarios(NavbarFixture):
    @scenario
    def adding_left(self):
        self.side = 'left'

    @scenario
    def adding_right(self):
        self.side = 'right'


@test(SpecifyPlacementScenarios)
def adding_to_navbar_with_specific_placement(fixture):
    """Widgets can be added to a Navbar placed right or left in the NavBar."""
    navbar = fixture.navbar.use_layout(NavbarLayout())

    if fixture.side == 'left':
        added_widget = navbar.layout.add(fixture.nav, left=True)
    else:
        added_widget = navbar.layout.add(fixture.nav, right=True)

    [wrapping_div] = navbar.children[0].children

    vassert( 'pull-%s' % fixture.side in wrapping_div.get_attribute('class') )
    vassert( added_widget is fixture.nav )
    vassert( [added_widget] == wrapping_div.children )


@test(SpecifyPlacementScenarios)
def adding_to_navbar_placement_for_device(fixture):
    """Placement of an added Widget can be specified to apply below a certain device size only."""
    fixture.navbar.use_layout(NavbarLayout())

    if fixture.side == 'left':
        fixture.navbar.layout.add(fixture.nav, left='md')
    else:
        fixture.navbar.layout.add(fixture.nav, right='md')
    
    [wrapping_div] = fixture.navbar.children[0].children
    vassert( 'pull-md-%s' % fixture.side in wrapping_div.get_attribute('class') )


@test(NavbarFixture)
def adding_to_navbar_with_both_left_and_right_alignment_not_allowed(fixture):
    """You cannot place an added Widget to both left and right sides."""
    navbar = fixture.navbar.use_layout(NavbarLayout())

    def check_ex(ex):
        vassert( six.text_type(ex).startswith('You should specify left or right, not both'))

    with expected(AssertionError, test=check_ex):
        navbar.layout.add(fixture.nav, left=True, right=True)


@test(NavbarFixture)
def adding_other_than_form_or_nav_is_not_allowed(fixture):
    """Only Navs and Forms may be added."""

    navbar = fixture.navbar.use_layout(NavbarLayout())
    not_a_form_or_nav = Div(fixture.view)

    def check_ex(ex):
        vassert( six.text_type(ex).startswith('You may only add Navs or Forms to a Navbar'))

    with expected(AssertionError, test=check_ex):
        navbar.layout.add(not_a_form_or_nav)

    # Case: Form
    navbar = fixture.new_navbar().use_layout(NavbarLayout())
    navbar.layout.add(fixture.form)
    [added_widget] = navbar.children[0].children
    vassert( added_widget is fixture.form )

    # Case: Nav
    navbar = fixture.new_navbar().use_layout(NavbarLayout())
    vassert( 'navbar-nav' not in fixture.nav.html_representation.get_attribute('class').split(' ') )
    navbar.layout.add(fixture.nav)
    [added_widget] = navbar.children[0].children
    vassert( added_widget is fixture.nav )
    vassert( 'navbar-nav' in fixture.nav.html_representation.get_attribute('class').split(' ') )


@test(NavbarFixture)
def navbar_with_centered_contents(fixture):
    """Contents of a Navbar appears centered when center_contents is set to True"""

    navbar_widget = fixture.navbar
    navbar_widget.use_layout(NavbarLayout(center_contents=True))
    navbar_widget.layout.set_brand_text('Brandy') #adding something to illustrate the structure change

    [navbar] = navbar_widget.children
    [centering_div] = navbar.children
    [brand_widget] = centering_div.children

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
        return XPath('//button[contains(node(), "%s")]' % '☰')

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
    def new_webconfig(self):
        webconfig = super(NavbarToggleFixture, self).new_webconfig()
        webconfig.frontend_libraries.add(Bootstrap4())
        webconfig.frontend_libraries.add(ReahlBootstrap4Additions())
        return webconfig


@test(NavbarToggleFixture)
def navbar_toggle_collapses_html_element(fixture):
    """You can add a toggle to the navbar that hides another element on the page."""

    fixture.reahl_server.set_app(fixture.wsgi_app)
    browser = fixture.driver_browser
    browser.open('/')

    #case: by default, the element to hide is not visible
    vassert( browser.wait_for_not(fixture.panel_is_visible) )

    #case: clicking on the toggle, causes the panel to appear
    browser.click(fixture.xpath_to_locate_toggle())
    browser.wait_for(fixture.panel_is_expanded)

    #case: clicking on the toggle again, causes the panel to disappear
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
        vassert( 'you must set its css_id' in six.text_type(ex))

    with expected(AssertionError, test=check_ex):
        navbar.layout.add_toggle(element_without_id)


@test(NavbarFixture)
def navbar_toggle_customised(fixture):
    """The text on a toggle that hides an element is customisable"""

    element_to_collapse = Div(fixture.view, css_id='my_id')
    toggle = fixture.navbar_with_layout.layout.add_toggle(element_to_collapse, text='≎')

    [toggle_text_node] = toggle.children

    vassert( '≎' == toggle_text_node.value )


@test(NavbarFixture)
def responsive_navbar(fixture):
    """A ResponsiveLayout hides its Navbar when the viewport becomes smaller than a given device size"""
    navbar_widget = fixture.navbar
    navbar_widget.set_id('my_navbar_id')
    navbar_widget.use_layout(ResponsiveLayout('sm'))

    [navbar] = navbar_widget.children
    [toggle, collapse_div] = navbar.children

    vassert( 'navbar-toggler' in toggle.get_attribute('class') )
    vassert( 'hidden-sm-up' in toggle.get_attribute('class') )
    vassert( 'button' in toggle.get_attribute('type') )
    vassert( 'collapse' in toggle.get_attribute('data-toggle') )
    vassert( 'my_navbar_id' in toggle.get_attribute('data-target') )

    vassert( 'my_navbar_id' in collapse_div.get_attribute('id') )
    vassert( 'collapse' in collapse_div.get_attribute('class') )
    vassert( 'navbar-toggleable-xs' in collapse_div.get_attribute('class') )

