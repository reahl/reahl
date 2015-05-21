# Copyright 2013, 2014, 2015 Reahl Software Services (Pty) Ltd. All rights reserved.
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
import re
import json
from webob import Response

from reahl.stubble import stubclass, CallMonitor
from nose.tools import istest
from reahl.tofu import scenario
from reahl.tofu import test
from reahl.tofu import vassert, expected

from reahl.webdev.tools import Browser
from reahl.component.exceptions import DomainException
from reahl.web.fw import CheckedRemoteMethod
from reahl.web.fw import JsonResult
from reahl.web.fw import MethodResult
from reahl.web.fw import RemoteMethod, RegenerateMethodResult
from reahl.web.fw import Widget
from reahl.web.fw import WidgetResult
from reahl.component.modelinterface import Field, IntegerField
from reahl.component.py3compat import ascii_as_bytes_or_str
from reahl.web_dev.fixtures import  WebFixture

class RemoteMethodFixture(WebFixture):
    def new_widget_factory(self, remote_method=None):
        remote_method = remote_method or self.remote_method
        
        @stubclass(Widget)
        class WidgetWithRemoteMethod(Widget):
            def __init__(self, view):
                super(WidgetWithRemoteMethod, self).__init__(view)
                view.add_resource(remote_method)
                
        return WidgetWithRemoteMethod.factory()

    def new_wsgi_app(self, remote_method=None):
        remote_method = remote_method or self.remote_method
        slot_definitions = {'main': self.new_widget_factory(remote_method=remote_method)}
        return super(RemoteMethodFixture, self).new_wsgi_app(view_slots=slot_definitions)
            
        
