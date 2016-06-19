# Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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

import warnings
import re

from nose.tools import istest
from reahl.tofu import scenario
from reahl.tofu import test
from reahl.tofu import vassert, expected

from reahl.web.ui import *
from reahl.component.modelinterface import BooleanField
from reahl.web.fw import Bookmark, Url
from reahl.webdev.tools import WidgetTester, XPath, Browser
from reahl.web_dev.fixtures import WebFixture

_ = Translator('reahl-web')

@istest
class BasicReahlWidgets(object):
    @test(WebFixture)
    def priority_group(self, fixture):
        """A Priority group is a construct that ensures only one of its members has primary priority."""
        g = PriorityGroup()
        w1 = P(fixture.view)
        w2 = P(fixture.view)
        w3 = P(fixture.view)
        
        g.add_secondary(w1)
        g.add_primary(w2)
        g.add_secondary(w3)

        vassert( w1.attributes.v['class'] == 'reahl-priority-secondary' )
        vassert( w2.attributes.v['class'] == 'reahl-priority-primary' )
        vassert( w3.attributes.v['class'] == 'reahl-priority-secondary' )
        
        # You cannot have more than one primary
        w4 = P(fixture.view)
        with expected(AssertionError):
            g.add_primary(w4)

        # You cannot add something more than once
        with expected(AssertionError):
            g.add_secondary(w3)


    class Scenarios(WebFixture):
        @scenario
        def panel(self):
            self.widget = Div(self.view)
            self.expected_html = '<div></div>'

        @scenario
        def input_group1(self):
            self.widget = InputGroup(self.view)
            self.expected_html = '<fieldset></fieldset>'

        @scenario
        def input_group2(self):
            self.widget = InputGroup(self.view, label_text='text')
            self.expected_html = '<fieldset><label>text</label></fieldset>'


                                
    @test(Scenarios)
    def aliassed_widgets(self, fixture):
        """Some Widgets really also just render HTML, but have more abstract names."""
        tester = WidgetTester(fixture.widget)
        rendered_html = tester.render_html()
        vassert( rendered_html == fixture.expected_html )

    @test(WebFixture)
    def html5_page(self, fixture):
        """An HTML5Page is an empty HTML 5 document using the header and body widgets."""
        widget = HTML5Page(fixture.view, title='It: $current_title')
        widget.add_default_slot('slot1', P.factory())
        tester = WidgetTester(widget)
        
        rendered_html = tester.render_html()
        head = '<head><title>It: %s</title></head>' % fixture.view.title
        expected_regex = '<!DOCTYPE html><html class="no-js"><script>.*</script>%s<body></body></html>' % head
        vassert( re.match(expected_regex, rendered_html.replace('\n', '')) )
        
        vassert( list(widget.default_slot_definitions.keys()) == ['slot1'] )

    @test(WebFixture)
    def rendering_a_menu_item(self, fixture):
        """A MenuItem is a li with a in it."""
        
        description = 'The link'
        href_path = '/link'
        bookmark = Bookmark('/', href_path, description)

        menu = Menu(fixture.view)
        menu_item = MenuItem.from_bookmark(fixture.view, bookmark)
        menu.add_item(menu_item)
        tester = WidgetTester(menu)

        with fixture.context:
            actual = tester.get_html_for('//li')
            
        vassert( actual == '<li><a href="%s">%s</a></li>' % (href_path, description) )
        
    @test(WebFixture)
    def menu(self, fixture):
        """Menus can be populated with a list of A's or Bookmarks, or MenuItems."""
        # Case: a normal menu from bookmarks
        item_specs = [Bookmark('/', '/href1', 'description1'),
                      Bookmark('/', '/href2', 'description2')]
        menu = Menu(fixture.view).with_bookmarks(item_specs)
        tester = WidgetTester(menu)

        with fixture.context:
            actual = tester.render_html()
        rendered_children = WidgetTester(menu.children[0].children).render_html()
        expected_html = '''<ul class="reahl-menu">%s</ul>''' % rendered_children
        vassert( actual == expected_html )
        
        #case: using A's
        a_list = [A.from_bookmark(fixture.view, i) for i in item_specs]
        menu = Menu(fixture.view).with_a_list(a_list)
        tester = WidgetTester(menu)
        with fixture.context:
            actual = tester.render_html()
        vassert( actual == expected_html )
        
        # Case: adding already constructed menu item
        menu = Menu(fixture.view)
        item1 = MenuItem(fixture.view, A.from_bookmark(fixture.view, item_specs[0]))
        item2 = MenuItem(fixture.view, A.from_bookmark(fixture.view, item_specs[1]))
        menu.add_item(item1)
        menu.add_item(item2)
        vassert( menu.menu_items == [item1, item2] )
        
        tester = WidgetTester(menu)
        with fixture.context:
            actual = tester.render_html()
        vassert( actual == expected_html )
        
        # Case: Menu
        menu = Menu(fixture.view).with_bookmarks(item_specs)
        vassert( menu.html_representation.attributes.v['class'] == 'reahl-menu' )

        # Case: HMenu
        with warnings.catch_warnings(record=True):
            menu = HMenu(fixture.view, []).with_bookmarks(item_specs)
        vassert( menu.html_representation.attributes.v['class'] == 'reahl-horizontal reahl-menu' )

        # Case: VMenu
        with warnings.catch_warnings(record=True):
            menu = VMenu(fixture.view, []).with_bookmarks(item_specs)
        vassert( menu.html_representation.attributes.v['class'] == 'reahl-menu reahl-vertical' )

    @test(WebFixture)
    def menu_can_have_submenus(self, fixture):
        """One Menu can be added to another as submenu."""
        # Case: a normal menu from bookmarks
        single_item_bookmark = Bookmark('/', '/href3', 'description3')
        item_specs = [Bookmark('/', '/href1', 'description1'),
                      Bookmark('/', '/href2', 'description2')]

        sub_menu = Menu(fixture.view).with_bookmarks(item_specs)
        sub_menu_title = 'Subbie'
        menu = Menu(fixture.view)
        menu.add_item(MenuItem(fixture.view, A.from_bookmark(fixture.view, single_item_bookmark)))
        menu.add_submenu(sub_menu_title, sub_menu)

        expected_html = '''<ul class="reahl-menu">'''\
                   '''<li><a href="/href3">description3</a></li>'''\
                   '''<li><a>Subbie</a>'''\
                   '''<ul class="reahl-menu">'''\
                   '''<li><a href="/href1">description1</a></li>'''\
                   '''<li><a href="/href2">description2</a></li>'''\
                   '''</ul>'''\
                   '''</li>'''\
                   '''</ul>'''
        tester = WidgetTester(menu)
        with fixture.context:
            actual = tester.render_html()
        vassert( actual == expected_html )

    @test(WebFixture)
    def menu_can_have_submenus_deprecated_interface(self, fixture):
        """Menus can have sub-menus too - when built-up using .add_item()."""
        # Case: a normal menu from bookmarks
        single_item_bookmark = Bookmark('/', '/href3', 'description3')
        item_specs = [Bookmark('/', '/href1', 'description1'),
                      Bookmark('/', '/href2', 'description2')]

        sub_menu = Menu(fixture.view).with_bookmarks(item_specs)
        sub_menu_title = 'Subbie'
        menu = Menu(fixture.view)
        menu.add_item(MenuItem(fixture.view, A.from_bookmark(fixture.view, single_item_bookmark)))
        menu.add_submenu(sub_menu_title, sub_menu)

        expected_html = '''<ul class="reahl-menu">'''\
                   '''<li><a href="/href3">description3</a></li>'''\
                   '''<li><a>Subbie</a>'''\
                   '''<ul class="reahl-menu">'''\
                   '''<li><a href="/href1">description1</a></li>'''\
                   '''<li><a href="/href2">description2</a></li>'''\
                   '''</ul>'''\
                   '''</li>'''\
                   '''</ul>'''
        tester = WidgetTester(menu)
        with fixture.context:
            actual = tester.render_html()
        vassert( actual == expected_html )

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
    def rendering_active_menu_items(self, fixture):    
        """A MenuItem is marked as active based on its active_regex or the A it represents."""
        description = 'The link'
        href = Url('/link')

        menu = Menu(fixture.view)
        menu_item = MenuItem(fixture.view, A(fixture.view, href, description=description), active_regex=fixture.active_regex)
        menu.add_item(menu_item)
        tester = WidgetTester(menu)

        actual = tester.get_html_for('//li')
        class_str = '' if not fixture.active else ' class="active"'
        expected_menu_item_html = '<li%s><a href="/link">The link</a></li>' % (class_str)

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
            menu = Menu(self.view)
            menu.add_item(self.menu_item)
            return menu
        
        def new_tester(self):
            return WidgetTester(self.menu)

        def item_displays_as_active(self):
            actual = self.tester.get_html_for('//li')
            class_str = ' class="active"'
            expected_menu_item_html = '<li%s><a href="/link">The link</a></li>' % (class_str)
            return actual == expected_menu_item_html

        def set_request_url(self, href):
            self.request.environ['PATH_INFO'] = str(href)
    
    @test(CustomMenuItemFixture)
    def custom_active_menu_items(self, fixture):
        """You can specify a custom method by which a MenuItem determines its active state."""

        # The default behaviour happens when no custom method is supplied
        fixture.set_request_url(fixture.href)
        vassert( fixture.item_displays_as_active() )
        
        # Overriding behaviour happens when supplied
        fixture.menu_item.determine_is_active_using(lambda: False)
        vassert( not fixture.item_displays_as_active() )

        url_on_which_item_is_usually_inactive = Url('/another_href')
        fixture.set_request_url(url_on_which_item_is_usually_inactive)
        fixture.menu_item.determine_is_active_using(lambda: True)
        vassert( fixture.item_displays_as_active() )

    @test(WebFixture)
    def language_menu(self, fixture):
        """A Menu can also be constructed to let a user choose to view the same page in 
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


    class Scenarios(WebFixture):
        @scenario
        def yuidoc(self):
            self.config.web.frontend_libraries.use_deprecated_yui()
            with warnings.catch_warnings(record=True):
                self.widget = YuiDoc(self.view, 'docid', 'docclass')
            self.expected_html = '<div id="docid" class="docclass"><div id="hd" class="yui-g"><header></header></div><div id="bd" role="main"><div id="yui-main"><div class="yui-b"></div></div><div class="yui-b"></div></div><div id="ft"><footer></footer></div></div>'
        @scenario
        def yuiblock(self):
            self.config.web.frontend_libraries.use_deprecated_yui()
            with warnings.catch_warnings(record=True):
                self.widget = YuiBlock(self.view)
            self.expected_html = '<div class="yui-b"></div>'

        @scenario
        def yuigrid(self):
            self.config.web.frontend_libraries.use_deprecated_yui()
            with warnings.catch_warnings(record=True):
                self.widget = YuiGrid(self.view)
            self.expected_html = '<div class="yui-g"></div>'

        @scenario
        def yuiunit1(self):
            self.config.web.frontend_libraries.use_deprecated_yui()
            with warnings.catch_warnings(record=True):
                self.widget = YuiUnit(self.view)
            self.expected_html = '<div class="yui-u"></div>'

        @scenario
        def yuiunit_first(self):
            self.config.web.frontend_libraries.use_deprecated_yui()
            with warnings.catch_warnings(record=True):
                self.widget = YuiUnit(self.view, first=True)
            self.expected_html = '<div class="first yui-u"></div>'
            
    @test(Scenarios)
    def yui_widgets(self, fixture):
        """Different Yui widgets for rendering HTML that it compatible with the Yui CSS framework."""
        tester = WidgetTester(fixture.widget)
        rendered_html = tester.render_html()
        vassert( rendered_html == fixture.expected_html )
        
    @test(WebFixture)
    def twocolumn_page(self, fixture):
        """A simple Yui page with two columns, a header and a footer."""
        fixture.config.web.frontend_libraries.use_deprecated_yui()
        with warnings.catch_warnings(record=True):
            widget = TwoColumnPage(fixture.view, title='It: $current_title')
        widget.add_default_slot('slot1', P.factory())
        tester = WidgetTester(widget)
        
        rendered_html = tester.render_html()
        expected_regex = '<!DOCTYPE html><html class="no-js"><script>.*</script><head><title>It: A view</title></head><body><div id="doc" class="yui-t2"><div id="hd" class="yui-g"><header></header></div><div id="bd" role="main"><div id="yui-main"><div class="yui-b"></div></div><div class="yui-b"></div></div><div id="ft"><footer></footer></div></div></body></html>'
        vassert( re.match(expected_regex, rendered_html.replace('\n','') ))
        
        vassert( list(widget.default_slot_definitions.keys()) == ['slot1'] )
        
        vassert( isinstance(widget.yui_page, YuiDoc) )
        vassert( widget.footer is widget.yui_page.footer )
        vassert( widget.header is widget.yui_page.header )
        vassert( widget.main is widget.yui_page.main_block )
        vassert( widget.secondary is widget.yui_page.secondary_block )




class TabbedPanelAjaxFixture(WebFixture):
    def new_PopulatedTabbedPanel(self):
        fixture = self
        class PopulatedTabbedPanel(TabbedPanel):
            def __init__(self, view):
                super(PopulatedTabbedPanel, self).__init__(view, 'tabbed')
                multi_tab = MultiTab(view, 'multitab name', 'multi-main', P.factory(text='main multi tab content'))
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
        return self.driver_browser.execute_script('return window.jQuery("a:contains(\'%s\')").parent().hasClass("active")' % tab_name)

    def tab_contents_equals(self, expected_contents):
        return self.driver_browser.execute_script('return window.jQuery("div.reahl-tabbedpanel div").html() == "%s"' % expected_contents)


@istest
class TabbedPanelTests(object):
    @test(WebFixture)
    def basic_rendering(self, fixture):
        """A TabbedPanel is a Div which contains a Horizontal Menu and a Div."""
        fixture.request.query_string = 'tab=tab1'
        tabbed_panel = TabbedPanel(fixture.view, 'tabbed_name')
        tabbed_panel.add_tab(Tab(fixture.view, 'tab 1 name', 'tab1', P.factory(text='tab 1 content')))

        tester = WidgetTester(tabbed_panel)

        expected_html = '''<div id="tabbed_name" class="reahl-tabbedpanel">'''\
                        '''<ul class="reahl-horizontal reahl-menu">'''\
                        '''<li class="active"><a href="/?tab=tab1" class="reahl-ajaxlink">tab 1 name</a></li>'''\
                        '''</ul>'''\
                        '''<div><p>tab 1 content</p></div>'''\
                        '''</div>'''
        actual = tester.render_html()        
        vassert( actual == expected_html )

    @test(WebFixture)
    def tabs_with_sub_options(self, fixture):
        """A TabbedPanel can have Tabs that are each composed of multiple sub-options."""
        fixture.request.query_string = 'tab=mult2'
        tabbed_panel = TabbedPanel(fixture.view, 'tabbed_name')
        multi_tab = MultiTab(fixture.view, 'tab 1 name', 'multitab-main', P.factory(text='multi tab main content'))
        multi_tab.add_tab(Tab(fixture.view, 'multi tab 1', 'mult1', P.factory(text='tab 1/1 content')))
        multi_tab.add_tab(Tab(fixture.view, 'multi tab 2', 'mult2', P.factory(text='tab 1/2 content')))
        tabbed_panel.add_tab(multi_tab)

        tester = WidgetTester(tabbed_panel)
        
        expected_html = '''<div id="tabbed_name" class="reahl-tabbedpanel">'''\
                        '''<ul class="reahl-horizontal reahl-menu">'''\
                        '''<li class="active"><a href="/?tab=multitab-main" class="reahl-ajaxlink">tab 1 name</a>&nbsp;'''\
                        '''<a class="dropdown-handle">▼</a>'''\
                        '''<ul class="reahl-menu reahl-vertical">'''\
                        '''<li><a href="/?tab=mult1" class="reahl-ajaxlink">multi tab 1</a></li>'''\
                        '''<li class="active"><a href="/?tab=mult2" class="reahl-ajaxlink">multi tab 2</a></li>'''\
                        '''</ul>'''\
                        '''</li>'''\
                        '''</ul>'''\
                        '''<div><p>tab 1/2 content</p></div>'''\
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
    def default_active_tab(self, fixture):
        """The first tab is active by default (if the active tab is not indicated in the query_string)."""
        tab1 = Tab(fixture.view, 'tab 1 name', 'tab1', P.factory(text='tab 1 content'))
        tab2 = Tab(fixture.view, 'tab 2 name', 'tab2', P.factory(text='tab 2 content'))

        tabbed_panel = TabbedPanel(fixture.view, 'tabbed_name')
        tabbed_panel.add_tab(tab1)
        tabbed_panel.add_tab(tab2)

        [menu_item1, menu_item2] = tabbed_panel.menu.menu_items
        vassert( menu_item1.is_active == fixture.tab1_active )
        vassert( menu_item2.is_active == fixture.tab2_active )

        tester = WidgetTester(tabbed_panel)
        panel_contents = tester.get_html_for('//div/div/*')
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
    def default_active_multi_tab(self, fixture):
        """The first item of the first tab is active by default (if the active tab is not indicated in the query_string)."""
        tabbed_panel = TabbedPanel(fixture.view, 'tabbed_panel')
        multi_tab = MultiTab(fixture.view, 'tab 1 name', 'multi-tab', P.factory(text='multi tab main content'))
        tab1 = Tab(fixture.view, 'tab 1 name', 'multi1', P.factory(text='tab 1/1 content'))
        tab2 = Tab(fixture.view, 'tab 2 name', 'multi2', P.factory(text='tab 1/2 content'))
        multi_tab.add_tab(tab1)
        multi_tab.add_tab(tab2)
        tabbed_panel.add_tab(multi_tab)

        tab3 = Tab(fixture.view, 'tab 3 name', 'tab3', P.factory(text='tab 3 content'))
        tabbed_panel.add_tab(tab3)

        [top_level_menu_item_for_multitab, top_level_normal_menu_item] = tabbed_panel.menu.menu_items
        [multi_tab_menu_item1, multi_tab_menu_item2] = multi_tab.menu.menu_items

        vassert( top_level_menu_item_for_multitab.is_active == fixture.multi_tab_active )
        vassert( multi_tab_menu_item1.is_active == fixture.tab1_active )
        vassert( multi_tab_menu_item2.is_active == fixture.tab2_active )
        vassert( top_level_normal_menu_item.is_active == fixture.tab3_active )

        tester = WidgetTester(tabbed_panel)
        panel_contents = tester.get_html_for('//div/div/*')
        vassert( panel_contents == fixture.expected_contents )

    @test(TabbedPanelAjaxFixture)
    def switching_panels(self, fixture):
        """The contents registered with the TabbedPanel's active tab are displayed."""
        fixture.reahl_server.set_app(fixture.wsgi_app)
        fixture.driver_browser.open('/')

        # by default, the first tab is active and its contents are displayed
        vassert( fixture.driver_browser.wait_for(fixture.tab_is_active, 'multitab name') )
        vassert( fixture.driver_browser.wait_for(fixture.tab_contents_equals, '<p>main multi tab content</p>') )

        fixture.driver_browser.click(XPath.link_with_text('tab 3 name'))
        # tab3 is active and its contents are shown
        vassert( fixture.driver_browser.wait_for(fixture.tab_is_active, 'tab 3 name') )
        vassert( fixture.driver_browser.wait_for(fixture.tab_contents_equals, '<p>tab 3 content</p>') )

        fixture.driver_browser.mouse_over(XPath.link_with_text('multitab name'))
        fixture.driver_browser.click(XPath.link_with_text('tab 2 name'))
        # tab2 is active and its contents are shown
        vassert( fixture.driver_browser.wait_for(fixture.tab_is_active, 'tab 2 name') )
        vassert( fixture.driver_browser.wait_for(fixture.tab_contents_equals, '<p>tab 1/2 content</p>') )

        fixture.driver_browser.click(XPath.link_with_text('▼'))
        # clicking on the down arrow does nothing
        vassert( fixture.driver_browser.wait_for(fixture.tab_is_active, 'tab 2 name') )

        fixture.driver_browser.click(XPath.link_with_text('multitab name'))
        # the main multitab is active and its contents are shown
        vassert( fixture.driver_browser.wait_for(fixture.tab_is_active, 'multitab name') )
        vassert( fixture.driver_browser.wait_for(fixture.tab_contents_equals, '<p>main multi tab content</p>') )



