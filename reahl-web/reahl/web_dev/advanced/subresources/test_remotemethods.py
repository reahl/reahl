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


import json
from webob import Response

from sqlalchemy import Column, UnicodeText, Integer

from reahl.stubble import stubclass, CallMonitor, replaced
from reahl.tofu import scenario, expected, Fixture, uses, NoException
from reahl.tofu.pytestsupport import with_fixtures

from reahl.browsertools.browsertools import Browser, XPath
from reahl.component.exceptions import DomainException, ProgrammerError
from reahl.web.fw import CheckedRemoteMethod, JsonResult, MethodResult, RemoteMethod, Widget, WidgetResult
from reahl.web.ui import Div
from reahl.component.modelinterface import Field, IntegerField

from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture
from reahl.sqlalchemysupport import Base, Session
from reahl.dev.fixtures import ReahlSystemFixture
from reahl.web_dev.fixtures import WebFixture


@uses(web_fixture=WebFixture)
class RemoteMethodFixture(Fixture):

    def new_widget_factory(self, remote_method=None):
        remote_method = remote_method or self.remote_method

        @stubclass(Widget)
        class WidgetWithRemoteMethod(Widget):
            def __init__(self, view):
                super().__init__(view)
                view.add_resource(remote_method)

        return WidgetWithRemoteMethod.factory()

    def new_wsgi_app(self, remote_method=None, enable_js=False):
        remote_method = remote_method or self.remote_method
        return self.web_fixture.new_wsgi_app(child_factory=self.new_widget_factory(remote_method=remote_method), enable_js=enable_js)


@with_fixtures(WebFixture, RemoteMethodFixture)
def test_remote_methods(web_fixture, remote_method_fixture):
    """A RemoteMethod is a SubResource representing a method on the server side which can be invoked via POSTing to an URL."""

    fixture = remote_method_fixture

    def callable_object():
        return 'value returned from method'

    encoding = 'koi8_r'  # Deliberate
    remote_method = RemoteMethod(web_fixture.view, 'amethod', callable_object, MethodResult(mime_type='ttext/hhtml', encoding=encoding), disable_csrf_check=True)

    wsgi_app = fixture.new_wsgi_app(remote_method=remote_method)
    browser = Browser(wsgi_app)

    # By default you cannot GET, since the method is not immutable
    browser.open('/_amethod_method', status=405)

    # POSTing to the URL, returns the result of the method
    browser.post('/_amethod_method', {})
    assert browser.raw_html == 'value returned from method'
    assert browser.last_response.charset == encoding
    assert browser.last_response.content_type == 'ttext/hhtml'


