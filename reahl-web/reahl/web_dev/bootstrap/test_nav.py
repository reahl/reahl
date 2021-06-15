# Copyright 2015-2021 Reahl Software Services (Pty) Ltd. All rights reserved.
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



from reahl.tofu import scenario, expected, Fixture, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.browsertools.browsertools import WidgetTester, Browser, XPath

from reahl.component.exceptions import ProgrammerError
from reahl.component.i18n import Catalogue
from reahl.web.fw import Bookmark, Url
from reahl.web.bootstrap.ui import A, Div, P, H
from reahl.web.bootstrap.forms import Form
from reahl.web.bootstrap.navs import Menu, Nav, PillLayout, TabLayout, DropdownMenu, DropdownMenuLayout, NavLayout

from reahl.web_dev.fixtures import WebFixture

_ = Catalogue('reahl-web')


@with_fixtures(WebFixture)
def test_navs(web_fixture):
    """A Nav is a menu with css classes for styling by Bootstrap."""

    bookmarks = [Bookmark('', '/one', 'One'),
                 Bookmark('', '/two', 'Two')]
    menu = Nav(web_fixture.view).with_bookmarks(bookmarks)

    # A nav is an ul.nav
    assert menu.html_representation.tag_name == 'ul'
    assert 'nav' in menu.html_representation.get_attribute('class')

    # Containing a li for each menu item
    [one, two] = menu.html_representation.children

    for item, expected_href, expected_description in [(one, '/one', 'One'),
                                                      (two, '/two', 'Two')]:
        assert item.tag_name == 'li'
        assert item.get_attribute('class') == 'nav-item'

        [a] = item.children
        assert a.get_attribute('href') == expected_href
        assert a.children[0].value ==  expected_description
        assert a.get_attribute('class') == 'nav-link'


@with_fixtures(WebFixture)
def test_populating(web_fixture):
    """Navs can be populated with a list of A's or Bookmarks."""

    # Case: a normal menu from bookmarks
    item_specs = [Bookmark('/', '/href1', 'description1'),
                  Bookmark('/', '/go_to_href', 'description2')]
    menu = Nav(web_fixture.view).with_bookmarks(item_specs)
    tester = WidgetTester(menu)

    [item1, item2] = menu.menu_items
    assert item1.a.href.path == '/href1'
    assert item1.a.children[0].value == 'description1'

    assert item2.a.href.path == '/go_to_href'
    assert item2.a.children[0].value == 'description2'

    #case: using A's
    a_list = [A.from_bookmark(web_fixture.view, i) for i in item_specs]
    menu = Nav(web_fixture.view).with_a_list(a_list)
    [item1, item2] = menu.menu_items
    assert item1.a is a_list[0]
    assert item2.a is a_list[1]


@uses(web_fixture=WebFixture)
class VisualFeedbackScenarios(Fixture):

    @scenario
    def disabled(self):
        """The mouse cursor is shown as no-access on disabled items."""
        def not_allowed():
            return False
        self.menu_item_with_state = A(self.web_fixture.view, Url('/another_url'), write_check=not_allowed)
        self.state_indicator_class = 'disabled'

    @scenario
    def active(self):
        """The currently active item is highlighted."""
        current_url = Url(self.web_fixture.request.url)
        self.menu_item_with_state = A(self.web_fixture.view, current_url)
        self.state_indicator_class = 'active'


@with_fixtures(WebFixture, VisualFeedbackScenarios)
def test_visual_feedback_on_items(web_fixture, visual_feedback_scenarios):
    """The state of a MenuItem is visually indicated to a user."""

    menu = Nav(web_fixture.view)
    menu.add_a(A(web_fixture.view, Url('/an_url')))
    menu.add_a(visual_feedback_scenarios.menu_item_with_state)

    [defaulted_item, item_with_state] = menu.html_representation.children

    [defaulted_a] = defaulted_item.children
    [a_with_state] = item_with_state.children

    assert visual_feedback_scenarios.state_indicator_class not in defaulted_a.get_attribute('class')
    assert visual_feedback_scenarios.state_indicator_class in a_with_state.get_attribute('class')


