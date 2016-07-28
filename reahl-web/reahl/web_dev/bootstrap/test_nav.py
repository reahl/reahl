# Copyright 2015, 2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.webdev.tools import WidgetTester, Browser, XPath
from reahl.web_dev.fixtures import WebFixture

from reahl.component.exceptions import ProgrammerError
from reahl.component.i18n import Translator
from reahl.web.fw import Bookmark, Url
from reahl.web.bootstrap.ui import A, Div, P
from reahl.web.bootstrap.navs import Menu, Nav, MenuItem, PillLayout, TabLayout, DropdownMenu, DropdownMenuLayout


_ = Translator('reahl-web')


@test(WebFixture)
def navs(fixture):
    """A Nav is a menu with css classes for styling by Bootstrap."""

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


@test(WebFixture)
def populating(fixture):
    """Navs can be populated with a list of A's or Bookmarks."""
    # Case: a normal menu from bookmarks
    item_specs = [Bookmark('/', '/href1', 'description1'),
                  Bookmark('/', '/go_to_href', 'description2')]
    menu = Nav(fixture.view).with_bookmarks(item_specs)
    tester = WidgetTester(menu)

    [item1, item2] = menu.menu_items
    vassert( item1.a.href.path == '/href1' )
    vassert( item1.a.children[0].value == 'description1' )
    
    vassert( item2.a.href.path == '/go_to_href' )
    vassert( item2.a.children[0].value == 'description2' )
    
    #case: using A's
    a_list = [A.from_bookmark(fixture.view, i) for i in item_specs]
    menu = Nav(fixture.view).with_a_list(a_list)
    [item1, item2] = menu.menu_items
    vassert( item1.a is a_list[0] )
    vassert( item2.a is a_list[1] )


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


class MenuItemScenarios(WebFixture):
    description = 'The link'
    href = Url('/link')

    @scenario
    def not_active(self):
        self.active_regex = None
        self.request.environ['PATH_INFO'] = '/something/else'
        self.active = False

    @scenario
    def active_exact_path(self):
        self.active_regex = None
        self.request.environ['PATH_INFO'] = '/link'
        self.active = True

    @scenario
    def active_partial_path(self):
        self.active_regex = None
        self.request.environ['PATH_INFO'] = '/link/something/more'
        self.active = True

    @scenario
    def inactive_partial_path(self):
        self.active_regex = '^/link$'
        self.request.environ['PATH_INFO'] = '/link/something/more'
        self.active = False

@test(MenuItemScenarios)
def rendering_active_menu_items(fixture):
    """A MenuItem is marked as active based on its active_regex or the A it represents."""
    description = 'The link'
    href = Url('/link')

    menu = Nav(fixture.view)
    menu_item = MenuItem(fixture.view, A(fixture.view, href, description=description), active_regex=fixture.active_regex)
    menu.add_item(menu_item)
    tester = WidgetTester(menu)

    actual = tester.get_html_for('//li')
    active_str = '' if not fixture.active else 'active '
    expected_menu_item_html = '<li class="nav-item"><a href="/link" class="%snav-link">The link</a></li>'  % (active_str)
    vassert( actual == expected_menu_item_html )


class CustomMenuItemFixture(WebFixture):
    def new_href(self):
        return Url('/link')

    def new_menu_item(self):
        description = 'The link'
        href = Url('/link')
    
        menu_item = MenuItem(self.view, A(self.view, self.href, description=description))
        return menu_item

    def new_menu(self):
        menu = Nav(self.view)
        menu.add_item(self.menu_item)
        return menu
    
    def new_tester(self):
        return WidgetTester(self.menu)

    def item_displays_as_active(self):
        actual = self.tester.get_html_for('//li')
        active_str = 'active '
        expected_menu_item_html = '<li class="nav-item"><a href="/link" class="%snav-link">The link</a></li>'  % (active_str)
        return actual == expected_menu_item_html

    def set_request_url(self, href):
        self.request.environ['PATH_INFO'] = str(href)

    @scenario
    def default(self):
        # The default behaviour happens when no custom method is supplied
        self.go_to_href = self.href
        self.expects_active = True
        self.overriding_callable = None

    @scenario
    def overridden(self):
        # Overriding behaviour happens when supplied
        self.go_to_href = self.href
        self.expects_active = False
        self.overriding_callable = lambda: False

    @scenario
    def overridden_on_unrelated_url(self):
        # On an unrelated url, active is forced
        url_on_which_item_is_usually_inactive = Url('/another_href')
        self.go_to_href = url_on_which_item_is_usually_inactive

        self.expects_active = True
        self.overriding_callable = lambda: True


@test(CustomMenuItemFixture)
def custom_active_menu_items(fixture):
    """You can specify a custom method by which a MenuItem determines its active state."""
    fixture.set_request_url(fixture.go_to_href)

    if fixture.overriding_callable:
        fixture.menu_item.determine_is_active_using(fixture.overriding_callable)
    vassert( fixture.expects_active == fixture.item_displays_as_active() )


@test(WebFixture)
def language_menu(fixture):
    """A Nav can also be constructed to let a user choose to view the same page in 
       another of the supported languages."""
    
    class PanelWithMenu(Div):
        def __init__(self, view):
            super(PanelWithMenu, self).__init__(view)
            self.add_child(Menu(view).with_languages())
            self.add_child(P(view, text=_('This is an English sentence.')))

    wsgi_app = fixture.new_wsgi_app(child_factory=PanelWithMenu.factory())
    
    browser = Browser(wsgi_app)
    browser.open('/')
    
    vassert( browser.is_element_present(XPath.paragraph_containing('This is an English sentence.')) )

    browser.click(XPath.link_with_text('Afrikaans'))
    vassert( browser.is_element_present(XPath.paragraph_containing('Hierdie is \'n sin in Afrikaans.')) )

    browser.click(XPath.link_with_text('English (United Kingdom)'))
    vassert( browser.is_element_present(XPath.paragraph_containing('This is an English sentence.')) )


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
    """Navs can be laid out in different ways."""
    menu = Nav(fixture.view)

    vassert( not fixture.layout_css_class.issubset(menu.html_representation.attributes['class'].value) )
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





