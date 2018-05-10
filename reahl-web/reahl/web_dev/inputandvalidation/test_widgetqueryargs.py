# Copyright 2013-2018 Reahl Software Services (Pty) Ltd. All rights reserved.
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

from reahl.tofu import Fixture, expected, scenario, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.component.exceptions import ProgrammerError

from reahl.webdev.tools import Browser, XPath

from reahl.component.modelinterface import Field, exposed, IntegerField
from reahl.web.fw import Bookmark, Widget
from reahl.web.ui import A, P, Form, TextInput, Div

from reahl.web_dev.fixtures import WebFixture


@uses(web_fixture=WebFixture)
class QueryStringFixture(Fixture):

    def is_state_labelled_now(self, label, state):
        return self.web_fixture.driver_browser.is_element_present(XPath.paragraph_containing('%s is now %s' % (label, state)))

    def is_state_now(self, state):
        return self.is_state_labelled_now('My state', state)

    def change_fragment(self, fragment):
        self.web_fixture.driver_browser.execute_script('return (window.location.hash="%s")' % fragment)

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
        # xxxxx
        widget_factory = widget_factory or self.FancyWidget.factory()
        return self.web_fixture.new_wsgi_app(enable_js=True, child_factory=widget_factory)


@with_fixtures(WebFixture, QueryStringFixture)
def test_query_string_widget_arguments(web_fixture, query_string_fixture):
    """Widgets can have arguments that are read from a query string"""

    fixture = query_string_fixture

    class WidgetWithQueryArguments(Widget):
        def __init__(self, view):
            super(WidgetWithQueryArguments, self).__init__(view)
            self.add_child(P(view, text=self.arg_directly_on_widget))

        @exposed
        def query_fields(self, fields):
            fields.arg_directly_on_widget = Field()

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=WidgetWithQueryArguments.factory())
    browser = Browser(wsgi_app)

    browser.open('/?arg_directly_on_widget=supercalafragalisticxpelidocious')
    assert browser.lxml_html.xpath('//p')[0].text == 'supercalafragalisticxpelidocious'


@with_fixtures(WebFixture)
def test_query_string_prepopulates_form(web_fixture):
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

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=FormWithQueryArguments.factory())
    browser = Browser(wsgi_app)

    browser.open('/?arg_on_other_object=metoo')
    assert browser.lxml_html.xpath('//input')[0].value == 'metoo'


@with_fixtures(WebFixture, QueryStringFixture)
def test_widgets_with_bookmarkable_state(web_fixture, query_string_fixture):
    """If a widget has query_fields, call `.enable_refresh()` on it to let it change
       its contents without reloading the whole page,
       depending on a variable in the fragment of the current URL. This makes
       such Widgets bookmarkable by a browser."""

    fixture = query_string_fixture

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.FancyWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    web_fixture.driver_browser.open('/')

    # Case: the default
    assert web_fixture.driver_browser.wait_for(fixture.is_state_now, 1)
    assert fixture.widget.fancy_state == 1

    # Case: change without page load
    fixture.change_fragment('#fancy_state=2')
    assert web_fixture.driver_browser.wait_for(fixture.is_state_now, 2)
    assert fixture.widget.fancy_state == 2

    # Case: unrelated fragment changes do not trigger a reload of the widget
    previous_widget = fixture.widget
    fixture.change_fragment('#fancy_state=2&other_var=other_value')
    assert web_fixture.driver_browser.wait_for(fixture.is_state_now, 2)
    assert fixture.widget is previous_widget


@with_fixtures(WebFixture)
def test_css_id_is_mandatory(web_fixture):
    """If a Widget is enabled to to be refreshed, it must also have a css_id set."""

    class MyFancyWidget(Div):
        def __init__(self, view):
            super(MyFancyWidget, self).__init__(view)
            self.enable_refresh()

    with expected(ProgrammerError):
        MyFancyWidget(web_fixture.view)


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