@uses(web_fixture=WebFixture)
class MenuItemScenarios(Fixture):
    description = 'The link'
    href = Url('/link')

    @scenario
    def not_active(self):
        self.active_regex = None
        self.web_fixture.request.environ['PATH_INFO'] = '/something/else'
        self.active = False

    @scenario
    def active_exact_path(self):
        self.active_regex = None
        self.web_fixture.request.environ['PATH_INFO'] = '/link'
        self.active = True

    @scenario
    def active_partial_path(self):
        self.active_regex = None
        self.web_fixture.request.environ['PATH_INFO'] = '/link/something/more'
        self.active = True

    @scenario
    def inactive_partial_path(self):
        self.active_regex = '^/link$'
        self.web_fixture.request.environ['PATH_INFO'] = '/link/something/more'
        self.active = False


@with_fixtures(WebFixture, MenuItemScenarios)
def test_rendering_active_menu_items(web_fixture, menu_item_scenarios):
    """A MenuItem is marked as active based on its active_regex or the A it represents."""
    description = 'The link'
    href = Url('/link')


    menu = Nav(web_fixture.view)
    menu_item_a = A(web_fixture.view, href, description=description)
    menu.add_a(menu_item_a, active_regex=menu_item_scenarios.active_regex)
    tester = WidgetTester(menu)

    actual = tester.get_html_for('//li')
    active_str = '' if not menu_item_scenarios.active else 'active '
    expected_menu_item_html = '<li class="nav-item"><a href="/link" class="%snav-link">The link</a></li>'  % (active_str)
    assert actual == expected_menu_item_html


@uses(web_fixture=WebFixture)
class CustomMenuItemFixture(Fixture):

    def new_href(self):
        return Url('/link')

    def new_menu_item_a(self):
        description = 'The link'
        href = Url('/link')

        menu_item_a = A(self.web_fixture.view, self.href, description=description)
        return menu_item_a

    def new_menu(self):
        menu = Nav(self.web_fixture.view)
        menu.add_a(self.menu_item_a)
        return menu

    @property
    def menu_item(self):
        return self.menu.menu_items[0]

    def new_tester(self):
        return WidgetTester(self.menu)

    def item_displays_as_active(self):
        actual = self.tester.get_html_for('//li')
        active_str = 'active '
        expected_menu_item_html = '<li class="nav-item"><a href="/link" class="%snav-link">The link</a></li>'  % (active_str)
        return actual == expected_menu_item_html

    def set_request_url(self, href):
        self.web_fixture.request.environ['PATH_INFO'] = str(href)

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


@with_fixtures(WebFixture, CustomMenuItemFixture)
def test_custom_active_menu_items(web_fixture, custom_menu_item_fixture):
    """You can specify a custom method by which a MenuItem determines its active state."""
    fixture = custom_menu_item_fixture


    fixture.set_request_url(fixture.go_to_href)

    if fixture.overriding_callable:
        fixture.menu_item.determine_is_active_using(fixture.overriding_callable)
    assert fixture.expects_active == fixture.item_displays_as_active()


@with_fixtures(WebFixture)
def test_language_menu(web_fixture):
    """A Nav can also be constructed to let a user choose to view the same page in
       another of the supported languages."""

    class PanelWithMenu(Div):
        def __init__(self, view):
            super().__init__(view)
            self.add_child(Menu(view).with_languages())
            self.add_child(P(view, text=_('This is an English sentence.')))


    wsgi_app = web_fixture.new_wsgi_app(child_factory=PanelWithMenu.factory())

    browser = Browser(wsgi_app)
    browser.open('/')

    assert browser.is_element_present(XPath.paragraph().including_text('This is an English sentence.'))

    browser.click(XPath.link().with_text('Afrikaans'))
    assert browser.is_element_present(XPath.paragraph().including_text('Hierdie is \'n sin in Afrikaans.'))

    browser.click(XPath.link().with_text('English (United Kingdom)'))
    assert browser.is_element_present(XPath.paragraph().including_text('This is an English sentence.'))


