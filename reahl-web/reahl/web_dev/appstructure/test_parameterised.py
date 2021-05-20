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


from reahl.tofu import scenario, Fixture, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.browsertools.browsertools import Browser, XPath

from reahl.component.modelinterface import Field
from reahl.web.fw import CannotCreate, IdentityDictionary, UrlBoundView, UserInterface
from reahl.web.ui import HTML5Page, P

from reahl.web_dev.fixtures import WebFixture, BasicPageLayout


@uses(web_fixture=WebFixture)
class ParameterisedScenarios(Fixture):
    
    class ParameterisedView(UrlBoundView):
        def assemble(self, some_arg=None):
            if some_arg == 'doesnotexist':
                raise CannotCreate()
            self.title = 'View for: %s' % some_arg
            self.set_slot('main', P.factory(text='content for %s' % some_arg))

    @scenario
    def normal_arguments(self):
        """Arguments can be sent from where the View is defined."""
        self.argument = 'some arg'
        self.expected_value = 'some arg'
        self.url = '/a_ui/aview'
        self.should_exist = True

    @scenario
    def url_arguments(self):
        """Arguments can be parsed from an URL, iff they are specified to the definition as Fields."""
        self.argument = Field()
        self.expected_value = 'test1'
        self.url = '/a_ui/aview/test1'
        self.should_exist = True

    @scenario
    def define_entire_page(self):
        """The dynamically defined View can also be define its entire page to be rendered, instead of slots"""
        self.url_arguments() # same setup as this except:
        class SimplePage(HTML5Page):
            def __init__(self, view, some_arg):
                super().__init__(view)
                self.body.add_child(P(view, text='content for %s' % some_arg))

        class ParameterisedView(UrlBoundView):
            def assemble(self, some_arg=None):
                if some_arg == 'doesnotexist':
                    raise CannotCreate()
                self.title = 'View for: %s' % some_arg
                self.set_page(SimplePage.factory(some_arg))

        self.ParameterisedView = ParameterisedView

    @scenario
    def cannot_create(self):
        """To indicate that a view does not exist for the given arguments, the .assemble() 
           method of the View should raise CannotCreate()."""
        self.argument = 'doesnotexist'
        self.url = '/a_ui/aview'
        self.should_exist = False


@with_fixtures(WebFixture, ParameterisedScenarios)
def test_views_with_parameters(web_fixture, parameterised_scenarios):
    """Views can have arguments that originate from code, or are parsed from the URL."""

    class UIWithParameterisedViews(UserInterface):
        def assemble(self):
            self.define_view('/aview', view_class=fixture.ParameterisedView, some_arg=fixture.argument)

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            self.define_user_interface('/a_ui',  UIWithParameterisedViews,  {'main': 'main'}, name='myui')

    fixture = parameterised_scenarios

    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    if fixture.should_exist:
        browser.open(fixture.url)
        assert browser.title == 'View for: %s' % fixture.expected_value
        assert browser.is_element_present(XPath.paragraph().including_text('content for %s' % fixture.expected_value))
    else:
        browser.open(fixture.url, status=404)


@with_fixtures(WebFixture)
def test_views_from_regex(web_fixture):
    """Parameterised Views can also be added based on a regex over the url."""

    class ParameterisedView(UrlBoundView):
        def assemble(self, some_key=None):
            self.title = 'View for: %s' % some_key

    class UIWithParameterisedViews(UserInterface):
        def assemble(self):
            self.define_regex_view('/someurl_(?P<some_key>.*)', '/someurl_${some_key}', view_class=ParameterisedView,
                                   some_key=Field(required=True))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page)
            self.define_user_interface('/a_ui',  UIWithParameterisedViews,  {}, name='myui')

    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    # Parameterised constructing a View from an URL
    browser.open('/a_ui/someurl_test1')
    assert browser.title == 'View for: test1' 


