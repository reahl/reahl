# Copyright 2011, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from webob import Request
from nose.tools import istest
from reahl.tofu import Fixture, scenario, test
from reahl.tofu import vassert, expected
from reahl.stubble import stubclass, EmptyStub

from reahl.web.ui import *
from reahl.component.modelinterface import Field, BooleanField
from reahl.web.fw import Bookmark, Url
from reahl.webdev.tools import WidgetTester, XPath, Browser
from reahl.web_dev.widgets.widgetbasics import WidgetFixture
from reahl.web_dev.fixtures import WebFixture

_ = Translator(u'reahl-web')

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

        vassert( w1.attributes.v[u'class'] == u'reahl-priority-secondary' )
        vassert( w2.attributes.v[u'class'] == u'reahl-priority-primary' )
        vassert( w3.attributes.v[u'class'] == u'reahl-priority-secondary' )
        
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
            self.widget = Panel(self.view)
            self.expected_html = u'<div></div>'

        @scenario
        def input_group1(self):
            self.widget = InputGroup(self.view)
            self.expected_html = u'<fieldset></fieldset>'

        @scenario
        def input_group2(self):
            self.widget = InputGroup(self.view, label_text=u'text')
            self.expected_html = u'<fieldset><label>text</label></fieldset>'

                                
    @test(Scenarios)
    def aliassed_widgets(self, fixture):
        """Some Widgets really also just render HTML, but have more abstract names."""
        tester = WidgetTester(fixture.widget)
        rendered_html = tester.render_html()
        vassert( rendered_html == fixture.expected_html )

    @test(WebFixture)
    def html5_page(self, fixture):
        """An HTML5Page is an empty HTML 5 document using the header and body widgets."""
        widget = HTML5Page(fixture.view, title=u'It: $current_title')
        widget.add_default_slot(u'slot1', P.factory())
        tester = WidgetTester(widget)
        
        rendered_html = tester.render_html()
        head = u'<head><title>It: %s</title></head>' % fixture.view.title
        vassert( rendered_html == u'<!DOCTYPE html><html>%s<body></body></html>' % head)
        
        vassert( widget.default_slot_definitions.keys() == [u'slot1'] )

    @test(WebFixture)
    def rendering_a_menu_item(self, fixture):
        """A MenuItem is a li with a in it."""
        
        description = 'The link'
        href_path = '/link'
        bookmark = Bookmark(u'/', href_path, description)

        menu_item = MenuItem.from_bookmark(fixture.view, bookmark)
        tester = WidgetTester(menu_item)

        with fixture.context:
            actual = tester.render_html()
            
        vassert( actual == u'<li><a href="%s">%s</a></li>' % (href_path, description) )
        
    @test(WebFixture)
    def menu(self, fixture):
        """Menus can be constructed from a list of A's or Bookmarks, or MenuItems can be added to them."""
        # Case: a normal menu from bookmarks
        item_specs = [Bookmark(u'/', u'/href1', u'description1'),
                      Bookmark(u'/', u'/href2', u'description2')]
        menu = Menu.from_bookmarks(fixture.view, item_specs)
        tester = WidgetTester(menu)

        with fixture.context:
            actual = tester.render_html()
        rendered_children = WidgetTester(menu.children).render_html()
        expected = u'''<ul class="reahl-menu">%s</ul>''' % rendered_children
        vassert( actual == expected )
        
        #case: using A's
        a_list = [A.from_bookmark(fixture.view, i) for i in item_specs]
        menu = Menu(fixture.view, a_list)
        tester = WidgetTester(menu)
        with fixture.context:
            actual = tester.render_html()
        vassert( actual == expected )
        
        # Case: adding already constructed menu item
        menu = Menu(fixture.view, [])
        menu.add_item(MenuItem(fixture.view, A.from_bookmark(fixture.view, item_specs[0])))
        menu.add_item(MenuItem(fixture.view, A.from_bookmark(fixture.view, item_specs[1])))
        vassert( menu.menu_items == menu.children )
        
        tester = WidgetTester(menu)
        with fixture.context:
            actual = tester.render_html()
        vassert( actual == expected )
        
        # Case: HMenu
        menu = HMenu.from_bookmarks(fixture.view, item_specs)
        vassert( menu.attributes.v[u'class'] == u'reahl-horizontal reahl-menu' )

        # Case: VMenu
        menu = VMenu.from_bookmarks(fixture.view, item_specs)
        vassert( menu.attributes.v[u'class'] == u'reahl-menu reahl-vertical' )

    @test(WebFixture)
    def menu_can_have_submenus(self, fixture):
        """Menus can have sub-menus too - when built-up using .add_item()."""
        # Case: a normal menu from bookmarks
        single_item_bookmark = Bookmark(u'/', u'/href3', u'description3')
        item_specs = [Bookmark(u'/', u'/href1', u'description1'),
                      Bookmark(u'/', u'/href2', u'description2')]

        sub_menu = Menu.from_bookmarks(fixture.view, item_specs)
        sub_menu_title = u'Subbie'
        menu = Menu(fixture.view, [])
        menu.add_item(MenuItem(fixture.view, A.from_bookmark(fixture.view, single_item_bookmark)))
        menu.add_item(SubMenu(fixture.view, sub_menu_title, sub_menu))

        expected_html = u'''<ul class="reahl-menu">'''\
                   u'''<li><a href="/href3">description3</a></li>'''\
                   u'''<li><a>Subbie</a>'''\
                   u'''<ul class="reahl-menu">'''\
                   u'''<li><a href="/href1">description1</a></li>'''\
                   u'''<li><a href="/href2">description2</a></li>'''\
                   u'''</ul>'''\
                   u'''</li>'''\
                   u'''</ul>'''
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
            self.request.environ[u'PATH_INFO'] = u'/something/else'
            self.active = False

        @scenario
        def active_exact_path(self):
            self.active_regex = None
            self.request.environ[u'PATH_INFO'] = u'/link'
            self.active = True

        @scenario
        def active_partial_path(self):
            self.active_regex = None
            self.request.environ[u'PATH_INFO'] = u'/link/something/more'
            self.active = True

        @scenario
        def inactive_partial_path(self):
            self.active_regex = u'^/link$'
            self.request.environ[u'PATH_INFO'] = u'/link/something/more'
            self.active = False

    @test(MenuItemScenarios)
    def rendering_active_menu_items(self, fixture):    
        description = 'The link'
        href = Url('/link')
        
        menu_item = MenuItem(fixture.view, A(fixture.view, href, description=description), active_regex=fixture.active_regex)
        tester = WidgetTester(menu_item)

        actual = tester.render_html()
        class_str = u'' if not fixture.active else u' class="active"'
        expected_menu_item_html = u'<li%s><a href="/link">The link</a></li>' % (class_str)

        vassert( actual == expected_menu_item_html )


    @test(WebFixture)
    def language_menu(self, fixture):
        """A Menu can also be constructed to let a user choose to view the same page in 
           another of the supported languages."""
        
        class PanelWithMenu(Panel):
            def __init__(self, view):
                super(PanelWithMenu, self).__init__(view)
                self.add_child(HMenu.from_languages(view))
                self.add_child(P(view, text=_(u'This is an English sentence.')))

        wsgi_app = fixture.new_wsgi_app(child_factory=PanelWithMenu.factory())
        
        browser = Browser(wsgi_app)
        browser.open(u'/')
        
        vassert( browser.is_element_present(XPath.paragraph_containing(u'This is an English sentence.')) )

        browser.click(XPath.link_with_text(u'Afrikaans'))
        vassert( browser.is_element_present(XPath.paragraph_containing(u'Hierdie is \'n sin in Afrikaans.')) )

        browser.click(XPath.link_with_text(u'English (United Kingdom)'))
        vassert( browser.is_element_present(XPath.paragraph_containing(u'This is an English sentence.')) )


    class Scenarios(WebFixture):
        @scenario
        def yuidoc(self):
            self.widget = YuiDoc(self.view, u'docid', u'docclass')
            self.expected_html = u'<div id="docid" class="docclass"><div id="hd" class="yui-g"><header></header></div><div id="bd" role="main"><div id="yui-main"><div class="yui-b"></div></div><div class="yui-b"></div></div><div id="ft"><footer></footer></div></div>'
        @scenario
        def yuiblock(self):
            self.widget = YuiBlock(self.view)
            self.expected_html = u'<div class="yui-b"></div>'

        @scenario
        def yuigrid(self):
            self.widget = YuiGrid(self.view)
            self.expected_html = u'<div class="yui-g"></div>'

        @scenario
        def yuiunit1(self):
            self.widget = YuiUnit(self.view)
            self.expected_html = u'<div class="yui-u"></div>'

        @scenario
        def yuiunit1(self):
            self.widget = YuiUnit(self.view, first=True)
            self.expected_html = u'<div class="first yui-u"></div>'
            
    @test(Scenarios)
    def yui_widgets(self, fixture):
        """Different Yui widgets for rendering HTML that it compatible with the Yui CSS framework."""
        tester = WidgetTester(fixture.widget)
        rendered_html = tester.render_html()
        vassert( rendered_html == fixture.expected_html )
        
    @test(WebFixture)
    def twocolumn_page(self, fixture):
        """A simple Yui page with two columns, a header and a footer."""
        widget = TwoColumnPage(fixture.view, title=u'It: $current_title')
        widget.add_default_slot(u'slot1', P.factory())
        tester = WidgetTester(widget)
        
        rendered_html = tester.render_html()
        expected = u'<!DOCTYPE html><html><head><title>It: A view</title></head><body><div id="doc" class="yui-t2"><div id="hd" class="yui-g"><header></header></div><div id="bd" role="main"><div id="yui-main"><div class="yui-b"></div></div><div class="yui-b"></div></div><div id="ft"><footer></footer></div></div></body></html>'
        vassert( rendered_html == expected )
        
        vassert( widget.default_slot_definitions.keys() == [u'slot1'] )
        
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
                super(PopulatedTabbedPanel, self).__init__(view, u'tabbed')
                multi_tab = MultiTab(view, u'multitab name', u'multi-main', P.factory(text=u'main multi tab content'))
                tab1 = Tab(fixture.view, u'tab 1 name', u'multi1', P.factory(text=u'tab 1/1 content'))
                tab2 = Tab(fixture.view, u'tab 2 name', u'multi2', P.factory(text=u'tab 1/2 content'))
                multi_tab.add_tab(tab1)
                multi_tab.add_tab(tab2)
                self.add_tab(multi_tab)

                tab3 = Tab(fixture.view, u'tab 3 name', u'tab3', P.factory(text=u'tab 3 content'))
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
        """A TabbedPanel is a Panel which contains an HMenu and a Panel."""
        fixture.request.query_string = u'tab=tab1'
        tabbed_panel = TabbedPanel(fixture.view, u'tabbed_name')
        tabbed_panel.add_tab(Tab(fixture.view, u'tab 1 name', u'tab1', P.factory(text=u'tab 1 content')))

        tester = WidgetTester(tabbed_panel)

        expected_html = u'''<div id="tabbed_name" class="reahl-tabbedpanel">'''\
                        u'''<ul class="reahl-horizontal reahl-menu">'''\
                        u'''<li class="active"><a href="?tab=tab1" class="reahl-ajaxlink">tab 1 name</a></li>'''\
                        u'''</ul>'''\
                        u'''<div><p>tab 1 content</p></div>'''\
                        u'''</div>'''
        actual = tester.render_html()        
        vassert( actual == expected_html )

    @test(WebFixture)
    def tabs_with_sub_options(self, fixture):
        """A TabbedPanel can have Tabs that are each composed of multiple sub-options."""
        fixture.request.query_string = u'tab=mult2'
        tabbed_panel = TabbedPanel(fixture.view, u'tabbed_name')
        multi_tab = MultiTab(fixture.view, u'tab 1 name', u'multitab-main', P.factory(text=u'multi tab main content'))
        multi_tab.add_tab(Tab(fixture.view, u'multi tab 1', u'mult1', P.factory(text=u'tab 1/1 content')))
        multi_tab.add_tab(Tab(fixture.view, u'multi tab 2', u'mult2', P.factory(text=u'tab 1/2 content')))
        tabbed_panel.add_tab(multi_tab)

        tester = WidgetTester(tabbed_panel)
        
        expected_html = u'''<div id="tabbed_name" class="reahl-tabbedpanel">'''\
                        u'''<ul class="reahl-horizontal reahl-menu">'''\
                        u'''<li class="active"><a href="?tab=multitab-main" class="reahl-ajaxlink">tab 1 name</a>&nbsp;'''\
                        u'''<a class="dropdown-handle">▼</a>'''\
                        u'''<ul class="reahl-menu reahl-vertical">'''\
                        u'''<li><a href="?tab=mult1" class="reahl-ajaxlink">multi tab 1</a></li>'''\
                        u'''<li class="active"><a href="?tab=mult2" class="reahl-ajaxlink">multi tab 2</a></li>'''\
                        u'''</ul>'''\
                        u'''</li>'''\
                        u'''</ul>'''\
                        u'''<div><p>tab 1/2 content</p></div>'''\
                        u'''</div>'''
        actual = tester.render_html()        
        vassert( actual == expected_html )

    class DefaultTabScenarios(WebFixture):
        @scenario
        def specified_on_query_string(self):
            self.request.query_string = u'tab=tab2'
            self.expected_contents = u'<p>tab 2 content</p>'
            self.tab1_active = False
            self.tab2_active = True
            
        @scenario
        def defaulted(self):
            self.request.query_string = u''
            self.expected_contents = u'<p>tab 1 content</p>'
            self.tab1_active = True
            self.tab2_active = False
            
    @test(DefaultTabScenarios)
    def default_active_tab(self, fixture):
        """The first tab is active by default (if the active tab is not indicated in the query_string)."""
        tab1 = Tab(fixture.view, u'tab 1 name', u'tab1', P.factory(text=u'tab 1 content'))
        tab2 = Tab(fixture.view, u'tab 2 name', u'tab2', P.factory(text=u'tab 2 content'))

        tabbed_panel = TabbedPanel(fixture.view, u'tabbed_name')
        tabbed_panel.add_tab(tab1)
        tabbed_panel.add_tab(tab2)

        vassert( tab1.is_active == fixture.tab1_active )
        vassert( tab2.is_active == fixture.tab2_active )

        tester = WidgetTester(tabbed_panel)
        panel_contents = tester.get_html_for('//div/div/*')
        vassert( panel_contents == fixture.expected_contents )

    class DefaultMultiTabScenarios(WebFixture):
        @scenario
        def specified_on_query_string(self):
            self.request.query_string = u'tab=multi2'
            self.expected_contents = u'<p>tab 1/2 content</p>'
            self.multi_tab_active = True
            self.tab1_active = False
            self.tab2_active = True
            self.tab3_active = False
            
        @scenario
        def defaulted(self):
            self.request.query_string = u''
            self.expected_contents = u'<p>multi tab main content</p>'
            self.multi_tab_active = True
            self.tab1_active = False
            self.tab2_active = False
            self.tab3_active = False

        @scenario
        def specified_to_other_tab(self):
            self.request.query_string = u'tab=tab3'
            self.expected_contents = u'<p>tab 3 content</p>'
            self.multi_tab_active = False
            self.tab1_active = False
            self.tab2_active = False
            self.tab3_active = True

    @test(DefaultMultiTabScenarios)
    def default_active_multi_tab(self, fixture):
        """The first item of the first tab is active by default (if the active tab is not indicated in the query_string)."""
        tabbed_panel = TabbedPanel(fixture.view, u'tabbed_panel')
        multi_tab = MultiTab(fixture.view, u'tab 1 name', u'multi-tab', P.factory(text=u'multi tab main content'))
        tab1 = Tab(fixture.view, u'tab 1 name', u'multi1', P.factory(text=u'tab 1/1 content'))
        tab2 = Tab(fixture.view, u'tab 2 name', u'multi2', P.factory(text=u'tab 1/2 content'))
        multi_tab.add_tab(tab1)
        multi_tab.add_tab(tab2)
        tabbed_panel.add_tab(multi_tab)

        tab3 = Tab(fixture.view, u'tab 3 name', u'tab3', P.factory(text=u'tab 3 content'))
        tabbed_panel.add_tab(tab3)

        vassert( multi_tab.is_active == fixture.multi_tab_active )
        vassert( tab1.is_active == fixture.tab1_active )
        vassert( tab2.is_active == fixture.tab2_active )
        vassert( tab3.is_active == fixture.tab3_active )

        tester = WidgetTester(tabbed_panel)
        panel_contents = tester.get_html_for('//div/div/*')
        vassert( panel_contents == fixture.expected_contents )

    @test(TabbedPanelAjaxFixture)
    def switching_panels(self, fixture):
        """The contents registered with the TabbedPanel's active tab are displayed."""
        fixture.reahl_server.set_app(fixture.wsgi_app)
        fixture.driver_browser.open(u'/')

        # by default, the first tab is active and its contents are displayed
        vassert( fixture.driver_browser.wait_for(fixture.tab_is_active, u'multitab name') )
        vassert( fixture.driver_browser.wait_for(fixture.tab_contents_equals, u'<p>main multi tab content</p>') )

        fixture.driver_browser.click(XPath.link_with_text(u'tab 3 name'))
        # tab3 is active and its contents are shown
        vassert( fixture.driver_browser.wait_for(fixture.tab_is_active, u'tab 3 name') )
        vassert( fixture.driver_browser.wait_for(fixture.tab_contents_equals, u'<p>tab 3 content</p>') )

        fixture.driver_browser.mouse_over(XPath.link_with_text(u'multitab name'))
        fixture.driver_browser.click(XPath.link_with_text(u'tab 2 name'))
        # tab2 is active and its contents are shown
        vassert( fixture.driver_browser.wait_for(fixture.tab_is_active, u'tab 2 name') )
        vassert( fixture.driver_browser.wait_for(fixture.tab_contents_equals, u'<p>tab 1/2 content</p>') )

        fixture.driver_browser.click(XPath.link_with_text(u'▼'))
        # clicking on the down arrow does nothing
        vassert( fixture.driver_browser.wait_for(fixture.tab_is_active, u'tab 2 name') )

        fixture.driver_browser.click(XPath.link_with_text(u'multitab name'))
        # the main multitab is active and its contents are shown
        vassert( fixture.driver_browser.wait_for(fixture.tab_is_active, u'multitab name') )
        vassert( fixture.driver_browser.wait_for(fixture.tab_contents_equals, u'<p>main multi tab content</p>') )