def test_nav_layout_restricts_option_to_alignment_or_justfication():

    with expected(ProgrammerError, test='Cannot set content_alignment and content_justfication at the same time.*'):
        NavLayout(content_alignment='fill', content_justification='start')


def test_nav_layout_ensures_valid_values_for_alignment():

    with expected(ProgrammerError, test='"invalid_value" should be one of: "center","end"'):
        NavLayout(content_alignment='invalid_value')


def test_nav_layout_ensures_valid_values_for_justification():

    with expected(ProgrammerError, test='"invalid_value" should be one of: "fill","justified"'):
        NavLayout(content_justification='invalid_value')


class LayoutScenarios(Fixture):
    @scenario
    def pill_layouts(self):
        """PillLayouts are used to make Navs MenuItems look almost like buttons."""
        self.layout_css_class = {'nav-pills'}
        self.layout = PillLayout()

    @scenario
    def stacked_pill_layouts(self):
        """Using a PillLayout, you can also make MenuItems appear stacked on top of
           one another instead of being placed next to one another."""
        self.layout_css_class = {'nav-pills', 'flex-column'}
        self.layout = PillLayout(stacked=True)

    @scenario
    def tab_layouts(self):
        """TabLayouts are used to make Navs MenuItems look like a series of tabs."""
        self.layout_css_class = {'nav-tabs'}
        self.layout = TabLayout()


@with_fixtures(WebFixture, LayoutScenarios)
def test_nav_layouts(web_fixture, layout_scenarios):
    """Navs can be laid out in different ways."""

    menu = Nav(web_fixture.view)

    assert not layout_scenarios.layout_css_class.issubset(menu.html_representation.attributes['class'].value)
    menu.use_layout(layout_scenarios.layout)
    assert layout_scenarios.layout_css_class.issubset(menu.html_representation.attributes['class'].value)


class DifferentLayoutTypes(Fixture):
    @scenario
    def pills(self):
        self.layout_class = PillLayout

    @scenario
    def tabs(self):
        self.layout_class = TabLayout


@with_fixtures(WebFixture, DifferentLayoutTypes)
def test_nav_layouts_can_be_used_to_fill_available_space(web_fixture, different_layout_types):
    """Both a PillLayout or TabLayout can be set to make the MenuItems of
       their Nav fill the width of the parent"""

    menu = Nav(web_fixture.view).use_layout(different_layout_types.layout_class())
    assert 'nav-justified' not in menu.html_representation.get_attribute('class')

    menu = Nav(web_fixture.view).use_layout(different_layout_types.layout_class(content_justification='justified'))
    assert 'nav-justified' in menu.html_representation.get_attribute('class')


@with_fixtures(WebFixture, DifferentLayoutTypes)
def test_nav_layouts_can_be_used_to_align_items_horizontally(web_fixture, different_layout_types):
    """Both a PillLayout or TabLayout can be set to make the MenuItems of
       their Nav be aligned horizontal."""

    menu = Nav(web_fixture.view).use_layout(different_layout_types.layout_class())
    assert 'justify-content-center' not in menu.html_representation.get_attribute('class')

    menu = Nav(web_fixture.view).use_layout(different_layout_types.layout_class(content_alignment='center'))
    assert 'justify-content-center' in menu.html_representation.get_attribute('class')