@with_fixtures(WebFixture)
def test_user_interfaces_from_regex(web_fixture):
    """Sub UserInterfaces can be created on the fly on a UserInterface, based on the URL visited. To indicate that a
       UserInterface does not exist, the creation method should return None."""

    class RegexUserInterface(UserInterface):
        def assemble(self, ui_key=None):
            if ui_key == 'doesnotexist':
                raise CannotCreate()

            self.name = 'user_interface-%s' % ui_key
            root = self.define_view('/', title='Simple user_interface %s' % self.name)
            root.set_slot('user_interface-slot', P.factory(text='in user_interface slot'))

    class UIWithParameterisedUserInterfaces(UserInterface):
        def assemble(self):
            self.define_regex_user_interface('/apath/(?P<ui_key>[^/]*)',
                                     '/apath/${ui_key}',
                                     RegexUserInterface,
                                     {'user_interface-slot': 'main'},
                                     ui_key=Field())

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            self.define_user_interface('/a_ui',  UIWithParameterisedUserInterfaces,  IdentityDictionary(), name='myui')


    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    # A sub-user_interface is dynamically created from an URL
    browser.open('/a_ui/apath/test1/')
    assert browser.title == 'Simple user_interface user_interface-test1' 

    # The slots of the sub-user_interface is correctly plugged into the page
    [p] = browser.lxml_html.xpath('//p')
    assert p.text == 'in user_interface slot' 

    # Another sub-user_interface is dynamically created from an URL
    browser.open('/a_ui/apath/another/')
    assert browser.title == 'Simple user_interface user_interface-another' 

    # When the URL cannot be mapped
    browser.open('/a_ui/apath/doesnotexist/', status=404)



@uses(web_fixture=WebFixture)
class ParameterisedUserInterfaceScenarios(Fixture):

    @scenario
    def normal_arguments(self):
        """Arguments can be sent from where the UserInterface is defined."""
        self.argument = 'some arg'
        self.expected_value = 'some arg'
        self.url = '/a_ui/parameterisedui/aview'
        self.should_exist = True

    @scenario
    def url_arguments(self):
        """Arguments can be parsed from an URL, iff they are specified to the definition as Fields."""
        self.argument = Field()
        self.expected_value = 'test1'
        self.url = '/a_ui/parameterisedui/test1/aview'
        self.should_exist = True

    @scenario
    def cannot_create(self):
        """To indicate that a UserInterface does not exist for the given arguments, the .assemble() 
           method of the UserInterface should raise CannotCreate()."""
        self.argument = 'doesnotexist'
        self.url = '/a_ui/parameterisedui/aview'
        self.should_exist = False


@with_fixtures(WebFixture, ParameterisedUserInterfaceScenarios)
def test_parameterised_uis(web_fixture, parameterised_user_interface_scenarios):
    """Sub UserInterfaces can also be parameterised by defining arguments in .define_user_interface, and receiving them in .assemble()."""

    class ParameterisedUserInterface(UserInterface):
        def assemble(self, ui_arg=None):
            if ui_arg == 'doesnotexist':
                raise CannotCreate()

            self.name = 'user_interface-%s' % ui_arg
            root = self.define_view('/aview', title='Simple user_interface %s' % self.name)
            root.set_slot('user_interface-slot', P.factory(text='in user_interface slot'))


    class UIWithParameterisedUserInterfaces(UserInterface):
        def assemble(self):
            self.define_user_interface('/parameterisedui', ParameterisedUserInterface, {'user_interface-slot': 'main'}, 
                               ui_arg=fixture.argument,
                               name='paramui')

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            self.define_user_interface('/a_ui',  UIWithParameterisedUserInterfaces,  IdentityDictionary(), name='myui')

    fixture = parameterised_user_interface_scenarios

    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    if fixture.should_exist:
        browser.open(fixture.url)

        # The correct argument was passed
        assert browser.title == 'Simple user_interface user_interface-%s' % fixture.expected_value 

        # The slots of the sub-user_interface is correctly plugged into the page
        [p] = browser.lxml_html.xpath('//p')
        assert p.text == 'in user_interface slot' 
    else:
        # When the URL cannot be mapped
        browser.open(fixture.url, status=404)