@with_fixtures(WebFixture, PartialRefreshFixture)
def test_refreshing_only_for_specific_args(web_fixture, partial_refresh_fixture):
    """Calling `.enable_refresh()` only with specific query_fields has the effect that
       the Widget is only refreshed automatically for the particular fields passed, not
       for any of its query_fields.
    """

    fixture = partial_refresh_fixture

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.FancyWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    web_fixture.driver_browser.open('/')

    # Case: the default
    assert web_fixture.driver_browser.wait_for(fixture.is_state_labelled_now, 'My refreshing state', 1)
    assert web_fixture.driver_browser.wait_for(fixture.is_state_labelled_now, 'My non-refreshing state', 2)

    # Case: changing the specified field only
    fixture.change_fragment('#refreshing_state=3')
    assert web_fixture.driver_browser.wait_for(fixture.is_state_labelled_now, 'My refreshing state', 3)
    assert web_fixture.driver_browser.wait_for(fixture.is_state_labelled_now, 'My non-refreshing state', 2)

    # Case: changing the other field only
    fixture.change_fragment('#non_refreshing_state=4')
    assert web_fixture.driver_browser.wait_for(fixture.is_state_labelled_now, 'My refreshing state', 3)
    assert web_fixture.driver_browser.wait_for(fixture.is_state_labelled_now, 'My non-refreshing state', 2)


@with_fixtures(WebFixture)
def test_bookmarks_support_such_fragments(web_fixture):
    """Page-internal bookmarks support such bookmarkable widgets.

       These Bookmarks usually do not affect an URL - they just set widget states in different ways,
       depending on whether the client has javascript support or not.
       However, if a page was opened using the widget arguments on the querystring, a bookmark that would
       normally only have changed that argument on the hash will point to a new
       url on which the argument has been removed from the querystring and changed on the hash.
    """

    fixture = web_fixture

    internal_bookmark = Bookmark.for_widget('an ajax bookmark', query_arguments={'fancy_state':2})
    normal_bookmark = Bookmark('/', '', 'a normal bookmark')

    # You can query whether a bookmark is page_internal or not
    assert internal_bookmark.is_page_internal
    assert not normal_bookmark.is_page_internal

    # page-internal bookmarks must be added to normal ones to be useful
    usable_bookmark = normal_bookmark+internal_bookmark

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=A.factory_from_bookmark(usable_bookmark))

    # Case: when rendered without javascript
    browser = Browser(wsgi_app)
    browser.open('/')

    a = browser.lxml_html.xpath('//a')[0]
    assert a.attrib['href'] == '/?fancy_state=2'
    assert a.text == 'an ajax bookmark'

    # Case: when rendered in a browser with javascript support
    web_fixture.reahl_server.set_app(wsgi_app)
    web_fixture.driver_browser.open('/')
    assert     web_fixture.driver_browser.is_element_present("//a[@href='/#fancy_state=2']")
    assert not web_fixture.driver_browser.is_element_present("//a[@href='/?fancy_state=2']")

    # Case: when the argument was given on the query string of the current page
    fixture.driver_browser.open('/?fancy_state=4')
    assert     web_fixture.driver_browser.is_element_present("//a[@href='/#fancy_state=2']")


class RightsScenarios(Fixture):
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


@with_fixtures(RightsScenarios)
def test_bookmark_rights_when_adding(rights_scenarios):
    """When adding two Bookmarks, access rights of both are taken into account.

    """
    fixture = rights_scenarios

    internal_bookmark = Bookmark.for_widget('an ajax bookmark',
                                            query_arguments={'fancy_state':2},
                                            read_check=fixture.internal_readable,
                                            write_check=fixture.internal_writable)
    normal_bookmark = Bookmark('/', '', 'a normal bookmark',
                               read_check=fixture.normal_readable,
                               write_check=fixture.normal_writable)

    usable_bookmark = normal_bookmark+internal_bookmark
    assert usable_bookmark.read_check() is fixture.expected_readable
    assert usable_bookmark.write_check() is fixture.expected_writable
