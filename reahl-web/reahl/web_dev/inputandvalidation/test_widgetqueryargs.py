# Copyright 2013-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from reahl.tofu import Fixture, expected, scenario, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.component.exceptions import ProgrammerError

from reahl.browsertools.browsertools import Browser, XPath

from reahl.component.modelinterface import ExposedNames, IntegerField, MultiChoiceField, Choice, Action, Event
from reahl.web.fw import Bookmark, Widget
from reahl.web.ui import A, P, Form, TextInput, Div, NestedForm, ButtonInput, FormLayout

from reahl.web_dev.fixtures import WebFixture
from reahl.dev.fixtures import ReahlSystemFixture


@uses(reahl_system_fixture=ReahlSystemFixture)
class ValueScenarios(Fixture):
    @scenario
    def single_value(self):
        self.field = IntegerField(required=False, default=1, label='field')
        self.field_on_query_string = '{field_name}=123'
        self.field_value_marshalled = 123
        self.field_value_as_string = '123'

    @scenario
    def multi_value(self):
        self.field = MultiChoiceField([Choice(1, IntegerField(label='One')),
                                       Choice(2, IntegerField(label='Two')),
                                       Choice(3, IntegerField(label='Three'))],
                                       default=[],
                                       label='field')
        self.field_on_query_string = '{field_name}[]=1&{field_name}[]=3'
        self.field_value_marshalled = [1, 3]
        self.field_value_as_string = '1,3'

    @scenario
    def multi_value_not_submitted(self):
        self.field = MultiChoiceField([Choice(1, IntegerField(label='One')),
                                       Choice(2, IntegerField(label='Two')),
                                       Choice(3, IntegerField(label='Three'))],
                                       default=[2], label='field')
        self.field_on_query_string = ''
        self.field_value_marshalled = [2]
        self.field_value_as_string = '2'

    @scenario
    def multi_value_empty_the_list(self):
        self.field = MultiChoiceField([Choice(1, IntegerField(label='One')),
                                       Choice(2, IntegerField(label='Two')),
                                       Choice(3, IntegerField(label='Three'))],
                                       default=[2], label='field')
        self.field_on_query_string = '{field_name}[]-'
        self.field_value_marshalled = []
        self.field_value_as_string = ''


@with_fixtures(WebFixture, ValueScenarios)
def test_query_string_widget_arguments(web_fixture, value_scenarios):
    """Widgets can have arguments that are read from a query string"""

    fixture = value_scenarios

    class WidgetWithQueryArguments(Widget):
        def __init__(self, view):
            super().__init__(view)
            self.add_child(P(view, text=str(self.arg_directly_on_widget)))

        query_fields = ExposedNames()
        query_fields.arg_directly_on_widget = lambda i: fixture.field.unbound_copy() # We use a copy, because the Field on the fixture is only constructed once, but we get here more than once during a GET

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=WidgetWithQueryArguments.factory())
    browser = Browser(wsgi_app)

    browser.open('/?%s' % fixture.field_on_query_string.format(field_name='arg_directly_on_widget'))
    assert browser.lxml_html.xpath('//p')[0].text == str(fixture.field_value_marshalled)


@with_fixtures(WebFixture, ValueScenarios)
def test_query_string_prepopulates_form(web_fixture, value_scenarios):
    """Widget query string arguments can be used on forms to pre-populate inputs based on the query string."""

    fixture = value_scenarios

    class ModelObject:
        fields = ExposedNames()
        fields.arg_on_other_object = lambda i: fixture.field

    class FormWithQueryArguments(Form):
        def __init__(self, view):
            self.model_object = ModelObject()
            super().__init__(view, 'name')
            self.use_layout(FormLayout())
            self.layout.add_input(TextInput(self, self.model_object.fields.arg_on_other_object))

        query_fields = ExposedNames()
        query_fields.arg_on_other_object = lambda i: i.model_object.fields.arg_on_other_object

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=FormWithQueryArguments.factory())
    browser = Browser(wsgi_app)

    browser.open('/?%s' % fixture.field_on_query_string.format(field_name='name-arg_on_other_object'))
    assert browser.get_value(XPath.input_labelled('field')) == fixture.field_value_as_string


