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



from reahl.tofu import scenario, Fixture, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.browsertools.browsertools import WidgetTester, XPath

from reahl.web.fw import Url
from reahl.web.bootstrap.ui import P
from reahl.web.bootstrap.tabbedpanel import TabbedPanel, MultiTab, Tab


from reahl.webdev.fixtures import WebServerFixture
from reahl.web_dev.fixtures import WebFixture


@uses(web_fixture=WebFixture)
class   TabbedPanelAjaxFixture(Fixture):

    def new_PopulatedTabbedPanel(self):
        class PopulatedTabbedPanel(TabbedPanel):
            def __init__(self, view):
                super().__init__(view)
                multi_tab = MultiTab(view, 'multitab name', 'multi-main')
                tab1 = Tab(view, 'tab 1 name', 'multi1', P.factory(text='tab 1/1 content'))
                tab2 = Tab(view, 'tab 2 name', 'multi2', P.factory(text='tab 1/2 content'))
                multi_tab.add_tab(tab1)
                multi_tab.add_tab(tab2)
                self.add_tab(multi_tab)

                tab3 = Tab(view, 'tab 3 name', 'tab3', P.factory(text='tab 3 content'))
                self.add_tab(tab3)
                tab4 = Tab(view, 'tab 4 name', 'tab4', P.factory(text='tab 4 content'))
                self.add_tab(tab4)
        return PopulatedTabbedPanel

    def new_wsgi_app(self, enable_js=True):
        return self.web_fixture.new_wsgi_app(enable_js=enable_js, child_factory=self.PopulatedTabbedPanel.factory())

    def tab_is_active(self, tab_name):
        element = self.web_fixture.driver_browser.find_element('//a[contains(text(), "%s")]' % tab_name)
        return 'active' in element.get_attribute('class')

    def tab_contents_equals(self, expected_contents):
        current_contents = self.web_fixture.driver_browser.get_inner_html_for('//div[contains(@class, "active")]')
        return current_contents == expected_contents


@with_fixtures(WebFixture)
def test_basic_rendering(web_fixture):
    """A TabbedPanel consists of a Nav (its tabs) and a Div in which tab contents are displayed."""


    web_fixture.request.query_string = 'tab=tab1'
    tabbed_panel = TabbedPanel(web_fixture.view)
    tabbed_panel.add_tab(Tab(web_fixture.view, 'tab 1 name', 'tab1', P.factory(text='tab 1 content')))

    tester = WidgetTester(tabbed_panel)

    expected_html = \
      '''<ul role="tablist" class="nav nav-tabs reahl-menu">'''\
       '''<li class="nav-item">'''\
       '''<a id="nav_tab_tab1_tab" aria-controls="tab_tab1" aria-selected="true" data-target="#tab_tab1" data-toggle="tab" href="/?tab=tab1" role="tab" class="active nav-link">tab 1 name</a>'''\
       '''</li>'''\
      '''</ul>'''\
      '''<div class="tab-content">'''\
       '''<div id="tab_tab1" aria-labelledby="nav_tab_tab1_tab" role="tabpanel" class="active tab-pane"><p>tab 1 content</p></div>'''\
      '''</div>'''\

    actual = tester.render_html()
    assert actual == expected_html


@with_fixtures(WebFixture)
def test_tabs_with_sub_options(web_fixture):
    """A TabbedPanel can have Tabs that are each composed of multiple sub-options."""

    web_fixture.request.query_string = 'tab=mult2'
    tabbed_panel = TabbedPanel(web_fixture.view)
    multi_tab = MultiTab(web_fixture.view, 'tab 1 name', 'multitab-main')
    multi_tab.add_tab(Tab(web_fixture.view, 'multi tab 1', 'mult1', P.factory(text='tab 1/1 content')))
    multi_tab.add_tab(Tab(web_fixture.view, 'multi tab 2', 'mult2', P.factory(text='tab 1/2 content')))
    tabbed_panel.add_tab(multi_tab)

    tester = WidgetTester(tabbed_panel)

    expected_html = \
     '''<ul role="tablist" class="nav nav-tabs reahl-menu">'''\
     '''<li class="dropdown nav-item">'''\
      '''<a aria-haspopup="true" data-toggle="dropdown" href="/?open_item=tab+1+name&amp;tab=mult2" role="button" class="active dropdown-toggle nav-link reahl-ajaxlink">tab 1 name</a>'''\
      '''<div class="dropdown-menu">'''\
       '''<a id="nav_tab_mult1_tab" aria-controls="tab_mult1" aria-selected="false" data-target="#tab_mult1" data-toggle="tab" href="/?tab=mult1" role="tab" class="dropdown-item">multi tab 1</a>'''\
       '''<a id="nav_tab_mult2_tab" aria-controls="tab_mult2" aria-selected="true" data-target="#tab_mult2" data-toggle="tab" href="/?tab=mult2" role="tab" class="active dropdown-item">multi tab 2</a>'''\
      '''</div>'''\
     '''</li>'''\
    '''</ul>'''\
    '''<div class="tab-content">'''\
     '''<div id="tab_mult1" aria-labelledby="nav_tab_mult1_tab" role="tabpanel" class="tab-pane"><p>tab 1/1 content</p></div>'''\
     '''<div id="tab_mult2" aria-labelledby="nav_tab_mult2_tab" role="tabpanel" class="active tab-pane"><p>tab 1/2 content</p></div>'''\
    '''</div>'''

    actual = tester.render_html()
    assert actual == expected_html