class SlidingPanelFixture(WebFixture):
    def new_PopulatedSlidingPanel(self):
        fixture = self
        class PopulatedSlidingPanel(SlidingPanel):
            def __init__(self, view):
                super(PopulatedSlidingPanel, self).__init__(view, 'slide')
                panel0 = Div(view)
                panel0.add_child(P(view, text='Contents for panel 0'))
                self.add_panel(panel0)

                panel1 = Div(view)
                panel1.add_child(P(view, text='Contents for panel 1'))
                self.add_panel(panel1)

        return PopulatedSlidingPanel

    def new_wsgi_app(self):
        return super(SlidingPanelFixture, self).new_wsgi_app(enable_js=True,
                                                           child_factory=self.PopulatedSlidingPanel.factory())
    def panel_is_visible(self, index):
        return self.driver_browser.wait_for_element_visible(XPath.paragraph_containing('Contents for panel %s' % index))

    def panel_is_not_visible(self, index):
        return self.driver_browser.wait_for_element_not_visible(XPath.paragraph_containing('Contents for panel %s' % index))



@test(SlidingPanelFixture)
def opens_on_selected_index(fixture):
    fixture.reahl_server.set_app(fixture.wsgi_app)
    browser = fixture.driver_browser
    
    browser.open('/?index=1')
    vassert( fixture.panel_is_visible(1) )
    

