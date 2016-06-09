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

from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import WidgetTester, XPath

from reahl.web.fw import Url
from reahl.web.ui import P

from reahl.web.bootstrap.tabbedpanel import TabbedPanel, MultiTab, Tab



class TabbedPanelAjaxFixture(WebFixture):
    def new_PopulatedTabbedPanel(self):
        fixture = self
        class PopulatedTabbedPanel(TabbedPanel):
            def __init__(self, view):
                super(PopulatedTabbedPanel, self).__init__(view)
                multi_tab = MultiTab(view, 'multitab name', 'multi-main')
                tab1 = Tab(fixture.view, 'tab 1 name', 'multi1', P.factory(text='tab 1/1 content'))
                tab2 = Tab(fixture.view, 'tab 2 name', 'multi2', P.factory(text='tab 1/2 content'))
                multi_tab.add_tab(tab1)
                multi_tab.add_tab(tab2)
                self.add_tab(multi_tab)

                tab3 = Tab(fixture.view, 'tab 3 name', 'tab3', P.factory(text='tab 3 content'))
                self.add_tab(tab3)
                tab4 = Tab(fixture.view, 'tab 4 name', 'tab4', P.factory(text='tab 4 content'))
                self.add_tab(tab4)
        return PopulatedTabbedPanel

    def new_webconfig(self):
        webconfig = super(TabbedPanelAjaxFixture, self).new_webconfig()
        webconfig.frontend_libraries.enable_experimental_bootstrap()
        return webconfig

    def new_wsgi_app(self, enable_js=True):
        return super(TabbedPanelAjaxFixture, self).new_wsgi_app(enable_js=enable_js,
                                                   child_factory=self.PopulatedTabbedPanel.factory())
    def tab_is_active(self, tab_name):
        element = self.driver_browser.find_element('//a[contains(text(), "%s")]' % tab_name)
        return 'active' in element.get_attribute('class')

    def tab_contents_equals(self, expected_contents):
        current_contents = self.driver_browser.get_inner_html_for('//div[contains(@class, "active")]')
        return current_contents == expected_contents


@test(WebFixture)
def basic_rendering(fixture):
    """A TabbedPanel consists of a Nav (its tabs) and a Div in which tab contents are displayed."""
    fixture.request.query_string = 'tab=tab1'
    tabbed_panel = TabbedPanel(fixture.view)
    tabbed_panel.add_tab(Tab(fixture.view, 'tab 1 name', 'tab1', P.factory(text='tab 1 content')))

    tester = WidgetTester(tabbed_panel)

    expected_html = \
      '''<ul class="nav nav-tabs">'''\
       '''<li class="nav-item">'''\
       '''<a data-target="#tab_tab1" data-toggle="tab" href="/?tab=tab1" class="active nav-link">tab 1 name</a>'''\
       '''</li>'''\
      '''</ul>'''\
      '''<div class="tab-content">'''\
       '''<div id="tab_tab1" class="active tab-pane"><p>tab 1 content</p></div>'''\
      '''</div>'''\

    actual = tester.render_html()
    vassert( actual == expected_html )


@test(WebFixture)
def tabs_with_sub_options(fixture):
    """A TabbedPanel can have Tabs that are each composed of multiple sub-options."""
    fixture.request.query_string = 'tab=mult2'
    tabbed_panel = TabbedPanel(fixture.view)
    multi_tab = MultiTab(fixture.view, 'tab 1 name', 'multitab-main')
    multi_tab.add_tab(Tab(fixture.view, 'multi tab 1', 'mult1', P.factory(text='tab 1/1 content')))
    multi_tab.add_tab(Tab(fixture.view, 'multi tab 2', 'mult2', P.factory(text='tab 1/2 content')))
    tabbed_panel.add_tab(multi_tab)

    tester = WidgetTester(tabbed_panel)

    expected_html = \
     '''<ul class="nav nav-tabs">'''\
     '''<li class="dropdown nav-item">'''\
      '''<a data-target="-" data-toggle="dropdown" href="/?open_item=tab+1+name&amp;tab=mult2" class="active dropdown-toggle nav-link reahl-ajaxlink">tab 1 name<span class="caret"></span></a>'''\
      '''<div class="dropdown-menu">'''\
       '''<a data-target="#tab_mult1" data-toggle="tab" href="/?tab=mult1" class="dropdown-item">multi tab 1</a>'''\
       '''<a data-target="#tab_mult2" data-toggle="tab" href="/?tab=mult2" class="active dropdown-item">multi tab 2</a>'''\
      '''</div>'''\
     '''</li>'''\
    '''</ul>'''\
    '''<div class="tab-content">'''\
     '''<div id="tab_mult1" class="tab-pane"><p>tab 1/1 content</p></div>'''\
     '''<div id="tab_mult2" class="active tab-pane"><p>tab 1/2 content</p></div>'''\
    '''</div>'''
    
    actual = tester.render_html()        
    vassert( actual == expected_html )