@uses(web_fixture=WebFixture)
class DefaultTabScenarios(Fixture):

    @scenario
    def specified_on_query_string(self):
        self.web_fixture.request.query_string = 'tab=tab2'
        self.expected_contents = '<p>tab 2 content</p>'
        self.tab1_active = False
        self.tab2_active = True

    @scenario
    def defaulted(self):
        self.web_fixture.request.query_string = ''
        self.expected_contents = '<p>tab 1 content</p>'
        self.tab1_active = True
        self.tab2_active = False


@with_fixtures(WebFixture, DefaultTabScenarios)
def test_default_active_tab(web_fixture, default_tab_scenarios):
    """The first tab is active by default (if the active tab is not indicated in the query_string)."""

    tab1 = Tab(web_fixture.view, 'tab 1 name', 'tab1', P.factory(text='tab 1 content'))
    tab2 = Tab(web_fixture.view, 'tab 2 name', 'tab2', P.factory(text='tab 2 content'))

    tabbed_panel = TabbedPanel(web_fixture.view)
    tabbed_panel.add_tab(tab1)
    tabbed_panel.add_tab(tab2)

    [menu_item1, menu_item2] = tabbed_panel.nav.menu_items
    assert menu_item1.is_active == default_tab_scenarios.tab1_active
    assert menu_item2.is_active == default_tab_scenarios.tab2_active

    tester = WidgetTester(tabbed_panel)
    panel_contents = tester.get_html_for('//div[@class="tab-content"]/div[contains(@class, "active")]/*')
    assert panel_contents == default_tab_scenarios.expected_contents


class DefaultMultiTabScenarios(Fixture):
    @scenario
    def specified_on_query_string(self):
        self.query_args = {'tab':'multi2'}
        self.expected_contents = '<p>tab 1/2 content</p>'
        self.multi_tab_active = True
        self.tab1_active = False
        self.tab2_active = True
        self.tab3_active = False

    @scenario
    def defaulted(self):
        self.query_args = {}
        self.expected_contents = '<p>tab 1/1 content</p>'
        self.multi_tab_active = True
        self.tab1_active = True
        self.tab2_active = False
        self.tab3_active = False

    @scenario
    def specified_to_other_tab(self):
        self.query_args = {'tab':'tab3'}
        self.expected_contents = '<p>tab 3 content</p>'
        self.multi_tab_active = False
        self.tab1_active = False
        self.tab2_active = False
        self.tab3_active = True


@with_fixtures(WebFixture, TabbedPanelAjaxFixture, DefaultMultiTabScenarios)
def test_default_active_multi_tab(web_fixture, tabbed_panel_ajax_fixture, default_multi_tab_scenarios):
    """The first item of the first tab is active by default (if the active tab is not indicated in the query_string)."""
    fixture = default_multi_tab_scenarios


    web_fixture.reahl_server.set_app(tabbed_panel_ajax_fixture.wsgi_app)
    url = Url('/')
    url.set_query_from(fixture.query_args)
    web_fixture.driver_browser.open(str(url))

    assert tabbed_panel_ajax_fixture.tab_contents_equals(fixture.expected_contents)

    assert (not fixture.multi_tab_active) or tabbed_panel_ajax_fixture.tab_is_active('multitab name')
    assert (not fixture.tab1_active) or tabbed_panel_ajax_fixture.tab_is_active('tab 1 name')
    assert (not fixture.tab2_active) or tabbed_panel_ajax_fixture.tab_is_active('tab 2 name')
    assert (not fixture.tab3_active) or tabbed_panel_ajax_fixture.tab_is_active('tab 3 name')


@uses(web_fixture=WebFixture, web_server_fixture=WebServerFixture)
class PanelSwitchFixture(Fixture):

    def ensure_disabled_js_files_not_cached(self):
        if self.web_server_fixture.is_instantiated('chrome_driver'):
            assert self.web_fixture.chrome_driver is self.web_fixture.web_driver
            self.web_server_fixture.restart_chrome_session()

    @scenario
    def without_js(self):
        self.enable_js = False

    @scenario
    def with_js(self):
        self.enable_js = True