@test(SlidingPanelFixture)
def slide_right(fixture):
    fixture.reahl_server.set_app(fixture.wsgi_app)
    browser = fixture.driver_browser

    browser.open('/')
    vassert( fixture.panel_is_visible(0) )

    browser.click(XPath.link_with_text('>'))
    vassert( fixture.panel_is_not_visible(0) )
    vassert( fixture.panel_is_visible(1) )

    #wrapping back to start
    browser.click(XPath.link_with_text('>'))
    vassert( fixture.panel_is_not_visible(1) )
    vassert( fixture.panel_is_visible(0) )

@test(SlidingPanelFixture)
def slide_left(fixture):
    fixture.reahl_server.set_app(fixture.wsgi_app)
    browser = fixture.driver_browser

    browser.open('/')
    vassert( fixture.panel_is_visible(0) )

    #wrapping
    browser.click(XPath.link_with_text('<'))
    vassert( fixture.panel_is_not_visible(0) )
    vassert( fixture.panel_is_visible(1) )

    browser.click(XPath.link_with_text('<'))
    vassert( fixture.panel_is_not_visible(1) )
    vassert( fixture.panel_is_visible(0) )

class PopupAFixture(WebFixture):
    # (note that this xpath ensures that the p is the ONLY content of the dialog)
    poppedup_contents = "//div[@class='reahl-dialogcontent' and count(*)=1]/p[@id='contents']"
    

