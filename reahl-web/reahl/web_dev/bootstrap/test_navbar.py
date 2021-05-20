# Copyright 2016-2021 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.browsertools.browsertools import XPath
from reahl.component.exceptions import IsInstance

from reahl.web.fw import Bookmark
from reahl.web.bootstrap.ui import A, Div, P, TextNode, Span
from reahl.web.bootstrap.forms import Form
from reahl.web.bootstrap.navbar import Navbar, NavbarLayout, ResponsiveLayout, CollapseToggle
from reahl.web.bootstrap.navs import Nav

from reahl.component.exceptions import ProgrammerError

from reahl.web_dev.fixtures import WebFixture


@uses(web_fixture=WebFixture)
class NavbarFixture(Fixture):

    def new_navbar(self):
        return Navbar(self.web_fixture.view)

    def new_navbar_with_layout(self):
        return self.navbar.use_layout(NavbarLayout())

    def new_bookmarks(self):
        return [Bookmark('', '/one', 'One')]

    def new_nav(self):
        return Nav(self.web_fixture.view).with_bookmarks(self.bookmarks)

    def new_form(self):
        return Form(self.web_fixture.view, 'myform')

    def new_textnode(self):
        return TextNode(self.web_fixture.view, 'mytext')


@with_fixtures(WebFixture, NavbarFixture)
def test_navbar_basics(web_fixture, navbar_fixture):
    """A typical Navbar is created by using its layout to add some brand text, a nav and form in it."""

    fixture = navbar_fixture

    navbar = Navbar(web_fixture.view).use_layout(NavbarLayout())

    navbar.layout.set_brand_text('Brandy')
    navbar.layout.add(fixture.nav)
    navbar.layout.add(fixture.form)

    [brand, nav, form] = navbar.children[0].children
    [ul] = nav.children

    # The Navbar itself
    assert navbar.children[0].tag_name == 'nav'
    assert 'navbar' in navbar.children[0].get_attribute('class').split(' ')

    # The added contents
    assert isinstance(brand, A)
    assert brand.href.path == '/'
    assert 'navbar-brand' in brand.get_attribute('class')

    assert 'navbar-nav' in ul.get_attribute('class')

    assert isinstance(form, Form)
    assert 'form-inline' in form.get_attribute('class')


@uses(web_fixture=WebFixture)
class LayoutScenarios(Fixture):

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


@with_fixtures(WebFixture, LayoutScenarios)
def test_navbar_can_have_layout(web_fixture, layout_scenarios):
    """NavbarLayout is used to define the placement of a Navbar."""

    fixture = layout_scenarios

    widget = Navbar(web_fixture.view).use_layout(fixture.layout)

    [navbar] = widget.children
    all_classes = ['fixed-bottom', 'fixed-top', 'sticky-top']
    if fixture.expected_css_class:
        assert fixture.expected_css_class in navbar.get_attribute('class').split(' ')

    for not_expected_class in [i for i in all_classes if i != fixture.expected_css_class]:
        assert not_expected_class not in navbar.get_attribute('class').split(' ')


@with_fixtures(WebFixture)
def test_customised_colour_scheme(web_fixture):
    """A ColourScheme is used to determine link colours and/or optionally a standard bootstrap background color."""

    layout = NavbarLayout(colour_theme='light', bg_scheme='dark')
    widget = Navbar(web_fixture.view).use_layout(layout)

    [navbar] = widget.children

    assert 'navbar-light' in navbar.get_attribute('class')
    assert 'bg-dark' in navbar.get_attribute('class')


@with_fixtures(WebFixture, NavbarFixture)
def test_adding_brand_widget(web_fixture, navbar_fixture):
    """Brand content can also be added as a Widget, instead of only text."""

    navbar_widget = navbar_fixture.navbar.use_layout(NavbarLayout())
    custom_brand = Div(web_fixture.view)
    navbar_widget.layout.set_brand(custom_brand)

    [navbar] = navbar_widget.children
    [actual_brand_widget] = navbar.children

    assert actual_brand_widget is custom_brand
    assert 'navbar-brand' in actual_brand_widget.get_attribute('class')