@with_fixtures(WebFixture, RemoteMethodFixture)
def test_remote_methods_via_ajax(web_fixture, remote_method_fixture):
    """A RemoteMethod can be called via AJAX with CSRF protection built-in."""

    fixture = remote_method_fixture

    def callable_object():
        return 'value returned from method'

    remote_method = RemoteMethod(web_fixture.view, 'amethod', callable_object, MethodResult(), disable_csrf_check=False)

    wsgi_app = fixture.new_wsgi_app(remote_method=remote_method, enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser

    # Case: using jquery to POST to the method includes the necessary xsrf info automatically
    browser.open('/')
    browser.execute_script('$.post("/_amethod_method", success=function(data){ $("body").attr("data-result", data) })')
    browser.wait_for_element_present(XPath('body/@data-result'))
    results = browser.execute_script('return $("body").attr("data-result")')
    assert results == 'value returned from method'

    # Case: POSTing without a csrf token breaks
    browser = Browser(wsgi_app)
    browser.post('/_amethod_method', {}, status=403)


@with_fixtures(WebFixture, RemoteMethodFixture)
def test_exception_handling(web_fixture, remote_method_fixture):
    """The RemoteMethod sends back the str() of an exception raised for the specified exception class."""


    def fail():
        raise Exception('I failed')
    remote_method = RemoteMethod(web_fixture.view, 'amethod', fail, MethodResult(catch_exception=Exception), disable_csrf_check=True)

    wsgi_app = remote_method_fixture.new_wsgi_app(remote_method=remote_method)
    browser = Browser(wsgi_app)

    browser.post('/_amethod_method', {})
    assert browser.raw_html == 'I failed'


@with_fixtures(WebFixture, RemoteMethodFixture)
def test_idempotent_remote_methods(web_fixture, remote_method_fixture):
    """A RemoteMethod that is idempotent is accessible via GET (instead of POST)."""

    def callable_object():
        return 'value returned from method'
    remote_method = RemoteMethod(web_fixture.view, 'amethod', callable_object, MethodResult(), idempotent=True, disable_csrf_check=True)

    wsgi_app = remote_method_fixture.new_wsgi_app(remote_method=remote_method)
    browser = Browser(wsgi_app)

    # GET, since the method is idempotent
    browser.open('/_amethod_method')
    assert browser.raw_html == 'value returned from method'

    # POSTing to the URL, is not supported
    browser.post('/_amethod_method', {}, status=405)


@with_fixtures(WebFixture, RemoteMethodFixture, SqlAlchemyFixture)
def test_immutable_remote_methods(web_fixture, remote_method_fixture, sql_alchemy_fixture):
    """The database is always rolled back at the end of an immutable RemoteMethod."""

    class TestObject(Base):
        __tablename__ = 'test_remotemethods_test_object'
        id = Column(Integer, primary_key=True)
        name = Column(UnicodeText)

    with sql_alchemy_fixture.persistent_test_classes(TestObject):
        def callable_object():
            Session.add(TestObject(name='new object'))
            assert Session.query(TestObject).count() == 1
            return 'value returned from method'
        
        remote_method = RemoteMethod(web_fixture.view, 'amethod', callable_object, MethodResult(), immutable=True, disable_csrf_check=True)

        assert remote_method.idempotent  # Immutable methods are idempotent

        wsgi_app = remote_method_fixture.new_wsgi_app(remote_method=remote_method)
        browser = Browser(wsgi_app)

        browser.open('/_amethod_method')
        assert browser.raw_html == 'value returned from method'

        # The database is rolled back to ensure immutability
        assert Session.query(TestObject).count() == 0


class ArgumentScenarios(Fixture):
    @scenario
    def get(self):
        self.idempotent = True
    @scenario
    def post(self):
        self.idempotent = False


@with_fixtures(WebFixture, RemoteMethodFixture, ArgumentScenarios)
def test_arguments_to_remote_methods(web_fixture, remote_method_fixture, argument_scenarios):
    """A RemoteMethod can get arguments from a query string or submitted form values, depending on the scenario."""

    fixture = argument_scenarios

    def callable_object(**kwargs):
        fixture.method_kwargs = kwargs
        return ''

    remote_method = RemoteMethod(web_fixture.view, 'amethod', callable_object, MethodResult(), idempotent=fixture.idempotent, disable_csrf_check=True)

    wsgi_app = remote_method_fixture.new_wsgi_app(remote_method=remote_method)
    browser = Browser(wsgi_app)

    kwargs_sent = {'a':'AAA', 'b':'BBB'}
    if fixture.idempotent:
        browser.open('/_amethod_method?a=AAA&b=BBB')
    else:
        browser.post('/_amethod_method', kwargs_sent)
    assert fixture.method_kwargs == kwargs_sent


@with_fixtures(WebFixture, RemoteMethodFixture, ArgumentScenarios)
def test_checked_arguments(web_fixture, remote_method_fixture, argument_scenarios):
    """A CheckedRemoteMethod checks and marshalls its parameters using Fields."""

    fixture = argument_scenarios

    def callable_object(anint=None, astring=None):
        fixture.method_kwargs = {'anint': anint, 'astring': astring}
        return ''

    remote_method = CheckedRemoteMethod(web_fixture.view, 'amethod', callable_object, MethodResult(),
                                        idempotent=fixture.idempotent,
                                        anint=IntegerField(),
                                        astring=Field(),
                                        disable_csrf_check=True)

    wsgi_app = remote_method_fixture.new_wsgi_app(remote_method=remote_method)
    browser = Browser(wsgi_app)

    if fixture.idempotent:
        browser.open('/_amethod_method?anint=5&astring=SupercalifraGilisticexpialidocious')
    else:
        browser.post('/_amethod_method', {'anint':'5', 'astring':'SupercalifraGilisticexpialidocious'})
    assert fixture.method_kwargs == {'anint':5, 'astring':'SupercalifraGilisticexpialidocious'}


@uses(web_fixture=WebFixture)
class ResultScenarios(Fixture):
    @scenario
    def json(self):
        self.method_result = JsonResult(IntegerField(), catch_exception=Exception)
        self.value_to_return = 1
        self.expected_response = '1'
        self.exception_response = '"exception text"'
        self.expected_charset = self.method_result.encoding
        self.expected_content_type = 'application/json'
        self.results_match = lambda x, y: x == y

    @stubclass(Widget)
    class WidgetStub(Widget):
        css_id = 'someid'
        def render_contents(self): return '<the widget contents>'
        def get_contents_js(self, context=None): return ['some', 'some', 'javascript']

    @scenario
    def widget(self):
        self.method_result = WidgetResult([self.WidgetStub(self.web_fixture.view)], as_json_and_result=False)
        self.value_to_return = 'ignored in this case'
        self.expected_response = '<the widget contents><script type="text/javascript">javascriptsome</script>'
        self.exception_response = Exception
        self.expected_charset = self.method_result.encoding
        self.expected_content_type = 'text/html'
        self.results_match = lambda x, y: x == y

    @scenario
    def widget_as_json(self):
        self.method_result = WidgetResult([self.WidgetStub(self.web_fixture.view)])
        [self.web_fixture.view.page] = self.method_result.result_widgets

        self.value_to_return = 'ignored in this case'
        self.expected_response = {'result': {"someid": '<the widget contents><script type="text/javascript">javascriptsome</script>'},
                                  'success': True, 'exception': ''}
        self.expected_charset = self.method_result.encoding
        self.expected_content_type = 'application/json'
        def results_match(expected, actual):
            return json.loads(actual) == expected
        self.results_match = results_match


@with_fixtures(WebFixture, RemoteMethodFixture, ResultScenarios)
def test_different_kinds_of_result(web_fixture, remote_method_fixture, result_scenarios):
    """Different kinds of MethodResult can be specified for a method."""

    fixture = result_scenarios

    def callable_object():
        return fixture.value_to_return
    remote_method = RemoteMethod(web_fixture.view, 'amethod', callable_object, default_result=fixture.method_result, disable_csrf_check=True)

    wsgi_app = remote_method_fixture.new_wsgi_app(remote_method=remote_method)
    browser = Browser(wsgi_app)

    browser.post('/_amethod_method', {})
    assert fixture.results_match(fixture.expected_response, browser.raw_html)
    assert browser.last_response.charset == fixture.expected_charset
    assert browser.last_response.content_type == fixture.expected_content_type


@with_fixtures(WebFixture, RemoteMethodFixture, ResultScenarios.json)
def test_exception_handling_for_json(web_fixture, remote_method_fixture, json_result_scenario):
    """How exceptions are handled with JsonResult."""

    fixture = json_result_scenario

    def fail():
        raise Exception('exception text')
    remote_method = RemoteMethod(web_fixture.view, 'amethod', fail, default_result=fixture.method_result, disable_csrf_check=True)

    wsgi_app = remote_method_fixture.new_wsgi_app(remote_method=remote_method)
    browser = Browser(wsgi_app)

    browser.post('/_amethod_method', {})
    assert browser.raw_html == fixture.exception_response
    assert browser.last_response.charset == fixture.expected_charset
    assert browser.last_response.content_type == fixture.expected_content_type


@with_fixtures(WebFixture, RemoteMethodFixture, ResultScenarios.widget)
def test_exception_handling_for_widgets(web_fixture, remote_method_fixture, widget_result_scenario):
    """How exceptions are handled with WidgetResult."""

    fixture = widget_result_scenario

    def fail():
        raise Exception('exception text')
    remote_method = RemoteMethod(web_fixture.view, 'amethod', fail, default_result=fixture.method_result, disable_csrf_check=True)

    wsgi_app = remote_method_fixture.new_wsgi_app(remote_method=remote_method)
    browser = Browser(wsgi_app)

    with expected(Exception):
        browser.post('/_amethod_method', {})


@uses(web_fixture=WebFixture)
class RegenerateMethodResultScenarios(Fixture):
    method_called = 0
    def new_method_result(self):
        fixture = self
        @stubclass(MethodResult)
        class ResultThatDependsOnExecutionOfMethod(MethodResult):
            def create_response(self, return_value):
                return Response(body='success: method was called %s times' % fixture.method_called)

            def create_exception_response(self, exception):
                return Response(body='exception: method was called %s times' % fixture.method_called)
        return ResultThatDependsOnExecutionOfMethod(catch_exception=DomainException, replay_request=True)

    def new_remote_method(self):
        fixture = self
        def callable_to_call():
            fixture.method_called += 1
            if fixture.exception:
                raise DomainException('ex')
        return RemoteMethod(self.web_fixture.view, 'amethod', callable_to_call, self.method_result, immutable=False, disable_csrf_check=True)

    @scenario
    def success(self):
        self.exception = False
        self.expected_response = 'success: method was called 1 times'

    @scenario
    def exception(self):
        self.exception = True
        self.expected_response = 'exception: method was called 1 times'


@with_fixtures(ReahlSystemFixture, WebFixture, RemoteMethodFixture, RegenerateMethodResultScenarios)
def test_regenerating_method_results(reahl_system_fixture, web_fixture,
                                     remote_method_fixture, regenerate_method_result_scenarios):
    """If a MethodResult is set up to replay_request=True, the view it is part of (and thus itself) is recreated
       before the (new incarnation of the) MethodResult generates its actual response. Replaying the request means recreating
       all Widgets on the current View as well as the MethodResult itself. The construction of any of these
       objects may happen differently because of the changes made during the RemoteMethod's execution. Replaying
       the request ensures that the MethodResult reflects such changes, yet ensures that the RemoteMethod
       is not executed twice.
    """


    wsgi_app = remote_method_fixture.new_wsgi_app(remote_method=regenerate_method_result_scenarios.remote_method)
    browser = Browser(wsgi_app)

    import sqlalchemy.orm 
    @stubclass(sqlalchemy.orm.Session)
    class TransactionStub:
        is_active=True
        def commit(self):pass
        def rollback(self):pass
    
    def wrapped_nested_transaction():
        return web_fixture.nested_transaction
    
    web_fixture.nested_transaction =  TransactionStub()
    with replaced(Session().begin_nested, wrapped_nested_transaction):
        with CallMonitor(web_fixture.nested_transaction.commit) as monitor:
            browser.post('/_amethod_method', {})
        assert browser.raw_html == regenerate_method_result_scenarios.expected_response
        assert monitor.times_called == 2


class WidgetResultScenarios(Fixture):
    changes_made = False
    def new_WidgetChildStub(self):
        @stubclass(Widget)
        class WidgetChildStub(Widget):
            def __init__(self, view, text):
                super().__init__(view)
                self.text = text
            def render(self): return '<%s>' % self.text
            def get_js(self, context=None): return ['js(%s)' % self.text]
        return WidgetChildStub

    def new_WidgetStub(self):
        fixture = self
        @stubclass(Widget)
        class WidgetStub(Widget):
            css_id = 'an_id'
            def __init__(self, view):
                super().__init__(view)
                message = 'changed contents' if fixture.changes_made else 'initial contents'
                self.add_child(fixture.WidgetChildStub(view, message))
        return WidgetStub

    def new_WidgetWithRemoteMethod(self):
        fixture = self
        @stubclass(Widget)
        class WidgetWithRemoteMethod(Widget):
            def __init__(self, view):
                super().__init__(view)
                method_result = WidgetResult([fixture.WidgetStub(view)])
                def change_something():
                    fixture.changes_made = True
                    if fixture.exception:
                        raise DomainException(message='breaking intentionally', handled_inline=fixture.handle_inline)
                remote_method = RemoteMethod(view, 'amethod', change_something, default_result=method_result,
                                             immutable=False, disable_csrf_check=True)
                view.add_resource(remote_method)
        return WidgetWithRemoteMethod

    @scenario
    def success(self):
        self.exception = False
        self.handle_inline = True
        self.expected_response = {'success': True,
                                  'exception': '',
                                  'result': {'an_id': '<changed contents><script type="text/javascript">js(changed contents)</script>'}}

    @scenario
    def exception(self):
        self.exception = True
        self.handle_inline = False
        self.expected_response = {'success': False,
                                  'exception': 'breaking intentionally',
                                  'result': {'an_id': '<changed contents><script type="text/javascript">js(changed contents)</script>'}}

    @scenario
    def exception_inline(self):
        self.exception = True
        self.handle_inline = True
        self.expected_response = {'success': False,
                                  'exception': '',
                                  'result': {'an_id': '<changed contents><script type="text/javascript">js(changed contents)</script>'}}

@with_fixtures(WebFixture, WidgetResultScenarios)
def test_widgets_that_change_during_method_processing(web_fixture, widget_result_scenarios):
    """The Widget rendered by WidgetResult reflects its Widget as it would have
       looked if it were constructed AFTER the changes effected by executing
       its RemoteMethod have been committed.
    """

    wsgi_app = web_fixture.new_wsgi_app(child_factory=widget_result_scenarios.WidgetWithRemoteMethod.factory())
    browser = Browser(wsgi_app)

    browser.post('/_amethod_method', {})
    json_response = json.loads(browser.raw_html)
    assert json_response == widget_result_scenarios.expected_response


@stubclass(Widget)
class CoactiveWidgetStub(Widget):
    def __init__(self, view, css_id, coactive_widgets):
        super().__init__(view)
        self._coactive_widgets = coactive_widgets
        self.css_id = css_id

    def render_contents(self): 
        return '<%s>' % self.css_id

    @property
    def coactive_widgets(self):
        return super().coactive_widgets + self._coactive_widgets


@with_fixtures(WebFixture)
def test_coactive_widgets(web_fixture):
    """Coactive Widgets of a Widget are Widgets that are included in a WidgetResult for that Widget.

    Included are: the coactive widgets of children of the result widget as well as the coactive widgets of coactive widgets.
    """

    @stubclass(Widget)
    class WidgetWithRemoteMethod(Widget):
        def __init__(self, view):
            super().__init__(view)
            coactive_widgets = [self.add_child(CoactiveWidgetStub(view, 'coactive1', [self.add_child(CoactiveWidgetStub(view, 'coactive2', []))]))]
            result_widget = self.add_child(CoactiveWidgetStub(view, 'main', []))
            result_widget.add_child(CoactiveWidgetStub(view, 'child', coactive_widgets))
            method_result = WidgetResult([result_widget])
            remote_method = RemoteMethod(view, 'amethod', lambda: None, default_result=method_result, disable_csrf_check=True)
            view.add_resource(remote_method)

    wsgi_app = web_fixture.new_wsgi_app(child_factory=WidgetWithRemoteMethod.factory())
    browser = Browser(wsgi_app)

    browser.post('/_amethod_method', {})
    json_response = json.loads(browser.raw_html)
    assert json_response == {'success': True,
                             'exception': '',
                             'result': {
                                'main': '<main><script type="text/javascript"></script>',
                                'coactive1': '<coactive1><script type="text/javascript"></script>',
                                'coactive2': '<coactive2><script type="text/javascript"></script>'}
                             }


@uses(web_fixture=WebFixture)
class CoactiveScenarios(Fixture):
    expected_exception = NoException
    expected_exception_regex = None
    def new_page(self):
        return Div(self.view)

    def new_view(self):
        return self.web_fixture.view

    @scenario
    def descendents_that_are_coactive_are_ignored(self):
        """Descendents that are also coactive_widgets are ignored in the final coactive_widget list."""

        coactive_descendent = CoactiveWidgetStub(self.view, 'coactive_descendent', [])

        widget = self.page.add_child(CoactiveWidgetStub(self.view, 'main', [coactive_descendent]))
        child = widget.add_child(CoactiveWidgetStub(self.view, 'child', []))
        child.add_child(coactive_descendent)

        self.result_widget = widget
        self.expected_coactive_widgets = []
        assert self.result_widget.coactive_widgets == [coactive_descendent]

    @scenario
    def coactive_widgets_include_children_coactive_widgets(self):
        """The coactive widgets of descendents are included in a widget's coactive widgets."""

        coactive_widget = self.page.add_child(CoactiveWidgetStub(self.view, 'coactive_widget', []))
        widget = self.page.add_child(CoactiveWidgetStub(self.view, 'main', []))
        child = widget.add_child(CoactiveWidgetStub(self.view, 'child', [coactive_widget]))

        self.result_widget = widget
        self.expected_coactive_widgets = [coactive_widget]

    @scenario
    def coactiveness_is_transitive(self):
        """The coactive widgets of the coactive widgets of a widget are included in its coactive widgets."""

        coactive_widget_level2 = self.page.add_child(CoactiveWidgetStub(self.view, 'coactive_widget_level2', []))
        coactive_widget_level1 = self.page.add_child(CoactiveWidgetStub(self.view, 'coactive_widget_level1', [coactive_widget_level2]))
        widget = self.page.add_child(CoactiveWidgetStub(self.view, 'main', [coactive_widget_level1]))

        self.result_widget = widget
        self.expected_coactive_widgets = [coactive_widget_level1, coactive_widget_level2]

    @scenario
    def coactive_widgets_cannot_be_parents(self):
        """The ancestor Widgets of a given Widget cannot be its coactive Widgets."""

        grandparent = self.page.add_child(Div(self.view, css_id='grandparent'))
        parent = grandparent.add_child(CoactiveWidgetStub(self.view, 'parent', []))
        child = parent.add_child(CoactiveWidgetStub(self.view, 'child', [grandparent]))

        self.result_widget = child
        self.expected_coactive_widgets = None
        self.expected_exception = ProgrammerError
        self.expected_exception_regex = 'The coactive Widgets of .+ include its ancestor\(s\): .+'


@with_fixtures(WebFixture, CoactiveScenarios)
def test_what_is_included_in_coactive_widgets(web_fixture, coactive_scenarios):

    fixture = coactive_scenarios
    fixture.view.page = fixture.page

    with expected(fixture.expected_exception, fixture.expected_exception_regex):
        coactive_widgets = WidgetResult([fixture.result_widget]).get_coactive_widgets_recursively(fixture.result_widget)
        assert set(coactive_widgets) == set(fixture.expected_coactive_widgets)


