# Copyright 2013-2016 Reahl Software Services (Pty) Ltd. All rights reserved.
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
from nose.tools import istest
from reahl.tofu import Fixture, test, vassert, expected, scenario
from reahl.component.exceptions import ProgrammerError

from reahl.webdev.tools import Browser, XPath
from reahl.web_dev.fixtures import WebBasicsMixin
from reahl.web_dev.fixtures import WebFixture


from reahl.component.modelinterface import Field, exposed, IntegerField
from reahl.web.fw import Bookmark
from reahl.web.fw import Widget
from reahl.web.ui import A, P, Form, TextInput, Div



class QueryStringFixture(Fixture, WebBasicsMixin):
    def is_state_labelled_now(self, label, state):
        return self.driver_browser.is_element_present(XPath.paragraph_containing('%s is now %s' % (label, state)))

    def is_state_now(self, state):
        return self.is_state_labelled_now('My state', state)

    def change_fragment(self, fragment):
        self.driver_browser.execute_script('return (window.location.hash="%s")' % fragment)

    def new_FancyWidget(self):
        fixture = self
        class MyFancyWidget(Div):
            def __init__(self, view):
                super(MyFancyWidget, self).__init__(view, css_id='sedrick')
                self.enable_refresh()
                self.add_child(P(self.view, text='My state is now %s' % self.fancy_state))
                fixture.widget = self

            @exposed
            def query_fields(self, fields):
                fields.fancy_state = IntegerField(required=False, default=1)
            

        return MyFancyWidget

    def new_wsgi_app(self, widget_factory=None):
        widget_factory = widget_factory or self.FancyWidget.factory()
        return super(QueryStringFixture, self).new_wsgi_app(enable_js=True, 
                                                          child_factory=widget_factory)



