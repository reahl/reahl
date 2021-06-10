# Copyright 2013-2021 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.stubble import stubclass
from reahl.tofu.pytestsupport import with_fixtures

from reahl.browsertools.browsertools import Browser

from reahl.web.fw import UserInterface, Widget, FactoryDict, UserInterfaceFactory, RegexPath, UrlBoundView
from reahl.web.ui import HTML5Page, P, A, Div, Slot

from reahl.web_dev.fixtures import WebFixture, BasicPageLayout


@with_fixtures(WebFixture)
def test_basic_ui(web_fixture):
    """A UserInterface is a chunk of web app that can be grafted onto the URL hierarchy of any app.

       A UserInterface has its own views. Its Views are relative to the UserInterface itself.
    """
    class UIWithTwoViews(UserInterface):
        def assemble(self):
            self.define_view('/', title='UserInterface root view')
            self.define_view('/other', title='UserInterface other view')

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page)
            self.define_user_interface('/a_ui',  UIWithTwoViews,  {}, name='myui')

    fixture = web_fixture
    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    browser.open('/a_ui/')
    assert browser.title == 'UserInterface root view' 

    browser.open('/a_ui/other')
    assert browser.title == 'UserInterface other view' 


@with_fixtures(WebFixture)
def test_ui_slots_map_to_window(web_fixture):
    """The UserInterface uses its own names for Slots. When attaching a UserInterface, you have to specify 
        which of the UserInterface's Slots plug into which of the page's Slots.
    """
    class UIWithSlots(UserInterface):
        def assemble(self):
            root = self.define_view('/', title='UserInterface root view')
            root.set_slot('text', P.factory(text='in user_interface slot named text'))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            self.define_user_interface('/a_ui',  UIWithSlots,  {'text': 'main'}, name='myui')

    fixture = web_fixture

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    browser.open('/a_ui/')
    assert browser.title == 'UserInterface root view' 

    # The widget in the UserInterface's slot named 'text' end up in the HTML5Page slot called main
    [p] = browser.lxml_html.xpath('//div[contains(@class,"column-main")]/p')
    assert p.text == 'in user_interface slot named text' 


@with_fixtures(WebFixture)
def test_ui_redirect(web_fixture):
    """When opening an URL without trailing slash that maps to where a UserInterface is attached,
       the browser is redirected to the UserInterface '/' View."""

    class UIWithRootView(UserInterface):
        def assemble(self):
            self.define_view('/', title='UserInterface root view')

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page)
            self.define_user_interface('/a_ui',  UIWithRootView,  {}, name='myui')

    fixture = web_fixture

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    browser.open('/a_ui')
    assert browser.title == 'UserInterface root view' 
    assert browser.current_url.path == '/a_ui/' 


@with_fixtures(WebFixture)
def test_ui_arguments(web_fixture):
    """UserInterfaces can take exta args and kwargs."""

    class UIWithArguments(UserInterface):
        def assemble(self, kwarg=None):
            self.kwarg = kwarg
            text = self.kwarg
            root = self.define_view('/', title='A view')
            root.set_slot('text', P.factory(text=text))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            self.define_user_interface('/a_ui', UIWithArguments, {'text': 'main'},
                            name='myui', kwarg='the kwarg')

    fixture = web_fixture

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    browser.open('/a_ui/')
    [p] = browser.lxml_html.xpath('//p')
    assert p.text == 'the kwarg' 


@with_fixtures(WebFixture)
def test_bookmarks(web_fixture):
    """Bookmarks are pointers to Views. You need them, because Views are relative to a UserInterface and
       a Bookmark can, at run time, turn these into absolute URLs. Bookmarks also contain metadata,
       such as the title of the View it points to.
    """
    fixture = web_fixture
    user_interface = UserInterface(None, '/a_ui', {}, False, 'test_ui')
    view = UrlBoundView(user_interface, '/aview', 'A View title')
    bookmark = view.as_bookmark()

    # What the bookmark knows
    assert bookmark.href.path == '/a_ui/aview' 
    assert bookmark.description == 'A View title' 
    assert bookmark.base_path == '/a_ui' 
    assert bookmark.relative_path == '/aview' 

    # How you would use a bookmark in other views (possibly in other UserInterfaces)
    a = A.from_bookmark(fixture.view, bookmark)
    assert str(a.href) == str(bookmark.href) 