class SlidingPanelFixture(WebFixture):
    def new_PopulatedSlidingPanel(self):
        fixture = self
        class PopulatedSlidingPanel(SlidingPanel):
            def __init__(self, view):
                super(PopulatedSlidingPanel, self).__init__(view, u'slide')
                panel0 = Panel(view)
                panel0.add_child(P(view, text=u'Contents for panel 0'))
                self.add_panel(panel0)

                panel1 = Panel(view)
                panel1.add_child(P(view, text=u'Contents for panel 1'))
                self.add_panel(panel1)

        return PopulatedSlidingPanel

    def new_wsgi_app(self):
        return super(SlidingPanelFixture, self).new_wsgi_app(enable_js=True,
                                                           child_factory=self.PopulatedSlidingPanel.factory())
    def panel_is_visible(self, index):
        return self.driver_browser.wait_for_element_visible(XPath.paragraph_containing(u'Contents for panel %s' % index))

    def panel_is_not_visible(self, index):
        return self.driver_browser.wait_for_element_not_visible(XPath.paragraph_containing(u'Contents for panel %s' % index))



@test(SlidingPanelFixture)
def opens_on_selected_index(fixture):
    fixture.reahl_server.set_app(fixture.wsgi_app)
    browser = fixture.driver_browser
    
    browser.open(u'/?index=1')
    vassert( fixture.panel_is_visible(1) )
    