@istest
class WidgetQueryArgTests(object):
    @test(QueryStringFixture)
    def query_string_widget_arguments(self, fixture):
        """Widgets can have arguments that are read from a query string"""

        class WidgetWithQueryArguments(Widget):
            def __init__(self, view):
                super(WidgetWithQueryArguments, self).__init__(view)
                self.add_child(P(view, text=self.arg_directly_on_widget))

            @exposed
            def query_fields(self, fields):
                fields.arg_directly_on_widget = Field()

        wsgi_app = fixture.new_wsgi_app(widget_factory=WidgetWithQueryArguments.factory())
        browser = Browser(wsgi_app)

        browser.open('/?arg_directly_on_widget=supercalafragalisticxpelidocious')
        vassert( browser.lxml_html.xpath('//p')[0].text == 'supercalafragalisticxpelidocious' )


    @test(QueryStringFixture)
    def query_string_prepopulates_form(self, fixture):
        """Widget query string arguments can be used on forms to pre-populate inputs based on the query string."""

        class ModelObject(object):
            @exposed
            def fields(self, fields):
                fields.arg_on_other_object = Field()

        class FormWithQueryArguments(Form):
            def __init__(self, view):
                self.model_object = ModelObject()
                super(FormWithQueryArguments, self).__init__(view, 'name')
                self.add_child(TextInput(self, self.model_object.fields.arg_on_other_object))

            @exposed
            def query_fields(self, fields):
                fields.arg_on_other_object = self.model_object.fields.arg_on_other_object
        

        wsgi_app = fixture.new_wsgi_app(widget_factory=FormWithQueryArguments.factory())
        browser = Browser(wsgi_app)

        browser.open('/?arg_on_other_object=metoo')
        vassert( browser.lxml_html.xpath('//input')[0].value == 'metoo' )


    @test(QueryStringFixture)
    def widgets_with_bookmarkable_state(self, fixture):
        """If a widget has query_fields, call `.enable_refresh()` on it to let it change 
           its contents without reloading the whole page,
           depending on a variable in the fragment of the current URL. This makes
           such Widgets bookmarkable by a browser."""

        fixture.reahl_server.set_app(fixture.wsgi_app)
        fixture.driver_browser.open('/')

        # Case: the default
        vassert( fixture.driver_browser.wait_for(fixture.is_state_now, 1) )
        vassert( fixture.widget.fancy_state == 1 )

        # Case: change without page load
        fixture.change_fragment('#fancy_state=2')
        vassert( fixture.driver_browser.wait_for(fixture.is_state_now, 2) )
        vassert( fixture.widget.fancy_state == 2 )

        # Case: unrelated fragment changes do not trigger a reload of the widget
        previous_widget = fixture.widget
        fixture.change_fragment('#fancy_state=2&other_var=other_value')
        vassert( fixture.driver_browser.wait_for(fixture.is_state_now, 2) )
        vassert( fixture.widget is previous_widget )

    @test(WebFixture)
    def css_id_is_mandatory(self, fixture):
        """If a Widget is enabled to to be refreshed, it must also have a css_id set."""
        class MyFancyWidget(Div):
            def __init__(self, view):
                super(MyFancyWidget, self).__init__(view)
                self.enable_refresh()

        with expected(ProgrammerError):
            MyFancyWidget(fixture.view)

    class PartialRefreshFixture(QueryStringFixture):
        def new_FancyWidget(self):
            fixture = self
            class MyFancyWidget(Div):
                def __init__(self, view):
                    super(MyFancyWidget, self).__init__(view, css_id='sedrick')
                    self.enable_refresh(self.query_fields.refreshing_state)
                    self.add_child(P(self.view, text='My refreshing state is now %s' % self.refreshing_state))
                    self.add_child(P(self.view, text='My non-refreshing state is now %s' % self.non_refreshing_state))
                    fixture.widget = self

                @exposed
                def query_fields(self, fields):
                    fields.refreshing_state = IntegerField(required=False, default=1)
                    fields.non_refreshing_state = IntegerField(required=False, default=2)

            return MyFancyWidget


    @test(PartialRefreshFixture)
    def refreshing_only_for_specific_args(self, fixture):
        """Calling `.enable_refresh()` only with specific query_fields has the effect that
           the Widget is only refreshed automatically for the particular fields passed, not
           for any of its query_fields.
        """

        fixture.reahl_server.set_app(fixture.wsgi_app)
        fixture.driver_browser.open('/')

        # Case: the default
        vassert( fixture.driver_browser.wait_for(fixture.is_state_labelled_now, 'My refreshing state', 1) )
        vassert( fixture.driver_browser.wait_for(fixture.is_state_labelled_now, 'My non-refreshing state', 2) )

        # Case: changing the specified field only
        fixture.change_fragment('#refreshing_state=3')
        vassert( fixture.driver_browser.wait_for(fixture.is_state_labelled_now, 'My refreshing state', 3) )
        vassert( fixture.driver_browser.wait_for(fixture.is_state_labelled_now, 'My non-refreshing state', 2) )

        # Case: changing the other field only
        fixture.change_fragment('#non_refreshing_state=4')
        vassert( fixture.driver_browser.wait_for(fixture.is_state_labelled_now, 'My refreshing state', 3) )
        vassert( fixture.driver_browser.wait_for(fixture.is_state_labelled_now, 'My non-refreshing state', 2) )

    @test(QueryStringFixture)
    def bookmarks_support_such_fragments(self, fixture):
        """Page-internal bookmarks support such bookmarkable widgets.

           These Bookmarks usually do not affect an URL - they just set widget states in different ways,
           depending on whether the client has javascript support or not.
           However, if a page was opened using the widget arguments on the querystring, a bookmark that would
           normally only have changed that argument on the hash will point to a new
           url on which the argument has been removed from the querystring and changed on the hash.
        """

        internal_bookmark = Bookmark.for_widget('an ajax bookmark', query_arguments={'fancy_state':2})
        normal_bookmark = Bookmark('/', '', 'a normal bookmark')

        # You can query whether a bookmark is page_internal or not
        vassert( internal_bookmark.is_page_internal )
        vassert( not normal_bookmark.is_page_internal )

        # page-internal bookmarks must be added to normal ones to be useful
        usable_bookmark = normal_bookmark+internal_bookmark
        
        wsgi_app = fixture.new_wsgi_app(widget_factory=A.factory_from_bookmark(usable_bookmark))

        # Case: when rendered without javascript
        browser = Browser(wsgi_app)
        browser.open('/')

        a = browser.lxml_html.xpath('//a')[0]
        vassert( a.attrib['href'] == '/?fancy_state=2' )
        vassert( a.text == 'an ajax bookmark' )

        # Case: when rendered in a browser with javascript support
        fixture.reahl_server.set_app(wsgi_app)
        fixture.driver_browser.open('/')
        vassert(     fixture.driver_browser.is_element_present("//a[@href='/#fancy_state=2']") )
        vassert( not fixture.driver_browser.is_element_present("//a[@href='/?fancy_state=2']") )

        # Case: when the argument was given on the query string of the current page
        fixture.driver_browser.open('/?fancy_state=4')
        vassert(     fixture.driver_browser.is_element_present("//a[@href='/#fancy_state=2']") )


    class RightsScenarios(QueryStringFixture):
        def allowed(self):
            return True
        def not_allowed(self):
            return False

        @scenario
        def all_allowed(self):
            self.internal_readable = self.allowed
            self.normal_readable = self.allowed
            self.expected_readable = True
            self.internal_writable = self.allowed
            self.normal_writable = self.allowed
            self.expected_writable = True

        @scenario
        def internal_disallowed(self):
            self.internal_readable = self.not_allowed
            self.normal_readable = self.allowed
            self.expected_readable = False
            self.internal_writable = self.not_allowed
            self.normal_writable = self.allowed
            self.expected_writable = False

        @scenario
        def normal_disallowed(self):
            self.internal_readable = self.allowed
            self.normal_readable = self.not_allowed
            self.expected_readable = False
            self.internal_writable = self.allowed
            self.normal_writable = self.not_allowed
            self.expected_writable = False

    @test(RightsScenarios)
    def bookmark_rights_when_adding(self, fixture):
        """When adding two Bookmarks, access rights of both are taken into account.

        """

        internal_bookmark = Bookmark.for_widget('an ajax bookmark', 
                                                query_arguments={'fancy_state':2},
                                                read_check=fixture.internal_readable,
                                                write_check=fixture.internal_writable)
        normal_bookmark = Bookmark('/', '', 'a normal bookmark',
                                   read_check=fixture.normal_readable,
                                   write_check=fixture.normal_writable)

        usable_bookmark = normal_bookmark+internal_bookmark
        vassert( usable_bookmark.read_check() is fixture.expected_readable )
        vassert( usable_bookmark.write_check() is fixture.expected_writable )