@with_fixtures(WebFixture, NavbarFixture)
def test_adding_other_than_form_or_nav_is_not_allowed(web_fixture, navbar_fixture):
    """Only Navs, Forms and Text may be added to a NavbarLayout."""

    navbar = navbar_fixture.navbar.use_layout(NavbarLayout())
    not_a_form_or_nav = Div(web_fixture.view)

    with expected(IsInstance):
        navbar.layout.add(not_a_form_or_nav)

    # Case: Form
    navbar = navbar_fixture.new_navbar().use_layout(NavbarLayout())
    navbar.layout.add(navbar_fixture.form)
    [added_widget] = navbar.children[0].children
    assert added_widget is navbar_fixture.form
    assert 'form-inline' in navbar_fixture.form.get_attribute('class')

    # Case: Nav
    navbar = navbar_fixture.new_navbar().use_layout(NavbarLayout())
    assert 'navbar-nav' not in navbar_fixture.nav.html_representation.get_attribute('class').split(' ')
    navbar.layout.add(navbar_fixture.nav)
    [added_widget] = navbar.children[0].children
    assert added_widget is navbar_fixture.nav
    assert 'navbar-nav' in navbar_fixture.nav.html_representation.get_attribute('class').split(' ')

    # Case: Text
    navbar = navbar_fixture.new_navbar().use_layout(NavbarLayout())
    navbar.layout.add(navbar_fixture.textnode)
    [added_widget] = navbar.children[0].children
    [textnode] = added_widget.children
    assert isinstance(added_widget, Span)
    assert textnode is navbar_fixture.textnode
    assert 'navbar-text' in added_widget.get_attribute('class').split(' ')



@with_fixtures(WebFixture, NavbarFixture)
def test_navbar_with_centered_contents(web_fixture, navbar_fixture):
    """Contents of a Navbar appears centered when center_contents is set to True"""

    navbar_widget = navbar_fixture.navbar
    navbar_widget.use_layout(NavbarLayout(center_contents=True))
    navbar_widget.layout.set_brand_text('Brandy') #adding something to illustrate the structure change

    [navbar] = navbar_widget.children
    [centering_div] = navbar.children
    [brand_widget] = centering_div.children

    assert 'container' in centering_div.get_attribute('class')
    assert 'navbar-brand' in brand_widget.get_attribute('class')


@uses(web_fixture=WebFixture)
class NavbarToggleFixture(Fixture):

    def is_expanded(self, locator):
        return self.web_fixture.driver_browser.is_visible(locator) and \
               self.web_fixture.driver_browser.does_element_have_attribute(locator, 'class', value='collapse show')

    def panel_is_visible(self):
        return self.web_fixture.driver_browser.is_visible(XPath.paragraph().including_text('Peek-A-Boo'))

    def panel_is_expanded(self):
        return self.is_expanded(XPath.paragraph().including_text('Peek-A-Boo'))

    def xpath_to_locate_toggle(self):
        return XPath('//span[contains(@class,"navbar-toggler-icon")]')

    def new_MainWidget(self):
        fixture = self
        class MainWidget(Div):
            def __init__(self, view):
                super().__init__(view)

                navbar = Navbar(view)
                navbar.use_layout(NavbarLayout(colour_theme='dark', bg_scheme='dark'))
                fixture.element_to_collapse = P(view, text='Peek-A-Boo', css_id='my_id')
                navbar.layout.add_toggle(fixture.element_to_collapse)

                self.add_child(fixture.element_to_collapse)
                self.add_child(navbar)
        return MainWidget


@with_fixtures(WebFixture, NavbarFixture)
def test_navbar_toggle_basics(web_fixture, navbar_fixture):
    """You can add a toggle to the navbar that hides another element on the page."""

    element_to_collapse = Div(web_fixture.view, css_id='my_id')
    toggle = navbar_fixture.navbar_with_layout.layout.add_toggle(element_to_collapse)

    [toggle_span] = toggle.children

    assert isinstance(toggle_span, Span)
    assert 'navbar-toggler-icon' in toggle_span.get_attribute('class')
    assert 'navbar-toggler' in toggle.get_attribute('class').split()


@with_fixtures(WebFixture, NavbarFixture)
def test_navbar_toggle_customised(web_fixture, navbar_fixture):
    """The text on a toggle that hides an element is customisable"""

    element_to_collapse = Div(web_fixture.view, css_id='my_id')
    toggle = navbar_fixture.navbar_with_layout.layout.add_toggle(element_to_collapse, text='≎')

    [toggle_text_node] = toggle.children

    assert('≎' == toggle_text_node.value)