class DefaultTabScenarios(WebFixture):
    @scenario
    def specified_on_query_string(self):
        self.request.query_string = 'tab=tab2'
        self.expected_contents = '<p>tab 2 content</p>'
        self.tab1_active = False
        self.tab2_active = True
        
    @scenario
    def defaulted(self):
        self.request.query_string = ''
        self.expected_contents = '<p>tab 1 content</p>'
        self.tab1_active = True
        self.tab2_active = False


@test(DefaultTabScenarios)
def default_active_tab(fixture):
    """The first tab is active by default (if the active tab is not indicated in the query_string)."""
    tab1 = Tab(fixture.view, 'tab 1 name', 'tab1', P.factory(text='tab 1 content'))
    tab2 = Tab(fixture.view, 'tab 2 name', 'tab2', P.factory(text='tab 2 content'))

    tabbed_panel = TabbedPanel(fixture.view)
    tabbed_panel.add_tab(tab1)
    tabbed_panel.add_tab(tab2)

    [menu_item1, menu_item2] = tabbed_panel.nav.menu_items
    vassert( menu_item1.is_active == fixture.tab1_active )
    vassert( menu_item2.is_active == fixture.tab2_active )

    tester = WidgetTester(tabbed_panel)
    panel_contents = tester.get_html_for('//div[@class="tab-content"]/div[contains(@class, "active")]/*')
    vassert( panel_contents == fixture.expected_contents )


class DefaultMultiTabScenarios(TabbedPanelAjaxFixture):
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


@test(DefaultMultiTabScenarios)
def default_active_multi_tab(fixture):
    """The first item of the first tab is active by default (if the active tab is not indicated in the query_string)."""
    fixture.reahl_server.set_app(fixture.wsgi_app)
    url = Url('/')
    url.set_query_from(fixture.query_args)
    fixture.driver_browser.open(str(url))

    vassert( fixture.tab_contents_equals(fixture.expected_contents) )
    
    vassert( (not fixture.multi_tab_active) or fixture.tab_is_active('multitab name') )
    vassert( (not fixture.tab1_active) or fixture.tab_is_active('tab 1 name') )
    vassert( (not fixture.tab2_active) or fixture.tab_is_active('tab 2 name') )
    vassert( (not fixture.tab3_active) or fixture.tab_is_active('tab 3 name') )


class PanelSwitchFixture(TabbedPanelAjaxFixture):
    def new_wsgi_app(self):
        return super(PanelSwitchFixture, self).new_wsgi_app(enable_js=self.enable_js)

    def ensure_disabled_js_files_not_cached(self):
        if self.run_fixture.is_instantiated('chrome_driver'):
            assert self.chrome_driver is self.web_driver
            self.run_fixture.restart_session(self.chrome_driver)

    @scenario
    def without_js(self):
        self.enable_js = False

    @scenario
    def with_js(self):
        self.enable_js = True