@istest
class RemoteMethodTests(object):
    @test(WebFixture)
    def remote_methods(self, fixture):
        """A RemoteMethod is a SubResource representing a method on the server side which can be invoked via POSTing to an URL."""

        def callable_object():
            return 'value returned from method'

        encoding = 'koi8_r'  # Deliberate
        remote_method = RemoteMethod('amethod', callable_object, MethodResult(mime_type='ttext/hhtml', encoding=encoding))
    
        @stubclass(Widget)
        class WidgetWithRemoteMethod(Widget):
            def __init__(self, view):
                super(WidgetWithRemoteMethod, self).__init__(view)
                view.add_resource(remote_method)

        wsgi_app = fixture.new_wsgi_app(view_slots={'main': WidgetWithRemoteMethod.factory()})
        browser = Browser(wsgi_app)
        
        # By default you cannot GET, since the method is not immutable
        browser.open('/_amethod_method', status=405)
        
        # POSTing to the URL, returns the result of the method
        browser.post('/_amethod_method', {})
        vassert( browser.raw_html == 'value returned from method' )
        vassert( browser.last_response.charset == encoding)
        vassert( browser.last_response.content_type == 'ttext/hhtml' )
    
    @test(RemoteMethodFixture)
    def exception_handling(self, fixture):
        """The RemoteMethod sends back the six.text_type() of an exception raised for the specified exception class."""
        
        def fail():
            raise Exception('I failed')
        remote_method = RemoteMethod('amethod', fail, MethodResult(catch_exception=Exception))

        wsgi_app = fixture.new_wsgi_app(remote_method=remote_method)
        browser = Browser(wsgi_app)

        browser.post('/_amethod_method', {})
        vassert( browser.raw_html == 'I failed' )

    @test(RemoteMethodFixture)
    def immutable_remote_methods(self, fixture):
        """A RemoteMethod that is immutable is accessible via GET (instead of POST)."""

        def callable_object():
            return 'value returned from method'
        remote_method = RemoteMethod('amethod', callable_object, MethodResult(), immutable=True)
    
        wsgi_app = fixture.new_wsgi_app(remote_method=remote_method)
        browser = Browser(wsgi_app)
        
        # GET, since the method is immutable
        browser.open('/_amethod_method')
        vassert( browser.raw_html == 'value returned from method' )
        
        # POSTing to the URL, is not supported
        browser.post('/_amethod_method', {}, status=405)
    
    
    class ArgumentScenarios(RemoteMethodFixture):
        @scenario
        def get(self):
            self.immutable = True
        @scenario
        def post(self):
            self.immutable = False
            
    @test(ArgumentScenarios)
    def arguments_to_remote_methods(self, fixture):
        """A RemoteMethod can get arguments from a query string or submitted form values, depending on the scenario."""

        def callable_object(**kwargs):
            fixture.method_kwargs = kwargs 
            return ''
        remote_method = RemoteMethod('amethod', callable_object, MethodResult(), immutable=fixture.immutable)
    
        wsgi_app = fixture.new_wsgi_app(remote_method=remote_method)
        browser = Browser(wsgi_app)
        
        kwargs_sent = {'a':'AAA', 'b':'BBB'}
        if fixture.immutable:
            browser.open('/_amethod_method?a=AAA&b=BBB')
        else:
            browser.post('/_amethod_method', kwargs_sent)
        vassert( fixture.method_kwargs == kwargs_sent )

    @test(ArgumentScenarios)
    def checked_arguments(self, fixture):
        """A CheckedRemoteMethod checks and marshalls its parameters using Fields."""

        def callable_object(anint=None, astring=None):
            fixture.method_kwargs = {'anint': anint, 'astring': astring}
            return ''
        remote_method = CheckedRemoteMethod('amethod', callable_object, MethodResult(), 
                                            immutable=fixture.immutable, 
                                            anint=IntegerField(),
                                            astring=Field())
    
        wsgi_app = fixture.new_wsgi_app(remote_method=remote_method)
        browser = Browser(wsgi_app)
        
        if fixture.immutable:
            browser.open('/_amethod_method?anint=5&astring=SupercalifraGilisticexpialidocious')
        else:
            browser.post('/_amethod_method', {'anint':'5', 'astring':'SupercalifraGilisticexpialidocious'})
        vassert( fixture.method_kwargs == {'anint':5, 'astring':'SupercalifraGilisticexpialidocious'} )

    class ResultScenarios(RemoteMethodFixture):
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
        class WidgetStub(object):
            css_id = 'someid'
            def render_contents(self): return '<the widget contents>'
            def get_contents_js(self, context=None): return ['some', 'some', 'javascript']

        @scenario
        def widget(self):
            self.method_result = WidgetResult(self.WidgetStub())
            self.value_to_return = 'ignored in this case'
            self.expected_response = '<the widget contents><script type="text/javascript">javascriptsome</script>'
            self.exception_response = Exception
            self.expected_charset = self.method_result.encoding
            self.expected_content_type = 'text/html'
            self.results_match = lambda x, y: x == y

        @scenario
        def widget_as_json(self):
            self.method_result = WidgetResult(self.WidgetStub(), as_json_and_result=True)
            self.value_to_return = 'ignored in this case'
            self.expected_response = {'widget': '<the widget contents><script type="text/javascript">javascriptsome</script>',
                                      'success': True}
            self.expected_charset = self.method_result.encoding
            self.expected_content_type = 'application/json'
            def results_match(expected, actual):
                return json.loads(actual) == expected
            self.results_match = results_match
            
    @test(ResultScenarios)
    def different_kinds_of_result(self, fixture):
        """Different kinds of MethodResult can be specified for a method."""

        def callable_object():
            return fixture.value_to_return
        remote_method = RemoteMethod('amethod', callable_object, default_result=fixture.method_result)
    
        wsgi_app = fixture.new_wsgi_app(remote_method=remote_method)
        browser = Browser(wsgi_app)
        
        browser.post('/_amethod_method', {})
        vassert( fixture.results_match(fixture.expected_response, browser.raw_html) )
        vassert( browser.last_response.charset == fixture.expected_charset )
        vassert( browser.last_response.content_type == fixture.expected_content_type )

    @test(ResultScenarios.json)
    def exception_handling_for_json(self, fixture):
        """How exceptions are handled with JsonResult."""

        def fail():
            raise Exception('exception text')
        remote_method = RemoteMethod('amethod', fail, default_result=fixture.method_result)
    
        wsgi_app = fixture.new_wsgi_app(remote_method=remote_method)
        browser = Browser(wsgi_app)
        
        browser.post('/_amethod_method', {})
        vassert( browser.raw_html == fixture.exception_response )
        vassert( browser.last_response.charset == fixture.expected_charset )
        vassert( browser.last_response.content_type == fixture.expected_content_type )

    @test(ResultScenarios.widget)
    def exception_handling_for_widgets(self, fixture):
        """How exceptions are handled with WidgetResult."""

        def fail():
            raise Exception('exception text')
        remote_method = RemoteMethod('amethod', fail, default_result=fixture.method_result)
    
        wsgi_app = fixture.new_wsgi_app(remote_method=remote_method)
        browser = Browser(wsgi_app)

        with expected(Exception):
            browser.post('/_amethod_method', {})

    class RegenerateMethodResultScenarios(RemoteMethodFixture):
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
            return RemoteMethod('amethod', callable_to_call, self.method_result, immutable=False)

        @scenario
        def success(self):
            self.exception = False
            self.expected_response = 'success: method was called 1 times'

        @scenario
        def exception(self):
            self.exception = True
            self.expected_response = 'exception: method was called 1 times'

    @test(RegenerateMethodResultScenarios)
    def regenerating_method_results(self, fixture):
        """If a MethodResult is set up to replay_request=True, the view it is part of (and thus itself) is recreated
           before the (new incarnation of the) MethodResult generates its actual response. Replaying the request means recreating
           all Widgets on the current View as well as the MethodResult itself. The construction of any of these 
           objects may happen differently because of the changes made during the RemoteMethod's execution. Replaying
           the request ensures that the MethodResult reflects such changes, yet ensures that the RemoteMethod
           is not executed twice.
        """

        wsgi_app = fixture.new_wsgi_app(remote_method=fixture.remote_method)
        browser = Browser(wsgi_app)
        
        with CallMonitor(fixture.system_control.orm_control.commit) as monitor:
            browser.post('/_amethod_method', {})
        vassert( browser.raw_html == fixture.expected_response )
        vassert( monitor.times_called == 2 )


    class WidgetResultScenarios(WebFixture):
        changes_made = False
        @stubclass(Widget)
        class WidgetChildStub(object):
            is_Widget = True
            def __init__(self, text):
                self.text = text
            def render(self): return '<%s>' % self.text
            def get_js(self, context=None): return ['js(%s)' % self.text]
            
        def new_WidgetStub(self):
            fixture = self
            @stubclass(Widget)
            class WidgetStub(Widget):
                css_id = 'an_id'
                def __init__(self, view):
                    super(WidgetStub, self).__init__(view)
                    message = 'changed contents' if fixture.changes_made else 'initial contents'
                    self.add_child(fixture.WidgetChildStub(message))
            return WidgetStub

        def new_WidgetWithRemoteMethod(self):
            fixture = self
            @stubclass(Widget)
            class WidgetWithRemoteMethod(Widget):
                def __init__(self, view):
                    super(WidgetWithRemoteMethod, self).__init__(view)
                    method_result = WidgetResult(fixture.WidgetStub(view), as_json_and_result=True)
                    def change_something():
                        fixture.changes_made = True
                        if fixture.exception:
                            raise DomainException('ex')
                    remote_method = RemoteMethod('amethod', change_something, default_result=method_result,
                                                 immutable=False)
                    view.add_resource(remote_method)
            return WidgetWithRemoteMethod

        @scenario
        def success(self):
            self.exception = False
            self.expected_response = {'success': True, 
                                      'widget': '<changed contents><script type="text/javascript">js(changed contents)</script>'}

        @scenario
        def exception(self):
            self.exception = True
            self.expected_response = {'success': False, 
                                      'widget': '<changed contents><script type="text/javascript">js(changed contents)</script>'}

    @test(WidgetResultScenarios)
    def widgets_that_change_during_method_processing(self, fixture):
        """The Widget rendered by WidgetResult reflects its Widget as it would have
           looked if it were constructed AFTER the changes effected by executing 
           its RemoteMethod have been committed.
        """
    
        wsgi_app = fixture.new_wsgi_app(child_factory=fixture.WidgetWithRemoteMethod.factory())
        browser = Browser(wsgi_app)
        
        browser.post('/_amethod_method', {})
        json_response = json.loads(browser.raw_html)
        vassert( json_response == fixture.expected_response )