@test(SlidingPanelFixture)
def slide_right(fixture):
    fixture.reahl_server.set_app(fixture.wsgi_app)
    browser = fixture.driver_browser

    browser.open(u'/')
    vassert( fixture.panel_is_visible(0) )

    browser.click(XPath.link_with_text(u'>'))
    vassert( fixture.panel_is_not_visible(0) )
    vassert( fixture.panel_is_visible(1) )

    #wrapping back to start
    browser.click(XPath.link_with_text(u'>'))
    vassert( fixture.panel_is_not_visible(1) )
    vassert( fixture.panel_is_visible(0) )

@test(SlidingPanelFixture)
def slide_left(fixture):
    fixture.reahl_server.set_app(fixture.wsgi_app)
    browser = fixture.driver_browser

    browser.open(u'/')
    vassert( fixture.panel_is_visible(0) )

    #wrapping
    browser.click(XPath.link_with_text(u'<'))
    vassert( fixture.panel_is_not_visible(0) )
    vassert( fixture.panel_is_visible(1) )

    browser.click(XPath.link_with_text(u'<'))
    vassert( fixture.panel_is_not_visible(1) )
    vassert( fixture.panel_is_visible(0) )

class PopupAFixture(WebFixture):
    # (note that this xpath ensures that the p is the ONLY content of the dialog)
    poppedup_contents = u"//div[@class='reahl-dialogcontent' and count(*)=1]/p[@id='contents']"
    

