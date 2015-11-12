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
from reahl.webdev.tools import WidgetTester, XPath

from reahl.component.exceptions import ProgrammerError
from reahl.web.fw import Bookmark, Url
from reahl.web.ui import A, Div, P

from reahl.web.bootstrap.navs import Nav, PillLayout, TabLayout, DropdownMenu, DropdownMenuLayout
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
        return PopulatedTabbedPanel

    def new_wsgi_app(self):
        return super(TabbedPanelAjaxFixture, self).new_wsgi_app(enable_js=True,
                                                   child_factory=self.PopulatedTabbedPanel.factory())
    def tab_is_active(self, tab_name):
        return self.driver_browser.execute_script('return window.jQuery("a:contains(\'%s\')").hasClass("active")' % tab_name)

    def tab_contents_equals(self, expected_contents):
        return self.driver_browser.execute_script('return window.jQuery("div.active").html() == "%s"' % expected_contents)


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


class DefaultMultiTabScenarios(WebFixture):
    @scenario
    def specified_on_query_string(self):
        self.request.query_string = 'tab=multi2'
        self.expected_contents = '<p>tab 1/2 content</p>'
        self.multi_tab_active = True
        self.tab1_active = False
        self.tab2_active = True
        self.tab3_active = False
        
    @scenario
    def defaulted(self):
        self.request.query_string = ''
        self.expected_contents = '<p>multi tab main content</p>'
        self.multi_tab_active = True
        self.tab1_active = False
        self.tab2_active = False
        self.tab3_active = False

    @scenario
    def specified_to_other_tab(self):
        self.request.query_string = 'tab=tab3'
        self.expected_contents = '<p>tab 3 content</p>'
        self.multi_tab_active = False
        self.tab1_active = False
        self.tab2_active = False
        self.tab3_active = True


@test(DefaultMultiTabScenarios)
def default_active_multi_tab(fixture):
    """The first item of the first tab is active by default (if the active tab is not indicated in the query_string)."""
    tabbed_panel = TabbedPanel(fixture.view)
    multi_tab = MultiTab(fixture.view, 'tab 1 name', 'multi-tab')
    tab1 = Tab(fixture.view, 'tab 1 name', 'multi1', P.factory(text='tab 1/1 content'))
    tab2 = Tab(fixture.view, 'tab 2 name', 'multi2', P.factory(text='tab 1/2 content'))
    multi_tab.add_tab(tab1)
    multi_tab.add_tab(tab2)
    tabbed_panel.add_tab(multi_tab)

    tab3 = Tab(fixture.view, 'tab 3 name', 'tab3', P.factory(text='tab 3 content'))
    tabbed_panel.add_tab(tab3)

    [top_level_menu_item_for_multitab, top_level_normal_menu_item] = tabbed_panel.nav.menu_items
    [multi_tab_menu_item1, multi_tab_menu_item2] = multi_tab.menu.menu_items

    vassert( top_level_menu_item_for_multitab.is_active == fixture.multi_tab_active )
    vassert( multi_tab_menu_item1.is_active == fixture.tab1_active )
    vassert( multi_tab_menu_item2.is_active == fixture.tab2_active )
    vassert( top_level_normal_menu_item.is_active == fixture.tab3_active )

    tester = WidgetTester(tabbed_panel)
    panel_contents = tester.get_html_for('//div[@class="tab-content"]/div[contains(@class, "active")]/*')
    vassert( panel_contents == fixture.expected_contents )


@test(TabbedPanelAjaxFixture)
def switching_panels(fixture):
    """The contents registered with the TabbedPanel's active tab are displayed."""
    fixture.reahl_server.set_app(fixture.wsgi_app)
    fixture.driver_browser.open('/')

    # by default, the first tab is active and its contents are displayed
    import pdb; pdb.set_trace()
    vassert( fixture.driver_browser.wait_for(fixture.tab_is_active, 'tab 1 name') )
    vassert( fixture.driver_browser.wait_for(fixture.tab_contents_equals, '<p>tab 1/1 content</p>') )

    fixture.driver_browser.click(XPath.link_with_text('tab 3 name'))
    # tab3 is active and its contents are shown
    vassert( fixture.driver_browser.wait_for(fixture.tab_is_active, 'tab 3 name') )
    vassert( fixture.driver_browser.wait_for(fixture.tab_contents_equals, '<p>tab 3 content</p>') )

    fixture.driver_browser.click(XPath.link_with_text('multitab name'))
    fixture.driver_browser.click(XPath.link_with_text('tab 2 name'))
    # tab2 is active and its contents are shown
    vassert( fixture.driver_browser.wait_for(fixture.tab_is_active, 'tab 2 name') )
    vassert( fixture.driver_browser.wait_for(fixture.tab_contents_equals, '<p>tab 1/2 content</p>') )

    fixture.driver_browser.click(XPath.link_with_text('tab 3 name'))
    # tab2 is not active anymore
    vassert( fixture.driver_browser.wait_for_not(fixture.tab_is_active, 'tab 2 name') )





