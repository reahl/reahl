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

from reahl.web.fw import UserInterface, Widget, FactoryDict, UserInterfaceFactory, RegexPath
from reahl.web.fw import Region
from reahl.web.ui import TwoColumnPage, P, A, Panel, Slot
from reahl.webdev.tools import Browser, WidgetTester
from reahl.web_dev.fixtures import WebFixture


@istest
class UserInterfaceTests(object):
    @test(WebFixture)
    def basic_ui(self, fixture):
        """A UserInterface is a chunk of web app that can be grafted onto the URL hierarchy of any app.
        
           A UserInterface has its own views. Its Views are relative to the UserInterface itself.
        """
        class UIWithTwoViews(UserInterface):
            def assemble(self):
                self.define_view(u'/', title=u'UserInterface root view')
                self.define_view(u'/other', title=u'UserInterface other view')

        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                self.define_user_interface(u'/a_ui',  UIWithTwoViews,  {}, name=u'myui')

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        browser.open('/a_ui/')
        vassert( browser.title == u'UserInterface root view' )

        browser.open('/a_ui/other')
        vassert( browser.title == u'UserInterface other view' )

    @test(WebFixture)
    def backwards_compatibility(self, fixture):
        """For backwards compatibility, there are aliases for new names:
             
             - UserInterface is Region
             - .define_user_interface() is define_region()
             - .define_page() is define_main_window()
        """
        class UIWithAView(UserInterface):
            def assemble(self):
                self.define_view(u'/aview', title=u'UserInterface view')

        class MainUI(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/a_ui',  UIWithAView,  {}, name=u'myui')

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        browser.open('/a_ui/aview')
        vassert( browser.title == u'UserInterface view' )

    @test(WebFixture)
    def ui_slots_map_to_window(self, fixture):
        """The UserInterface uses its own names for Slots. When attaching a UserInterface, you have to specify 
            which of the UserInterface's Slots plug into which of the page's Slots.
        """
        class UIWithSlots(UserInterface):
            def assemble(self):
                root = self.define_view(u'/', title=u'UserInterface root view')
                root.set_slot(u'text', P.factory(text=u'in user_interface slot named text'))

        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                self.define_user_interface(u'/a_ui',  UIWithSlots,  {u'text': u'main'}, name='myui')

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        browser.open('/a_ui/')
        vassert( browser.title == u'UserInterface root view' )

        # The widget in the UserInterface's slot named 'text' end up in the TwoColumnPage slot called main
        [p] = browser.lxml_html.xpath('//div[@id="yui-main"]/div/p')
        vassert( p.text == 'in user_interface slot named text' )


    @test(WebFixture)
    def ui_redirect(self, fixture):
        """When opening an URL without trailing slash that maps to where a UserInterface is attached,
           the browser is redirected to the UserInterface '/' View."""
           
        class UIWithRootView(UserInterface):
            def assemble(self):
                self.define_view(u'/', title=u'UserInterface root view')

        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                self.define_user_interface(u'/a_ui',  UIWithRootView,  {}, name='myui')

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        browser.open('/a_ui')
        vassert( browser.title == u'UserInterface root view' )
        vassert( browser.location_path == u'/a_ui/' )

    @test(WebFixture)
    def ui_arguments(self, fixture):
        """UserInterfaces can take exta args and kwargs."""
           
        class UIWithArguments(UserInterface):
            def assemble(self, kwarg=None):
                self.kwarg = kwarg
                text = self.kwarg
                root = self.define_view(u'/', title=u'A view')
                root.set_slot(u'text', P.factory(text=text))

        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                self.define_user_interface(u'/a_ui', UIWithArguments, {u'text': u'main'},
                                name='myui', kwarg=u'the kwarg')

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        browser.open('/a_ui/')
        [p] = browser.lxml_html.xpath('//p')
        vassert( p.text == 'the kwarg' )

    @test(WebFixture)
    def bookmarks(self, fixture):
        """Bookmarks are pointers to Views. You need them, because Views are relative to a UserInterface and
           a Bookmark can, at run time, turn these into absolute URLs. Bookmarks also contain metadata,
           such as the title of the View it points to.
        """
        class UIWithRelativeView(UserInterface):
            def assemble(self):
                self.define_view(u'/aview', title=u'A View title')

        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                ui_factory = self.define_user_interface(u'/a_ui',  UIWithRelativeView,  {}, name=u'myui')

                # How you could get a bookmark from a UserInterfaceFactory
                fixture.bookmark = ui_factory.get_bookmark(relative_path=u'/aview')

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        Browser(wsgi_app).open('/a_ui/aview') # To execute the above once

        # What the bookmark knows
        vassert( fixture.bookmark.href.path == u'/a_ui/aview' )
        vassert( fixture.bookmark.description == u'A View title' )
        vassert( fixture.bookmark.base_path == u'/a_ui' )
        vassert( fixture.bookmark.relative_path == u'/aview' )

        # How you would use a bookmark in other views (possibly in other UserInterfaces)
        a = A.from_bookmark(fixture.view, fixture.bookmark)
        
        # .. and how the A will be rendered
        a_etree = WidgetTester(a).render_html_tree()        
        vassert( a_etree.attrib[u'href'] == u'/a_ui/aview' )
        vassert( a_etree.text == u'A View title' )

    class LifeCycleFixture(WebFixture):
        def current_view_is_plugged_in(self, page):
            return page.slot_contents[u'main_slot'].__class__ is Panel

    @test(LifeCycleFixture)
    def the_lifecycle_of_a_ui(self, fixture):
        """This test illustrates the steps a UserInterface goes through from being specified, to
           being used. It tests a couple of lower-level implementation issues (see comments)."""

        @stubclass(UserInterface)
        class UserInterfaceStub(UserInterface):
            assembled = False
            def assemble(self, **ui_arguments):
                self.controller_at_assemble_time = self.controller
                root = self.define_view(u'/some/path', title=u'A view')
                root.set_slot(u'slotA', Panel.factory())
                self.assembled = True

        # Phase1: specifying a user_interface and assembleing it to a site (with kwargs)
        parent_ui = None
#        parent_ui = EmptyStub(base_path=u'/')
        slot_map = {u'slotA': u'main_slot'}
        ui_factory = UserInterfaceFactory(parent_ui, RegexPath(u'/', u'/', {}), slot_map, UserInterfaceStub, u'test_ui')


        # Phase2: creating a user_interface
        request = Request.blank(u'/some/path')
        fixture.context.set_request(request)
        user_interface = ui_factory.create(u'/some/path', for_bookmark=False)

        # - Assembly happened correctly
        vassert( user_interface.parent_ui is parent_ui )
        vassert( user_interface.slot_map is slot_map )
        vassert( user_interface.name is u'test_ui' )
        vassert( user_interface.relative_base_path == u'/' )
        vassert( user_interface.controller_at_assemble_time is not None)
        vassert( user_interface.controller is not None )
        vassert( user_interface.assembled )

        # - Create for_bookmark empties the relative_path
        user_interface = ui_factory.create(u'/some/path', for_bookmark=True)
        vassert( user_interface.relative_path == u'' )

        # - The relative_path is reset if not done for_bookmark
        #   This is done in case a for_bookmark call just
        #   happened to be done for the same UserInterface in the same request
        #   before the "real" caal is done
        user_interface = ui_factory.create(u'/some/path', for_bookmark=False)
        vassert( user_interface.relative_path == u'/some/path' )

        # Phase5: create the page and plug the view into it
        page = Widget.factory().create(user_interface.current_view)
        page.add_child(Slot(user_interface.current_view, 'main_slot'))

        page.plug_in(user_interface.current_view)
        vassert( fixture.current_view_is_plugged_in(page) )
        vassert( isinstance(user_interface.sub_resources, FactoryDict) )
