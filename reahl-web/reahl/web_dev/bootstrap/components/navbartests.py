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



# brand link to home page of site, in correct language
# When collapsed, internal nav should stack like on bs3 examples

#see things below scenarioify
#file upload multiple files
#dialog button and friends (popupA etc)
#paged table
#reahl-domainui - bootstrap"ify" worklow, register user


from reahl.tofu import vassert, scenario, expected, test
from reahl.stubble import stubclass

from reahl.web.fw import Bookmark
from reahl.web_dev.fixtures import WebFixture
from reahl.web.bootstrap.navbar import Navbar, ColourScheme, NavbarLayout, ResponsiveLayout
from reahl.web.bootstrap.navs import Nav
from reahl.web.bootstrap.ui import A, Form, InlineFormLayout, TextInput, Button, Div

from reahl.component.modelinterface import exposed, Field, Event
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
        class MyDomainObject(object):
            @exposed
            def fields(self, fields):
                fields.search_text = Field(label=' ')
            @exposed
            def events(self, events):
                events.search = Event(label='Search')

        domain_object = MyDomainObject()
        class MyForm(Form):
            def __init__(self, view):
                super(MyForm, self).__init__(view, 'myform')
                self.use_layout(InlineFormLayout())
                self.layout.add_input(TextInput(self, domain_object.fields.search_text), help_text='')
                self.define_event_handler(domain_object.events.search)
                self.add_child(Button(self, domain_object.events.search)).append_class('btn-success-outline')

        return MyForm(self.view)


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
    vassert( 'navbar-form' in form.get_attribute('class') )



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

"scenarioify"
@test(NavbarFixture)
def adding_to_navbar_with_specific_device_alignment(fixture):
    """ """
    navbar = fixture.navbar.use_layout(NavbarLayout())
    left_expected_device = 'lg'
    right_expected_device = None
    side = 'left'
    widget_to_add = fixture.nav
    
    navbar.layout.add(widget_to_add, left=left_expected_device, right=right_expected_device)
    
    [added] = navbar.children[0].children
    
    expected_device = left_expected_device if left_expected_device else right_expected_device
    if expected_device:
        vassert( isinstance(added, Div) )
        vassert( added.children[0] is widget_to_add )
    if expected_device is True:
        vassert( 'pull-%s' % side in added.get_attribute('class') )
    if expected_device and expected_device is not True:
        vassert( 'pull-%s-%s' % (expected_device, side) in added.get_attribute('class') )



@test(NavbarFixture)
def adding_tralala(fixture):
    """Only Navs and Forms can be   added..."""
    pass

@test(NavbarFixture)
def navbar_with_centered_contents(fixture):
    """Contents of a Navbar appears centered when center_contents is set to True"""

    navbar_widget = fixture.navbar
    navbar_widget.use_layout(NavbarLayout(center_contents=True))
    navbar_widget.layout.set_brand_text('Brandy') #adding someting to illustrate the structure change

    [navbar] = navbar_widget.children
    [centering_div] = navbar.children
    [brand_widget] = centering_div.children

    vassert( 'container' in centering_div.get_attribute('class') )
    vassert( 'navbar-brand' in brand_widget.get_attribute('class') )


@test(NavbarFixture)
def navbar_toggle_collapses_html_element(fixture):
    """You can add a toggle to the navbar that toggles the visiblity of another Widget on the page."""
"selenium"
"maak oop, isnie visible"
"click toggle, is visible"
"click toggle, is nie visible"
    element_to_collapse = Div(fixture.view, css_id='my_id')
    navbar_widget = fixture.navbar_with_layout
    navbar_widget.layout.add_toggle(element_to_collapse)

    [navbar] = navbar_widget.children
    [toggle] = navbar.children
    [toggle_text_node] = toggle.children

    vassert( toggle.tag_name == 'button' )
    vassert( 'navbar-toggler' in toggle.get_attribute('class') )
    vassert( 'button' in toggle.get_attribute('type') )
    vassert( 'collapse' in toggle.get_attribute('data-toggle') )
    vassert( 'my_id' in toggle.get_attribute('data-target') )
    vassert( '☰' == toggle_text_node.value )


@test(NavbarFixture)
def navbar_toggle_customised(fixture):

    element_to_collapse = Div(fixture.view, css_id='my_id')
    toggle = fixture.navbar_with_layout.layout.add_toggle(element_to_collapse, text='≎')

    [toggle_text_node] = toggle.children

    vassert( '≎' == toggle_text_node.value )


@test(NavbarFixture)
def responsive_navbar(fixture):
    """A ResponsiveLayout collapses its Navbar when the viewport becomes smaller than a given device size"""
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