@istest
class PopupATests(object):
    @test(PopupAFixture)
    def default_behaviour(self, fixture):
        """If you click on the A, a popupwindow opens with its contents the specified
           element on the target page."""

        class PopupTestPanel(Div):
            def __init__(self, view):
                super(PopupTestPanel, self).__init__(view)
                self.add_child(PopupA(view, view.as_bookmark(), '#contents'))
                popup_contents = self.add_child(P(view, text='this is the content of the popup'))
                popup_contents.set_id('contents')

        wsgi_app = fixture.new_wsgi_app(child_factory=PopupTestPanel.factory(), enable_js=True)
        fixture.reahl_server.set_app(wsgi_app)
        fixture.driver_browser.open('/')
        
        # The A is rendered correctly
        fixture.driver_browser.is_element_present("//a[@title='Home page' and text()='Home page' and @href='/']")

        # subsequent behaviour
        fixture.driver_browser.click(XPath.link_with_text('Home page'))
        fixture.driver_browser.wait_for_element_visible(fixture.poppedup_contents)
        
        fixture.driver_browser.click(XPath.button_labelled('Close'))
        fixture.driver_browser.wait_for_element_not_visible(fixture.poppedup_contents)

    @test(PopupAFixture)
    def customising_dialog_buttons(self, fixture):
        """The buttons of the dialog can be customised."""
        
        class PopupTestPanel(Div):
            def __init__(self, view):
                super(PopupTestPanel, self).__init__(view)
                popup_a = self.add_child(PopupA(view, view.as_bookmark(), '#contents'))
                popup_a.add_button(DialogButton('Butt1'))
                popup_a.add_button(DialogButton('Butt2'))
                popup_contents = self.add_child(P(view, text='this is the content of the popup'))
                popup_contents.set_id('contents')

        wsgi_app = fixture.new_wsgi_app(child_factory=PopupTestPanel.factory(), enable_js=True)
        fixture.reahl_server.set_app(wsgi_app)

        button1_xpath = XPath.button_labelled('Butt1')
        button2_xpath = XPath.button_labelled('Butt2')
        fixture.driver_browser.open('/')

        fixture.driver_browser.click(XPath.link_with_text('Home page'))
        fixture.driver_browser.wait_for_element_visible(fixture.poppedup_contents)

        vassert( fixture.driver_browser.is_element_present(button1_xpath) )
        vassert( fixture.driver_browser.is_element_present(button2_xpath) )

    @test(PopupAFixture)
    def workings_of_check_checkbox_button(self, fixture):
        """A CheckCheckBoxButton checks the checkbox on the original page when clicked."""

        class PopupTestPanel(Div):
            @exposed
            def fields(self, fields):
                fields.field = BooleanField()
                
            def __init__(self, view):
                super(PopupTestPanel, self).__init__(view)
                popup_a = self.add_child(PopupA(view, view.as_bookmark(), '#contents'))
                popup_contents = self.add_child(P(view, text='this is the content of the popup'))
                popup_contents.set_id('contents')
                form = self.add_child(Form(view, 'aform'))
                checkbox = form.add_child(CheckboxInput(form, self.fields.field))

                popup_a.add_button(CheckCheckboxButton('Checkit', checkbox))

        wsgi_app = fixture.new_wsgi_app(child_factory=PopupTestPanel.factory(), enable_js=True)
        fixture.reahl_server.set_app(wsgi_app)

        button_xpath = XPath.button_labelled('Checkit')
        fixture.driver_browser.open('/')

        fixture.driver_browser.click(XPath.link_with_text('Home page'))
        fixture.driver_browser.wait_for_element_visible(fixture.poppedup_contents)

        fixture.driver_browser.click(button_xpath)
        fixture.driver_browser.wait_for_element_not_visible(fixture.poppedup_contents)

        vassert( fixture.driver_browser.is_checked("//input[@type='checkbox']") )