@with_fixtures(WebFixture, PanelSwitchFixture, TabbedPanelAjaxFixture)
def test_clicking_on_different_tabs_switch(web_fixture, panel_switch_fixture, tabbed_panel_ajax_fixture):
    """Clicking on tabs change the contents that are displayed as well as the active tab."""
    if not panel_switch_fixture.enable_js:
        panel_switch_fixture.ensure_disabled_js_files_not_cached()


    wsgi_app = tabbed_panel_ajax_fixture.new_wsgi_app(enable_js=panel_switch_fixture.enable_js)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    # Clicking on 3 (a normal tab), changes the current tab
    assert browser.wait_for_not(tabbed_panel_ajax_fixture.tab_is_active, 'tab 3 name')
    assert browser.wait_for_not(tabbed_panel_ajax_fixture.tab_contents_equals, '<p>tab 3 content</p>')

    browser.click(XPath.link().with_text('tab 3 name'))

    assert browser.wait_for(tabbed_panel_ajax_fixture.tab_is_active, 'tab 3 name')
    assert browser.wait_for(tabbed_panel_ajax_fixture.tab_contents_equals, '<p>tab 3 content</p>')

    browser.click(XPath.link().with_text('tab 4 name'))

    assert browser.wait_for_not(tabbed_panel_ajax_fixture.tab_is_active, 'tab 3 name')
    assert browser.wait_for(tabbed_panel_ajax_fixture.tab_is_active, 'tab 4 name')
    assert browser.wait_for(tabbed_panel_ajax_fixture.tab_contents_equals, '<p>tab 4 content</p>')


@with_fixtures(WebFixture, PanelSwitchFixture, TabbedPanelAjaxFixture)
def test_clicking_on_multi_tab(web_fixture, panel_switch_fixture, tabbed_panel_ajax_fixture):
    """Clicking on a multitab just opens and closes its dropdown without affecting the current open tab."""
    if not panel_switch_fixture.enable_js:
        panel_switch_fixture.ensure_disabled_js_files_not_cached()

    wsgi_app = tabbed_panel_ajax_fixture.new_wsgi_app(enable_js=panel_switch_fixture.enable_js)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    # Make tab 3 the active one
    browser.click(XPath.link().with_text('tab 3 name'))
    assert browser.wait_for(tabbed_panel_ajax_fixture.tab_is_active, 'tab 3 name')
    assert browser.wait_for(tabbed_panel_ajax_fixture.tab_contents_equals, '<p>tab 3 content</p>')

    # Clicking on the multitab toggles the dropdown
    assert browser.wait_for_element_not_visible(XPath.link().with_text('tab 2 name'))
    browser.click(XPath.link().with_text('multitab name'))
    assert browser.wait_for_element_visible(XPath.link().with_text('tab 2 name'))

    # - current active tab not changed
    assert browser.wait_for(tabbed_panel_ajax_fixture.tab_is_active, 'tab 3 name')
    assert browser.wait_for(tabbed_panel_ajax_fixture.tab_contents_equals, '<p>tab 3 content</p>')

    # Clicking on the multitab toggles the dropdown again
    browser.click(XPath.link().with_text('multitab name'))

    # - current active tab not changed
    assert browser.wait_for(tabbed_panel_ajax_fixture.tab_is_active, 'tab 3 name')
    assert browser.wait_for(tabbed_panel_ajax_fixture.tab_contents_equals, '<p>tab 3 content</p>')


@with_fixtures(WebFixture, PanelSwitchFixture, TabbedPanelAjaxFixture)
def test_clicking_on_sub_tab_switches(web_fixture, panel_switch_fixture, tabbed_panel_ajax_fixture):
    """Clicking on a sub tab also changes the contents that are displayed as well as the active tab."""
    if not panel_switch_fixture.enable_js:
        panel_switch_fixture.ensure_disabled_js_files_not_cached()

    wsgi_app = tabbed_panel_ajax_fixture.new_wsgi_app(enable_js=panel_switch_fixture.enable_js)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    browser.click(XPath.link().with_text('tab 3 name'))
    assert browser.wait_for(tabbed_panel_ajax_fixture.tab_is_active, 'tab 3 name')
    assert browser.wait_for(tabbed_panel_ajax_fixture.tab_contents_equals, '<p>tab 3 content</p>')

    assert browser.wait_for_not(tabbed_panel_ajax_fixture.tab_is_active, 'tab 2 name')
    assert browser.wait_for_not(tabbed_panel_ajax_fixture.tab_contents_equals, '<p>tab 1/2 content</p>')

    browser.click(XPath.link().with_text('multitab name'))
    browser.click(XPath.link().with_text('tab 2 name'))

    # - active status removed from previous
    assert browser.wait_for_not(tabbed_panel_ajax_fixture.tab_is_active, 'tab 3 name')

    # - new status and contents set
    assert browser.wait_for(tabbed_panel_ajax_fixture.tab_is_active, 'tab 2 name')
    assert browser.wait_for(tabbed_panel_ajax_fixture.tab_contents_equals, '<p>tab 1/2 content</p>')

    # Clicking away from the multitab sub-tab removes its active status
    browser.click(XPath.link().with_text('tab 3 name'))
    # tab2 is not active anymore
    assert browser.wait_for_not(tabbed_panel_ajax_fixture.tab_is_active, 'tab 2 name')
    # TODO: cs Remove the next commented code - there used to be a problem with bootstrap4 alpha
    # tab2 is not active anymore
    # if fixture.enable_js:
    #    pass
    #    ### assert None, 'This is a bug in bootstrap v4.0 alpha javascript'
    # else:
    #     vassert( fixture.driver_browser.wait_for_not(fixture.tab_is_active, 'tab 2 name') )