@with_fixtures(WebFixture)
def test_bookmarks_overrides(web_fixture):
    """Various bits of information can be overridden from the defaults when creating a bookmark from a View.
    """
    fixture = web_fixture

    user_interface = UserInterface(None, '/a_ui', {}, False, 'test_ui')
    view = UrlBoundView(user_interface, '/aview', 'A View title')
    bookmark = view.as_bookmark(description='different description',
                                query_arguments={'arg1': 'val1'},
                                locale='af')

    # What the bookmark knows
    assert bookmark.description == 'different description' 
    assert bookmark.query_arguments == {'arg1': 'val1'} 
    assert bookmark.locale == 'af' 


@with_fixtures(WebFixture)
def test_bookmarks_from_other_sources(web_fixture):
    """Bookmarks can also be made from ViewFactories, UserInterfaces or UserInterfaceFactories. 
    """
    fixture = web_fixture

    class UIWithRelativeView(UserInterface):
        def assemble(self):
            view_factory = self.define_view('/aview', title='A View title')

            # How you could get a bookmark from a UserInterface or ViewFactory
            fixture.bookmark_from_view_factory = view_factory.as_bookmark(self)
            fixture.bookmark_from_ui = self.get_bookmark(relative_path='/aview')

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page)
            fixture.ui_factory = self.define_user_interface('/a_ui',  UIWithRelativeView,  {}, name='myui')

            # How you could get a bookmark from a UserInterfaceFactory
            fixture.bookmark_from_ui_factory = fixture.ui_factory.get_bookmark(relative_path='/aview')

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    Browser(wsgi_app).open('/a_ui/aview') # To execute the above once

    for bookmark in [fixture.bookmark_from_view_factory, 
                     fixture.bookmark_from_ui, 
                     fixture.bookmark_from_ui_factory]:
        # What the bookmark knows
        assert bookmark.href.path == '/a_ui/aview' 
        assert bookmark.description == 'A View title' 
        assert bookmark.base_path == '/a_ui' 
        assert bookmark.relative_path == '/aview' 


@with_fixtures(WebFixture)
def test_the_lifecycle_of_a_ui(web_fixture):
    """This test illustrates the steps a UserInterface goes through from being specified, to
       being used. It tests a couple of lower-level implementation issues (see comments)."""

    def current_view_is_plugged_in(page):
        return page.slot_contents['main_slot'].__class__ is Div

    @stubclass(UserInterface)
    class UserInterfaceStub(UserInterface):
        assembled = False
        def assemble(self, **ui_arguments):
            self.controller_at_assemble_time = self.controller
            root = self.define_view('/some/path', title='A view')
            root.set_slot('slotA', Div.factory())
            self.assembled = True

    fixture = web_fixture

    # Phase1: specifying a user_interface and assembleing it to a site (with kwargs)
    parent_ui = None
#        parent_ui = EmptyStub(base_path='/')
    slot_map = {'slotA': 'main_slot'}
    ui_factory = UserInterfaceFactory(parent_ui, RegexPath('/', '/', {}), slot_map, UserInterfaceStub, 'test_ui')


    # Phase2: creating a user_interface
    request = Request.blank('/some/path')
    fixture.context.request = request
    user_interface = ui_factory.create('/some/path', for_bookmark=False)

    # - Assembly happened correctly
    assert user_interface.parent_ui is parent_ui 
    assert user_interface.slot_map is slot_map 
    assert user_interface.name is 'test_ui' 
    assert user_interface.relative_base_path == '/' 
    assert user_interface.controller_at_assemble_time is not None
    assert user_interface.controller is not None 
    assert user_interface.assembled 

    # - Create for_bookmark empties the relative_path
    user_interface = ui_factory.create('/some/path', for_bookmark=True)
    assert user_interface.relative_path == '' 

    # - The relative_path is reset if not done for_bookmark
    #   This is done in case a for_bookmark call just
    #   happened to be done for the same UserInterface in the same request
    #   before the "real" caal is done
    user_interface = ui_factory.create('/some/path', for_bookmark=False)
    assert user_interface.relative_path == '/some/path' 

    # Phase5: create the page and plug the view into it
    page = Widget.factory().create(user_interface.current_view)
    page.add_child(Slot(user_interface.current_view, 'main_slot'))

    page.plug_in(user_interface.current_view)
    assert current_view_is_plugged_in(page) 
    assert isinstance(user_interface.sub_resources, FactoryDict) 