@test(PanelSwitchFixture)
def clicking_on_different_tabs_switch(fixture):
    """Clicking on tabs change the contents that are displayed as well as the active tab."""
    fixture.reahl_server.set_app(fixture.wsgi_app)
    fixture.driver_browser.open('/')

    # Clicking on 3 (a normal tab), changes the current tab
    vassert( fixture.driver_browser.wait_for_not(fixture.tab_is_active, 'tab 3 name') )
    vassert( fixture.driver_browser.wait_for_not(fixture.tab_contents_equals, '<p>tab 3 content</p>') )

    fixture.driver_browser.click(XPath.link_with_text('tab 3 name'))

    vassert( fixture.driver_browser.wait_for(fixture.tab_is_active, 'tab 3 name') )
    vassert( fixture.driver_browser.wait_for(fixture.tab_contents_equals, '<p>tab 3 content</p>') )

    fixture.driver_browser.click(XPath.link_with_text('tab 4 name'))

    vassert( fixture.driver_browser.wait_for_not(fixture.tab_is_active, 'tab 3 name') )
    vassert( fixture.driver_browser.wait_for(fixture.tab_is_active, 'tab 4 name') )
    vassert( fixture.driver_browser.wait_for(fixture.tab_contents_equals, '<p>tab 4 content</p>') )


@test(PanelSwitchFixture)
def clicking_on_multi_tab(fixture):
    """Clicking on a multitab just opens and closes its dropdown without affecting the current open tab."""
    fixture.reahl_server.set_app(fixture.wsgi_app)
    fixture.driver_browser.open('/')

    # Make tab 3 the active one
    fixture.driver_browser.click(XPath.link_with_text('tab 3 name'))
    vassert( fixture.driver_browser.wait_for(fixture.tab_is_active, 'tab 3 name') )
    vassert( fixture.driver_browser.wait_for(fixture.tab_contents_equals, '<p>tab 3 content</p>') )

    # Clicking on the multitab toggles the dropdown
    vassert( fixture.driver_browser.wait_for_element_not_visible(XPath.link_with_text('tab 2 name')) )
    fixture.driver_browser.click(XPath.link_with_text('multitab name'))
    vassert( fixture.driver_browser.wait_for_element_visible(XPath.link_with_text('tab 2 name')) )

    # - current active tab not changed
    vassert( fixture.driver_browser.wait_for(fixture.tab_is_active, 'tab 3 name') )
    vassert( fixture.driver_browser.wait_for(fixture.tab_contents_equals, '<p>tab 3 content</p>') )
    
    # Clicking on the multitab toggles the dropdown again
    fixture.driver_browser.click(XPath.link_with_text('multitab name'))

    # - current active tab not changed
    vassert( fixture.driver_browser.wait_for(fixture.tab_is_active, 'tab 3 name') )
    vassert( fixture.driver_browser.wait_for(fixture.tab_contents_equals, '<p>tab 3 content</p>') )


@test(PanelSwitchFixture)
def clicking_on_sub_tab_switches(fixture):
    """Clicking on a sub tab also changes the contents that are displayed as well as the active tab."""
    if not fixture.enable_js:
        fixture.ensure_disabled_js_files_not_cached()
    
    fixture.reahl_server.set_app(fixture.wsgi_app)
    fixture.driver_browser.open('/')

    fixture.driver_browser.click(XPath.link_with_text('tab 3 name'))
    vassert( fixture.driver_browser.wait_for(fixture.tab_is_active, 'tab 3 name') )
    vassert( fixture.driver_browser.wait_for(fixture.tab_contents_equals, '<p>tab 3 content</p>') )

    vassert( fixture.driver_browser.wait_for_not(fixture.tab_is_active, 'tab 2 name') )
    vassert( fixture.driver_browser.wait_for_not(fixture.tab_contents_equals, '<p>tab 1/2 content</p>') )

    fixture.driver_browser.click(XPath.link_with_text('multitab name'))
    fixture.driver_browser.click(XPath.link_with_text('tab 2 name'))

    # - active status removed from previous
    vassert( fixture.driver_browser.wait_for_not(fixture.tab_is_active, 'tab 3 name') )
    
    # - new status and contents set
    vassert( fixture.driver_browser.wait_for(fixture.tab_is_active, 'tab 2 name') )
    vassert( fixture.driver_browser.wait_for(fixture.tab_contents_equals, '<p>tab 1/2 content</p>') )

    # Clicking away from the multitab sub-tab removes its active status
    fixture.driver_browser.click(XPath.link_with_text('tab 3 name'))
#####
#    # tab2 is not active anymore
#    if fixture.enable_js:
#        assert None, 'This is a bug in bootstrap v4.0 alpha javascript'
#    vassert( fixture.driver_browser.wait_for_not(fixture.tab_is_active, 'tab 2 name') )


