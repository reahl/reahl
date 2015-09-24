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

from reahl.tofu import vassert, scenario, expected, test

from reahl.web_dev.fixtures import WebFixture

from reahl.component.exceptions import ProgrammerError
from reahl.web.fw import Bookmark, Url
from reahl.web.ui import A, Div

from reahl.web.bootstrap.navs import Nav, PillLayout, TabLayout, DropdownMenu, DropdownMenuLayout



@test(WebFixture)
def navs(fixture):
    """A Nav is a Menu with css classes for styling by Bootstrap."""

    bookmarks = [Bookmark('', '/one', 'One'),
                 Bookmark('', '/two', 'Two')]
    menu = Nav(fixture.view).with_bookmarks(bookmarks)
    
    # A nav is an ul.nav
    vassert( menu.html_representation.tag_name == 'ul' )
    vassert( 'nav' in menu.html_representation.get_attribute('class') )

    # Containing a li for each menu item
    [one, two] = menu.html_representation.children

    for item, expected_href, expected_description in [(one, '/one', 'One'),
                                                      (two, '/two', 'Two')]:
        vassert( item.tag_name == 'li' )
        vassert( item.get_attribute('class') == 'nav-item' )

        [a] = item.children
        vassert( a.get_attribute('href') == expected_href )
        vassert( a.children[0].value ==  expected_description )
        vassert( a.get_attribute('class') == 'nav-link' )

# To test:
#  That dropdown menus open/close when no javascript
#  and that they do not actually break in js when JS is on.
#  that Menu & Nav & DropdownMenu have default layouts if you never specify one


class VisualFeedbackScenarios(WebFixture):
    @scenario
    def disabled(self):
        """The mouse cursor is shown as no-access on disabled items."""
        def not_allowed():
            return False
        self.menu_item_with_state = A(self.view, Url('/another_url'), write_check=not_allowed)
        self.state_indicator_class = 'disabled'

    @scenario
    def active(self):
        """The currently active item is highlighted."""
        current_url = Url(self.request.url)
        self.menu_item_with_state = A(self.view, current_url)
        self.state_indicator_class = 'active'


@test(VisualFeedbackScenarios)
def visual_feedback_on_items(fixture):
    """The state of a MenuItem is visually indicated to a user."""
    menu = Nav(fixture.view, [])
    menu.add_a(A(fixture.view, Url('/an_url')))
    menu.add_a(fixture.menu_item_with_state)

    [defaulted_item, item_with_state] = menu.html_representation.children

    [defaulted_a] = defaulted_item.children
    [a_with_state] = item_with_state.children
    
    vassert( fixture.state_indicator_class not in defaulted_a.get_attribute('class') )
    vassert( fixture.state_indicator_class in a_with_state.get_attribute('class') )



class LayoutScenarios(WebFixture):
    @scenario
    def pill_layouts(self):
        """PillLayouts are used to make Navs MenuItems look almost like buttons."""
        self.layout_css_class = {'nav-pills'}
        self.layout = PillLayout()

    @scenario
    def stacked_pill_layouts(self):
        """Using a PillLayout, you can also make MenuItems appear stacked on top of 
           one another instead of being placed next to one another."""
        self.layout_css_class = {'nav-pills', 'nav-stacked'}
        self.layout = PillLayout(stacked=True)

    @scenario
    def tab_layouts(self):
        """TabLayouts are used to make Navs MenuItems look like a series of tabs."""
        self.layout_css_class = {'nav-tabs'}
        self.layout = TabLayout()


@test(LayoutScenarios)
def nav_layouts(fixture):
    """Navs can be laid out in different ways, and the Layout used creates the html_representation of the Nav"""
    menu = Nav(fixture.view)

    vassert( not menu.html_representation )
    menu.use_layout(fixture.layout)
    vassert( fixture.layout_css_class.issubset(menu.html_representation.attributes['class'].value) )


class DifferentLayoutTypes(WebFixture):
    @scenario
    def pills(self):
        self.layout_type = PillLayout

    @scenario
    def tabs(self):
        self.layout_type = TabLayout


@test(DifferentLayoutTypes)
def justified_items(fixture):
    """Both a PillLayout or TabLayout can be set to make the MenuItems of
       their Nav fill the width of the parent, with the text of each item centered."""

    menu = Nav(fixture.view).use_layout(fixture.layout_type())
    vassert( 'nav-justified' not in menu.html_representation.get_attribute('class') )
    
    menu = Nav(fixture.view).use_layout(fixture.layout_type(justified=True))
    vassert( 'nav-justified' in menu.html_representation.get_attribute('class') )


@test(WebFixture)
def pill_layouts_cannot_mix_justified_and_stacked(fixture):
    """A PillLayout cannot be both stacked and justified at the same time."""

    with expected(ProgrammerError):
        PillLayout(stacked=True, justified=True)


@test(WebFixture)
def dropdown_menus(fixture):
    """You can add a DropdownMenu as a dropdown inside a Nav."""
    menu = Nav(fixture.view)
    sub_menu = DropdownMenu(fixture.view)
    sub_menu.add_a(A(fixture.view, Url('/an/url'), description='sub menu item'))
    menu.add_dropdown('Dropdown title', sub_menu)

    [item] = menu.html_representation.children
    
    vassert( item.tag_name == 'li' )
    vassert( 'dropdown' in item.get_attribute('class') )
    
    [toggle, added_sub_menu] = item.children
    vassert( 'dropdown-toggle' in toggle.get_attribute('class') )
    vassert( 'dropdown' in toggle.get_attribute('data-toggle') )
    vassert( '-' in toggle.get_attribute('data-target') )
    vassert( 'caret' in toggle.children[1].get_attribute('class') )

    title_text = toggle.children[0].value
    vassert( title_text == 'Dropdown title' )

    vassert( added_sub_menu is sub_menu )
    vassert( 'dropdown-menu' in added_sub_menu.html_representation.get_attribute('class').split() )
    vassert( isinstance(added_sub_menu.html_representation, Div) )

    [dropdown_item] = added_sub_menu.html_representation.children
    vassert( isinstance(dropdown_item, A) )
    vassert( 'dropdown-item' in dropdown_item.get_attribute('class').split() )
    

@test(WebFixture)
def dropdown_menus_can_drop_up(fixture):
    """Dropdown menus can drop upwards instead of downwards."""
    menu = Nav(fixture.view)
    sub_menu = Nav(fixture.view)
    menu.add_dropdown('Dropdown title', sub_menu, drop_up=True)

    [item] = menu.html_representation.children
    
    vassert( item.tag_name == 'li' )
    vassert( 'dropup' in item.get_attribute('class') )


@test(WebFixture)
def dropdown_menus_right_align(fixture):
    """Dropdown menus can be aligned to the bottom right of their toggle, instead of the default (left)."""

    defaulted_sub_menu = DropdownMenu(fixture.view).use_layout(DropdownMenuLayout())
    vassert( 'dropdown-menu-right' not in defaulted_sub_menu.html_representation.get_attribute('class') )

    right_aligned_sub_menu = DropdownMenu(fixture.view).use_layout(DropdownMenuLayout(align_right=True))
    vassert( 'dropdown-menu-right' in right_aligned_sub_menu.html_representation.get_attribute('class') )





