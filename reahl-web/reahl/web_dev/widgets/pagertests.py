# Copyright 2010-2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from __future__ import unicode_literals
from __future__ import print_function
import six
from reahl.stubble import stubclass
from nose.tools import istest
from reahl.tofu import Fixture
from reahl.tofu import scenario
from reahl.tofu import test
from reahl.tofu import vassert

from reahl.webdev.tools import XPath
from reahl.web.ui import P
from reahl.web.ui import Panel
from reahl.web.pager import PageIndex
from reahl.web.pager import PageMenu
from reahl.web.pager import PagedPanel
from reahl.web_dev.fixtures import WebBasicsMixin

from reahl.web.pager import SequentialPageIndex, AnnualPageIndex, AnnualItemOrganiserProtocol

class PageMenuFixture(Fixture, WebBasicsMixin):
    def new_number_of_pages(self):
        return 10
        
    def new_max_page_links(self):
        return 5
        
    def new_PageIndexStub(self):
        fixture = self
        @stubclass(PageIndex)
        class PageIndexStub(PageIndex):
            def __init__(self, max_page_links, number_of_pages):
                super(PageIndexStub, self).__init__(max_page_links=max_page_links)
                self.number_of_pages = number_of_pages

            @property
            def total_number_of_pages(self):
                return self.number_of_pages
            
            def get_contents_for_page(self, page_number):
                return 'contents of page %s' % page_number

            def get_description_for_page(self, page_number):
                return 'p%s' % page_number

        return PageIndexStub
        
    def new_PageContainer(self):
        class PageContainer(PagedPanel):
            def __init__(self, parent, page_index):
                super(PageContainer, self).__init__(parent, page_index, 'container')
                self.add_child(P(self.view, text=self.current_contents))

        return PageContainer

    def new_MainWidget(self):
        fixture = self
        class MainWidget(Panel):
            def __init__(self, view):
                super(MainWidget, self).__init__(view)
                page_index = fixture.PageIndexStub(fixture.max_page_links, fixture.number_of_pages)
                page_container = self.add_child(fixture.PageContainer(self.view, page_index))
                self.add_child(PageMenu(self.view, 'page_menu_widget', page_index, page_container))
        return MainWidget
        
    def container_contents_is(self, expected):
        return self.driver_browser.execute_script('return window.jQuery("div p").html() == "%s"' % expected)

    def page_range_links_match(self, link_labels):
        return self.driver_browser.execute_script('return window.jQuery(".reahl-pagemenu a").slice(2,-2).map(function(){return window.jQuery(this).html();}).toArray() == "%s"' % link_labels)

    def new_wsgi_app(self):
        return super(PageMenuFixture, self).new_wsgi_app(enable_js=True, 
                                                       child_factory=self.MainWidget.factory())