@with_fixtures(WebFixture, NavbarToggleFixture)
def test_navbar_toggle_collapses_html_element(web_fixture, navbar_toggle_fixture):
    """You can add a toggle to the navbar that hides another element on the page."""

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=navbar_toggle_fixture.MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')


    #case: by default, the element to hide is not visible
    assert browser.wait_for_not(navbar_toggle_fixture.panel_is_visible)

    #case: clicking on the toggle, causes the panel to appear
    browser.click(navbar_toggle_fixture.xpath_to_locate_toggle())
    browser.wait_for(navbar_toggle_fixture.panel_is_expanded)

    # case: clicking on the toggle again, causes the panel to disappear
    browser.click(navbar_toggle_fixture.xpath_to_locate_toggle())
    browser.wait_for_not(navbar_toggle_fixture.panel_is_visible)



@with_fixtures(WebFixture, NavbarFixture)
def test_navbar_toggle_requires_target_id(web_fixture, navbar_fixture):
    """To be able to hide an element, it is required to have an id"""

    navbar = navbar_fixture.navbar
    navbar.use_layout(NavbarLayout())
    element_without_id = P(web_fixture.view, text='Peek-A-Boo')

    with expected(ProgrammerError, test='.*has no css_id set.*'):
        navbar.layout.add_toggle(element_without_id)


@with_fixtures(WebFixture, NavbarFixture)
def test_responsive_navbar_basics(web_fixture, navbar_fixture):
    """A ResponsiveLayout hides its Navbar when the viewport becomes smaller than a given device size"""

    navbar_widget = navbar_fixture.navbar
    navbar_widget.set_id('my_navbar_id')
    navbar_widget.use_layout(ResponsiveLayout('sm'))

    [navbar] = navbar_widget.children
    [toggle, collapse_div] = navbar.children

    assert 'navbar-toggler' in toggle.get_attribute('class')
    assert 'button' in toggle.get_attribute('type')
    assert 'collapse' in toggle.get_attribute('data-toggle')
    assert 'my_navbar_id' in toggle.get_attribute('data-target')

    assert 'my_navbar_id' in collapse_div.get_attribute('id')
    assert 'collapse' in collapse_div.get_attribute('class').split()
    assert 'navbar-collapse' in collapse_div.get_attribute('class').split()

    assert 'navbar-expand-xs' in navbar.get_attribute('class')


class ToggleAlignmentScenarios(Fixture):
    @scenario
    def aligned_right(self):
        self.layout = ResponsiveLayout('sm', align_toggle_left=False)
        self.expected_order = [A, CollapseToggle, Div]

    @scenario
    def aligned_left(self):
        self.layout = ResponsiveLayout('sm', align_toggle_left=True)
        self.expected_order = [CollapseToggle, A, Div]


@with_fixtures(NavbarFixture, ToggleAlignmentScenarios)
def test_responsive_navbar_toggle_alignment(navbar_fixture, toggle_alignment_fixture):
    """A ResponsiveLayout hides its Navbar when the viewport becomes smaller than a given device size"""

    navbar_widget = navbar_fixture.navbar
    navbar_widget.set_id('my_navbar_id')
    navbar_widget.use_layout(toggle_alignment_fixture.layout)
    navbar_widget.layout.set_brand_text('brand')

    [navbar] = navbar_widget.children

    assert [c.__class__ for c in navbar.children] == toggle_alignment_fixture.expected_order


class BrandCollapseScenarios(Fixture):

    @scenario
    def brand_does_not_collapse_with_content(self):
        self.brand_collapse = False

    @scenario
    def brand_does_collapse_with_content(self):
        self.brand_collapse = True


@with_fixtures(WebFixture, NavbarFixture, BrandCollapseScenarios)
def test_brand_may_be_collapsed_with_expandable_content(web_fixture, navbar_fixture, brand_collapse_fixture):
    """Brands may be collapse along with the other content."""

    responsive_navbar = navbar_fixture.navbar
    responsive_navbar.set_id('my_navbar_id')
    responsive_navbar.use_layout(ResponsiveLayout('md', collapse_brand_with_content=brand_collapse_fixture.brand_collapse))
    responsive_navbar.layout.add(navbar_fixture.nav)

    brand_widget = Div(web_fixture.view)
    responsive_navbar.layout.set_brand(brand_widget)

    if brand_collapse_fixture.brand_collapse:
        [toggle, collapse_div] = responsive_navbar.children[0].children
        [brand, navbar_nav] = collapse_div.children
    else:
        [brand, toggle, collapse_div] = responsive_navbar.children[0].children
        [navbar_nav] = collapse_div.children

    assert brand is brand_widget
    assert 'navbar-collapse' in collapse_div.get_attribute('class')
    assert 'navbar-nav' in navbar_nav.html_representation.get_attribute('class')
    assert 'navbar-toggler' in toggle.get_attribute('class')