@istest
class PopupATests(object):
    @test(PopupAFixture)
    def default_behaviour(self, fixture):
        """If you click on the A, a popupwindow opens with its contents the specified
           element on the target page."""

        class PopupTestPanel(Panel):
            def __init__(self, view):
                super(PopupTestPanel, self).__init__(view)
                self.add_child(PopupA(view, view.as_bookmark(), u'#contents'))
                popup_contents = self.add_child(P(view, text=u'this is the content of the popup'))
                popup_contents.set_id(u'contents')

        wsgi_app = fixture.new_wsgi_app(child_factory=PopupTestPanel.factory(), enable_js=True)
        fixture.reahl_server.set_app(wsgi_app)
        fixture.driver_browser.open('/')
        
        # The A is rendered correctly
        fixture.driver_browser.is_element_present(u"//a[@title='Home page' and text()='Home page' and @href='/']")

        # subsequent behaviour
        fixture.driver_browser.click(XPath.link_with_text(u'Home page'))
        fixture.driver_browser.wait_for_element_visible(fixture.poppedup_contents)
        
        fixture.driver_browser.click(XPath.button_labelled(u'Close'))
        fixture.driver_browser.wait_for_element_not_visible(fixture.poppedup_contents)

    @test(PopupAFixture)
    def customising_dialog_buttons(self, fixture):
        """The buttons of the dialog can be customised."""
        
        class PopupTestPanel(Panel):
            def __init__(self, view):
                super(PopupTestPanel, self).__init__(view)
                popup_a = self.add_child(PopupA(view, view.as_bookmark(), u'#contents'))
                popup_a.add_button(DialogButton(u'Butt1'))
                popup_a.add_button(DialogButton(u'Butt2'))
                popup_contents = self.add_child(P(view, text=u'this is the content of the popup'))
                popup_contents.set_id(u'contents')

        wsgi_app = fixture.new_wsgi_app(child_factory=PopupTestPanel.factory(), enable_js=True)
        fixture.reahl_server.set_app(wsgi_app)

        button1_xpath = XPath.button_labelled(u'Butt1')
        button2_xpath = XPath.button_labelled(u'Butt2')
        fixture.driver_browser.open('/')

        fixture.driver_browser.click(XPath.link_with_text(u'Home page'))
        fixture.driver_browser.wait_for_element_visible(fixture.poppedup_contents)

        vassert( fixture.driver_browser.is_element_present(button1_xpath) )
        vassert( fixture.driver_browser.is_element_present(button2_xpath) )

    @test(PopupAFixture)
    def workings_of_check_checkbox_button(self, fixture):
        """A CheckCheckBoxButton checks the checkbox on the original page when clicked."""
        
        class PopupTestPanel(Panel):
            @exposed
            def fields(self, fields):
                fields.field = BooleanField()
                
            def __init__(self, view):
                super(PopupTestPanel, self).__init__(view)
                popup_a = self.add_child(PopupA(view, view.as_bookmark(), u'#contents'))
                popup_contents = self.add_child(P(view, text=u'this is the content of the popup'))
                popup_contents.set_id(u'contents')
                form = self.add_child(Form(view, u'aform'))
                checkbox = form.add_child(CheckboxInput(form, self.fields.field))

                popup_a.add_button(CheckCheckboxButton(u'Checkit', checkbox))

        wsgi_app = fixture.new_wsgi_app(child_factory=PopupTestPanel.factory(), enable_js=True)
        fixture.reahl_server.set_app(wsgi_app)

        button_xpath = XPath.button_labelled(u'Checkit')
        fixture.driver_browser.open('/')

        fixture.driver_browser.click(XPath.link_with_text(u'Home page'))
        fixture.driver_browser.wait_for_element_visible(fixture.poppedup_contents)

        fixture.driver_browser.click(button_xpath)
        fixture.driver_browser.wait_for_element_not_visible(fixture.poppedup_contents)

        vassert( fixture.driver_browser.is_checked(u"//input[@type='checkbox']") )




