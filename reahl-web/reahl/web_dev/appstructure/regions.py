# Copyright 2011, 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
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
from reahl.tofu import Fixture, test
from reahl.tofu import vassert, expected
from reahl.stubble import stubclass, EmptyStub

from reahl.web.fw import Region, Widget, FactoryDict, RegionFactory, RegexPath
from reahl.web.ui import TwoColumnPage, P, A, Panel, Slot
from reahl.webdev.tools import Browser, WidgetTester
from reahl.web_dev.fixtures import WebFixture


@istest
class RegionTests(object):
    @test(WebFixture)
    def basic_region(self, fixture):
        """A Region is a chunk of web app that can be grafted onto the URL hierarchy of any app.
        
           A Region has its own views. Its Views are relative to the Region itself.
        """
        class RegionWithTwoViews(Region):
            def assemble(self):
                self.define_view(u'/', title=u'Region root view')
                self.define_view(u'/other', title=u'Region other view')

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/aregion',  RegionWithTwoViews,  {}, name=u'myregion')

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)

        browser.open('/aregion/')
        vassert( browser.title == u'Region root view' )

        browser.open('/aregion/other')
        vassert( browser.title == u'Region other view' )

    @test(WebFixture)
    def region_slots_map_to_window(self, fixture):
        """The Region uses its own names for Slots. When attaching a Region, you have to specify 
            which of the Region's Slots plug into which of the main window's Slots.
        """
        class RegionWithSlots(Region):
            def assemble(self):
                root = self.define_view(u'/', title=u'Region root view')
                root.set_slot(u'text', P.factory(text=u'in region slot named text'))

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/aregion',  RegionWithSlots,  {u'text': u'main'}, name='myregion')

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)

        browser.open('/aregion/')
        vassert( browser.title == u'Region root view' )

        # The widget in the Region's slot named 'text' end up in the TwoColumnPage slot called main
        [p] = browser.lxml_html.xpath('//div[@id="yui-main"]/div/p')
        vassert( p.text == 'in region slot named text' )


    @test(WebFixture)
    def region_redirect(self, fixture):
        """When opening an URL without trailing slash that maps to where a Region is attached,
           the browser is redirected to the Region '/' View."""
           
        class RegionWithRootView(Region):
            def assemble(self):
                self.define_view(u'/', title=u'Region root view')

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/aregion',  RegionWithRootView,  {}, name='myregion')

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)

        browser.open('/aregion')
        vassert( browser.title == u'Region root view' )
        vassert( browser.location_path == u'/aregion/' )

    @test(WebFixture)
    def region_arguments(self, fixture):
        """Regions can take exta args and kwargs."""
           
        class RegionWithArguments(Region):
            def assemble(self, kwarg=None):
                self.kwarg = kwarg
                text = self.kwarg
                root = self.define_view(u'/', title=u'A view')
                root.set_slot(u'text', P.factory(text=text))

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/aregion', RegionWithArguments, {u'text': u'main'},
                                name='myregion', kwarg=u'the kwarg')

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)

        browser.open('/aregion/')
        [p] = browser.lxml_html.xpath('//p')
        vassert( p.text == 'the kwarg' )

    @test(WebFixture)
    def bookmarks(self, fixture):
        """Bookmarks are pointers to Views. You need them, because Views are relative to a Region and
           a Bookmark can, at run time, turn these into absolute URLs. Bookmarks also contain metadata,
           such as the title of the View it points to.
        """
        class RegionWithRelativeView(Region):
            def assemble(self):
                self.define_view(u'/aview', title=u'A View title')

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                region_factory = self.define_region(u'/aregion',  RegionWithRelativeView,  {}, name=u'myregion')

                # How you could get a bookmark from a RegionFactory
                fixture.bookmark = region_factory.get_bookmark(relative_path=u'/aview')

        webapp = fixture.new_webapp(site_root=MainRegion)
        Browser(webapp).open('/aregion/aview') # To execute the above once

        # What the bookmark knows
        vassert( fixture.bookmark.href.path == u'/aregion/aview' )
        vassert( fixture.bookmark.description == u'A View title' )
        vassert( fixture.bookmark.base_path == u'/aregion' )
        vassert( fixture.bookmark.relative_path == u'/aview' )

        # How you would use a bookmark in other views (possibly in other regions)
        a = A.from_bookmark(fixture.view, fixture.bookmark)
        
        # .. and how the A will be rendered
        a_etree = WidgetTester(a).render_html_tree()        
        vassert( a_etree.attrib[u'href'] == u'/aregion/aview' )
        vassert( a_etree.text == u'A View title' )

    class LifeCycleFixture(WebFixture):
        def current_view_is_plugged_in(self, main_window):
            return main_window.slot_contents[u'main_slot'].__class__ is Panel

    @test(LifeCycleFixture)
    def the_lifecycle_of_a_region(self, fixture):
        """This test illustrates the steps a Region goes through from being specified, to
           being used. It tests a couple of lower-level implementation issues (see comments)."""

        @stubclass(Region)
        class RegionStub(Region):
            assembled = False
            def assemble(self, **region_arguments):
                self.controller_at_assemble_time = self.controller
                root = self.define_view(u'/some/path', title=u'A view')
                root.set_slot(u'slotA', Panel.factory())
                self.assembled = True

        # Phase1: specifying a region and assembleing it to a site (with kwargs)
        parent_region = None
#        parent_region = EmptyStub(base_path=u'/')
        slot_map = {u'slotA': u'main_slot'}
        region_factory = RegionFactory(parent_region, RegexPath(u'/', u'/', {}), slot_map, RegionStub, u'test_region')


        # Phase2: creating a region
        request = Request.blank(u'/some/path')
        fixture.context.set_request(request)
        region = region_factory.create(u'/some/path', for_bookmark=False)

        # - Assembly happened correctly
        vassert( region.parent_region is parent_region )
        vassert( region.slot_map is slot_map )
        vassert( region.name is u'test_region' )
        vassert( region.relative_base_path == u'/' )
        vassert( region.controller_at_assemble_time is not None)
        vassert( region.controller is not None )
        vassert( region.assembled )

        # - Create for_bookmark empties the relative_path
        region = region_factory.create(u'/some/path', for_bookmark=True)
        vassert( region.relative_path == u'' )

        # - The relative_path is reset if not done for_bookmark
        #   This is done in case a for_bookmark call just
        #   happened to be done for the same Region in the same request
        #   before the "real" caal is done
        region = region_factory.create(u'/some/path', for_bookmark=False)
        vassert( region.relative_path == u'/some/path' )

        # Phase5: create the main_window and plug the view into it
        main_window = Widget.factory().create(region.current_view)
        main_window.add_child(Slot(region.current_view, 'main_slot'))

        main_window.plug_in(region.current_view)
        vassert( fixture.current_view_is_plugged_in(main_window) )
        vassert( isinstance(region.sub_resources, FactoryDict) )