@istest
class PageMenuTests(object):
    # Please see fixture for how to declare a PageIndex, PageContainer and PageMenu
    @test(PageMenuFixture)
    def selecting_a_page(self, fixture):
        """Clicking the link of a page results in the contents of the PageContainer being refreshed."""
        fixture.reahl_server.set_app(fixture.wsgi_app)
        fixture.driver_browser.open('/')

        fixture.driver_browser.wait_for(fixture.container_contents_is, 'contents of page 1')
        fixture.driver_browser.click(XPath.link_with_text('p2'))
        fixture.driver_browser.wait_for(fixture.container_contents_is, 'contents of page 2')

    @test(PageMenuFixture)
    def navigating_the_page_numbers(self, fixture):
        """One can navigate the range of page links displayed by the PageMenu using the special links."""
        fixture.number_of_pages = 30
        fixture.max_page_links = 5
        fixture.reahl_server.set_app(fixture.wsgi_app)
        fixture.driver_browser.open('/')

        # Case: next link
        fixture.driver_browser.click(XPath.link_with_text('>'))
        vassert( fixture.driver_browser.wait_for(fixture.page_range_links_match, 'p6,p7,p8,p9,p10') )
        fixture.driver_browser.click(XPath.link_with_text('>'))
        vassert( fixture.driver_browser.wait_for(fixture.page_range_links_match, 'p11,p12,p13,p14,p15') )

        # Case: prev link
        fixture.driver_browser.click(XPath.link_with_text('<'))
        vassert( fixture.driver_browser.wait_for(fixture.page_range_links_match, 'p6,p7,p8,p9,p10') )

        # Case: last link
        fixture.driver_browser.click(XPath.link_with_text('>|'))
        vassert( fixture.driver_browser.wait_for(fixture.page_range_links_match, 'p26,p27,p28,p29,p30') )

        # Case: first link
        fixture.driver_browser.click(XPath.link_with_text('|<'))
        vassert( fixture.driver_browser.wait_for(fixture.page_range_links_match, 'p1,p2,p3,p4,p5') )

    @test(PageMenuFixture)
    def contents_when_navigating_the_page_numbers(self, fixture):
        """When navigating the range of page links, the currently displayed contents stay unchanged."""
        fixture.number_of_pages = 30
        fixture.max_page_links = 5
        fixture.reahl_server.set_app(fixture.wsgi_app)
        fixture.driver_browser.open('/')

        fixture.driver_browser.click(XPath.link_with_text('p2'))
        fixture.driver_browser.wait_for(fixture.container_contents_is, 'contents of page 2')
        fixture.driver_browser.click(XPath.link_with_text('>'))
        fixture.driver_browser.wait_for(fixture.container_contents_is, 'contents of page 2')

    @test(PageMenuFixture)
    def active_state_of_next_prev_links(self, fixture):
        """Next and Last links are only active when not on the last range of pages,
           and Prev and First are similarly deactive when on the first range of pages."""
        fixture.number_of_pages = 15
        fixture.max_page_links = 5
        fixture.reahl_server.set_app(fixture.wsgi_app)
        fixture.driver_browser.open('/')

        # Case: when you are on the left of the page range        
        vassert( not fixture.driver_browser.is_active(XPath.link_with_text('|<')) )
        vassert( not fixture.driver_browser.is_active(XPath.link_with_text('<')) )
        vassert( fixture.driver_browser.is_active(XPath.link_with_text('>')) )
        vassert( fixture.driver_browser.is_active(XPath.link_with_text('>|')) )

        # Case: when you are in the middle of the page range        
        fixture.driver_browser.click(XPath.link_with_text('>'))
        fixture.driver_browser.wait_for_element_present(XPath.link_with_text('p6'))
        vassert( fixture.driver_browser.is_active(XPath.link_with_text('|<')) )
        vassert( fixture.driver_browser.is_active(XPath.link_with_text('<')) )
        vassert( fixture.driver_browser.is_active(XPath.link_with_text('>')) )
        vassert( fixture.driver_browser.is_active(XPath.link_with_text('>|')) )
        
        # Case: when you are at the end of the page range        
        fixture.driver_browser.click(XPath.link_with_text('>'))
        fixture.driver_browser.wait_for_element_present(XPath.link_with_text('p11'))
        vassert( fixture.driver_browser.is_active(XPath.link_with_text('|<')) )
        vassert( fixture.driver_browser.is_active(XPath.link_with_text('<')) )
        vassert( not fixture.driver_browser.is_active(XPath.link_with_text('>')) )
        vassert( not fixture.driver_browser.is_active(XPath.link_with_text('>|')) )

    class LinkScenarios(PageMenuFixture):
        @scenario
        def only_one_page(self):
            self.number_of_pages = 1
            self.max_page_links = 5
            self.goto_last_range = False
            self.visible_page_descriptions = 'p1'
            self.visible_last_page_descriptions = self.visible_page_descriptions

        @scenario
        def fewer_pages_than_max_links(self):
            self.number_of_pages = 2
            self.max_page_links = 5
            self.goto_last_range = False
            self.visible_page_descriptions = 'p1,p2'
            self.visible_last_page_descriptions = self.visible_page_descriptions

        @scenario
        def more_pages_than_max_links(self):
            self.number_of_pages = 10
            self.max_page_links = 5
            self.goto_last_range = True
            self.visible_page_descriptions = 'p1,p2,p3,p4,p5'
            self.visible_last_page_descriptions = 'p6,p7,p8,p9,p10'

        @scenario
        def more_than_one_range_last_range_not_complete(self):
            self.number_of_pages = 7
            self.max_page_links = 5
            self.goto_last_range = True
            self.visible_page_descriptions = 'p1,p2,p3,p4,p5'
            self.visible_last_page_descriptions = 'p3,p4,p5,p6,p7'

        @scenario
        def changing_number_of_links(self):
            self.number_of_pages = 10
            self.max_page_links = 3
            self.goto_last_range = False
            self.visible_page_descriptions = 'p1,p2,p3'
            self.visible_last_page_descriptions = self.visible_page_descriptions

    @test(LinkScenarios)
    def which_links_display(self, fixture):
        """The menu displayes the correct range of page links, depending on the starting page in the range, the
           total number of pages and the max number of links in a range"""
        fixture.reahl_server.set_app(fixture.wsgi_app)

        fixture.driver_browser.open('/')
        vassert( fixture.driver_browser.wait_for(fixture.page_range_links_match, fixture.visible_page_descriptions) )

        if fixture.goto_last_range:
            fixture.driver_browser.click(XPath.link_with_text('>|'))

        vassert( fixture.driver_browser.wait_for(fixture.page_range_links_match, fixture.visible_last_page_descriptions) )

    @test(Fixture)
    def annual_page_index(self, fixture):
        """The AnnualPageIndex breaks a query of items up into pages containing items with the same year."""
        
        @stubclass(AnnualItemOrganiserProtocol)
        class ItemOrganiser(AnnualItemOrganiserProtocol):
            def get_years(self):                return [2000, 2001]
            def get_items_for_year(self, year): return [year]*3

        page_index = AnnualPageIndex(ItemOrganiser())

        vassert( page_index.get_contents_for_page(2) == [2001, 2001, 2001] )
        vassert( page_index.get_description_for_page(1) == '2000' )
        vassert( page_index.years == [2000, 2001] )
        vassert( page_index.total_number_of_pages == 2 )


    class SequentialScenarios(Fixture):
        def new_items(self):
            return list(range(0, self.number_of_items))

        def new_page_index(self):
            return SequentialPageIndex(self.items, items_per_page=self.items_per_page, max_page_links=12)
            
        @scenario
        def less_than_a_page_items(self):
            self.number_of_items = 2
            self.items_per_page = 10
            self.expected_pages = 1
            self.last_page_contents = self.items[0:2]

        @scenario
        def exactly_one_page_items(self):
            self.number_of_items = 10
            self.items_per_page = 10
            self.expected_pages = 1
            self.last_page_contents = self.items[0:10]

        @scenario
        def just_more_than_one_page_items(self):
            self.number_of_items = 15
            self.items_per_page = 10
            self.expected_pages = 2
            self.last_page_contents = self.items[10:15]
        
    @test(SequentialScenarios)
    def sequential_page_index(self, fixture):
        """The SequentialPageIndex breaks a query of items up into pages of sequential items"""
        
        vassert( fixture.page_index.total_number_of_pages == fixture.expected_pages )
        page = fixture.page_index.get_page_number(fixture.expected_pages)
        vassert( page.description == six.text_type(fixture.expected_pages) )
        vassert( page.contents == fixture.last_page_contents )        
        vassert( fixture.page_index.max_page_links == 12 )