@with_fixtures(WebFixture)
def test_dropdown_menus(web_fixture):
    """You can add a DropdownMenu as a dropdown inside a Nav."""

    menu = Nav(web_fixture.view)
    sub_menu = DropdownMenu(web_fixture.view)
    sub_menu.add_a(A(web_fixture.view, Url('/an/url'), description='sub menu item'))
    menu.add_dropdown('Dropdown title', sub_menu)

    [item] = menu.html_representation.children

    assert item.tag_name == 'li'
    assert 'dropdown' in item.get_attribute('class')

    [toggle, added_sub_menu] = item.children
    assert 'dropdown-toggle' in toggle.get_attribute('class')
    assert 'button' in toggle.get_attribute('role')
    assert 'true' in toggle.get_attribute('aria-haspopup')
    assert 'dropdown' in toggle.get_attribute('data-toggle')

    title_text = toggle.children[0].value
    assert title_text == 'Dropdown title'

    assert added_sub_menu is sub_menu
    assert 'dropdown-menu' in added_sub_menu.html_representation.get_attribute('class').split()
    assert isinstance(added_sub_menu.html_representation, Div)

    [dropdown_item] = added_sub_menu.html_representation.children
    assert isinstance(dropdown_item, A)
    assert 'dropdown-item' in dropdown_item.get_attribute('class').split()


@with_fixtures(WebFixture)
def test_dropdown_menus_with_divider(web_fixture):
    """You can add a divider to a DropdownMenu."""
    sub_menu = DropdownMenu(web_fixture.view)
    sub_menu.add_a(A(web_fixture.view, Url('/an/url'), description='sub menu item'))
    sub_menu.add_divider()
    sub_menu.add_a(A(web_fixture.view, Url('/another/url'), description='another sub menu item'))

    [item1, divider, item2] = sub_menu.html_representation.children
    assert 'dropdown-divider' in divider.get_attribute('class').split()


@with_fixtures(WebFixture)
def test_dropdown_menu_with_header(web_fixture):
    """You can add a header item to a DropdownMenu."""
    sub_menu = DropdownMenu(web_fixture.view)
    my_header = H(web_fixture.view, 6, text='My header text')
    header = sub_menu.add_header(my_header)

    assert header is my_header
    [header] = sub_menu.html_representation.children
    assert 'dropdown-header' in header.get_attribute('class').split()


@with_fixtures(WebFixture)
def test_dropdown_menu_with_form(web_fixture):
    """You can add form to a DropdownMenu."""
    sub_menu = DropdownMenu(web_fixture.view)

    my_form = Form(web_fixture.view, 'myform')
    form = sub_menu.add_form(my_form)

    assert form is my_form
    [form] = sub_menu.html_representation.children
    assert 'px-4' in form.get_attribute('class').split()
    assert 'py-3' in form.get_attribute('class').split()


class DifferentDropPositions(Fixture):
    @scenario
    def dropup(self):
        self.direction = 'up'
        self.expected_class = 'dropup'

    @scenario
    def dropdown(self):
        self.direction = 'down'
        self.expected_class = 'dropdown'

    @scenario
    def dropleft(self):
        self.direction = 'left'
        self.expected_class = 'dropleft'

    @scenario
    def dropright(self):
        self.direction = 'right'
        self.expected_class = 'dropright'


@with_fixtures(WebFixture, DifferentDropPositions)
def test_dropdown_menus_drop_positions(web_fixture, drop_position_fixture):
    """Dropdown menus can drop to many positions."""

    menu = Nav(web_fixture.view)
    sub_menu = Nav(web_fixture.view)
    menu.add_dropdown('Dropdown title', sub_menu, drop_position=drop_position_fixture.direction)

    [item] = menu.html_representation.children

    assert item.tag_name == 'li'
    assert drop_position_fixture.expected_class in item.get_attribute('class')


@with_fixtures(WebFixture)
def test_dropdown_menus_right_align(web_fixture):
    """Dropdown menus can be aligned to the bottom right of their toggle, instead of the default (left)."""

    defaulted_sub_menu = DropdownMenu(web_fixture.view).use_layout(DropdownMenuLayout())
    assert 'dropdown-menu-right' not in defaulted_sub_menu.html_representation.get_attribute('class')

    right_aligned_sub_menu = DropdownMenu(web_fixture.view).use_layout(DropdownMenuLayout(align_right=True))
    assert 'dropdown-menu-right' in right_aligned_sub_menu.html_representation.get_attribute('class')