@uses(web_fixture=WebFixture)
class QueryStringFixture(Fixture):
    def is_state_now(self, state):
        return self.is_state_labelled_now('My state', state)
    def is_state_on_another_widget_now(self, state):
        return self.is_state_labelled_now('Another widget state', state)

    def is_state_labelled_now(self, label, state):
        return self.web_fixture.driver_browser.is_element_present(XPath.paragraph().including_text('%s is now %s' % (label, state)))


@with_fixtures(WebFixture, QueryStringFixture, ValueScenarios)
def test_widgets_with_bookmarkable_state(web_fixture, query_string_fixture, value_scenarios):
    """If a widget has query_fields, call `.enable_refresh()` on it to let it change
       its contents without reloading the whole page,
       depending on a variable in the fragment of the current URL. This makes
       such Widgets bookmarkable by a browser."""

    fixture = query_string_fixture

    class MyFancyWidget(Div):
        def __init__(self, view):
            super().__init__(view, css_id='sedrick')
            self.enable_refresh()
            self.add_child(P(self.view, text='My state is now %s' % self.fancy_state))
            fixture.widget = self

        query_fields = ExposedNames()
        query_fields.fancy_state = lambda i: value_scenarios.field.unbound_copy()

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=MyFancyWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    web_fixture.driver_browser.open('/')

    # Case: the default
    assert web_fixture.driver_browser.wait_for(fixture.is_state_now, str(value_scenarios.field.default))
    assert fixture.widget.fancy_state == value_scenarios.field.default

    # Case: change without page load
    web_fixture.driver_browser.set_fragment('#%s' % value_scenarios.field_on_query_string.format(field_name='fancy_state'))
    assert web_fixture.driver_browser.wait_for(fixture.is_state_now, value_scenarios.field_value_marshalled)
    assert fixture.widget.fancy_state == value_scenarios.field_value_marshalled

    # Case: unrelated fragment changes do not trigger a reload of the widget
    previous_widget = fixture.widget
    web_fixture.driver_browser.set_fragment('#%s&other_var=other_value' % value_scenarios.field_on_query_string.format(field_name='fancy_state'))
    assert web_fixture.driver_browser.wait_for(fixture.is_state_now, value_scenarios.field_value_marshalled)
    assert fixture.widget is previous_widget


@with_fixtures(WebFixture)
def test_css_id_is_mandatory(web_fixture):
    """If a Widget is enabled to to be refreshed, it must also have a css_id set."""

    class MyFancyWidget(Div):
        def __init__(self, view):
            super().__init__(view)
            self.enable_refresh()

    with expected(ProgrammerError):
        MyFancyWidget(web_fixture.view)


@with_fixtures(WebFixture, QueryStringFixture)
def test_refreshing_only_for_specific_args(web_fixture, query_string_fixture):
    """Calling `.enable_refresh()` only with specific query_fields has the effect that
       the Widget is only refreshed automatically for the particular fields passed, not
       for any of its query_fields.
    """

    fixture = query_string_fixture

    class MyFancyWidget(Div):
        def __init__(self, view):
            super().__init__(view, css_id='sedrick')
            self.enable_refresh(self.query_fields.refreshing_state)
            self.add_child(P(self.view, text='My refreshing state is now %s' % self.refreshing_state))
            self.add_child(P(self.view, text='My non-refreshing state is now %s' % self.non_refreshing_state))
            fixture.widget = self

        query_fields = ExposedNames()
        query_fields.refreshing_state = lambda i: IntegerField(required=False, default=1)
        query_fields.non_refreshing_state = lambda i: IntegerField(required=False, default=2)

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=MyFancyWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    web_fixture.driver_browser.open('/')

    # Case: the default
    assert web_fixture.driver_browser.wait_for(fixture.is_state_labelled_now, 'My refreshing state', 1)
    assert web_fixture.driver_browser.wait_for(fixture.is_state_labelled_now, 'My non-refreshing state', 2)

    # Case: changing the specified field only
    web_fixture.driver_browser.set_fragment('#refreshing_state=3')
    assert web_fixture.driver_browser.wait_for(fixture.is_state_labelled_now, 'My refreshing state', 3)
    assert web_fixture.driver_browser.wait_for(fixture.is_state_labelled_now, 'My non-refreshing state', 2)

    # Case: changing the other field only
    web_fixture.driver_browser.set_fragment('#non_refreshing_state=4')
    assert web_fixture.driver_browser.wait_for(fixture.is_state_labelled_now, 'My refreshing state', 3)
    assert web_fixture.driver_browser.wait_for(fixture.is_state_labelled_now, 'My non-refreshing state', 2)


@with_fixtures(WebFixture, QueryStringFixture)
def test_coactive_widgets_are_refreshed_when_their_widgets_are(web_fixture, query_string_fixture):
    """The coactive Widgets of a Widget are refreshed whenever the Widget itself is refreshed, even though
       they are not children of the refreshed Widget."""

    fixture = query_string_fixture
    fixture.submitted = False

    class RefreshingDiv(Div):
        def __init__(self, view, coactive_div):
            super().__init__(view, css_id='sedrick')
            self.coactive_div = coactive_div
            self.enable_refresh()
            self.add_child(P(self.view, text='My state is now %s' % self.fancy_state))

        @property
        def coactive_widgets(self):
            return super().coactive_widgets + [self.coactive_div]

        query_fields = ExposedNames()
        query_fields.fancy_state = lambda i: IntegerField(required=False, default=1)


    class MyFancyWidget(Widget):
        def __init__(self, view):
            super().__init__(view)
            
            static_div = self.add_child(Div(view))
            coactive_div = static_div.add_child(Div(view, css_id='coactive_div'))

            refreshing_div = self.add_child(RefreshingDiv(view, coactive_div))

            text_to_show = 'original'
            if refreshing_div.fancy_state == 2:
                text_to_show = 'coactive refreshed'
            coactive_div.add_child(P(view, text=text_to_show))

            fixture.widget = self


    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=MyFancyWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    web_fixture.driver_browser.open('/')

    def coactive_widget_text_is(expected_text):
        return web_fixture.driver_browser.is_element_present(XPath.paragraph().including_text(expected_text))

    assert web_fixture.driver_browser.wait_for(fixture.is_state_now, '1')
    assert coactive_widget_text_is('original')

    web_fixture.driver_browser.set_fragment('#fancy_state=%s' % '2')
    assert web_fixture.driver_browser.wait_for(fixture.is_state_now, '2')
    assert coactive_widget_text_is('coactive refreshed')


@with_fixtures(WebFixture, QueryStringFixture)
def test_refresh_nested_forms(web_fixture, query_string_fixture):
    """NestedForms work correctly when they appear as children of a refreshed widget."""

    fixture = query_string_fixture
    fixture.submitted = False

    class MyFancyWidget(Div):
        def __init__(self, view):
            super().__init__(view, css_id='sedrick')
            self.enable_refresh()
            self.add_child(P(self.view, text='My state is now %s' % self.fancy_state))
            if self.fancy_state == 2:
                form = self.add_child(NestedForm(view, 'nestedform'))
                form.define_event_handler(self.events.submit)
                form.add_child(ButtonInput(form.form, self.events.submit))
            fixture.widget = self

        def submit(self):
            fixture.submitted = True

        query_fields = ExposedNames()
        query_fields.fancy_state = lambda i: IntegerField(required=False, default=1)

        events = ExposedNames()
        events.submit = lambda i: Event(action=Action(i.submit))

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=MyFancyWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    web_fixture.driver_browser.open('/')

    assert web_fixture.driver_browser.wait_for(fixture.is_state_now, '1')

    web_fixture.driver_browser.set_fragment('#fancy_state=%s' % '2')
    assert web_fixture.driver_browser.wait_for(fixture.is_state_now, '2')

    assert not fixture.submitted
    web_fixture.driver_browser.click(XPath.button_labelled('submit'))
    assert fixture.submitted



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
