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


from __future__ import unicode_literals
from __future__ import print_function
import re

from reahl.stubble import stubclass
from nose.tools import istest
from reahl.tofu import scenario
from reahl.tofu import test
from reahl.tofu import vassert, expected

from reahl.webdev.tools import Browser
from reahl.web.fw import CheckedRemoteMethod
from reahl.web.fw import JsonResult
from reahl.web.fw import MethodResult
from reahl.web.fw import RemoteMethod
from reahl.web.fw import Widget
from reahl.web.fw import WidgetResult
from reahl.component.modelinterface import Field, IntegerField
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
        remote_method = RemoteMethod('amethod', callable_object, MethodResult(content_type='ttext/hhtml', charset='utf-8'))
    
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
        vassert( browser.last_response.charset == 'utf-8' )
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
            self.expected_charset = 'utf-8'
            self.expected_content_type = 'application/json'

        @scenario
        def widget(self):
            @stubclass(Widget)
            class WidgetStub(object):
                css_id = 'someid'
                def render_contents(self): return '<the widget contents>'
                def get_contents_js(self, context=None): return ['some', 'some', 'javascript']

            self.method_result = WidgetResult(WidgetStub())
            self.value_to_return = 'ignored in this case'
            self.expected_response = '<the widget contents><script type="text/javascript">javascriptsome</script>'
            self.exception_response = Exception
            self.expected_charset = 'utf-8'
            self.expected_content_type = 'text/html'
            
    @test(ResultScenarios)
    def different_kinds_of_result(self, fixture):
        """Different kinds of MethodResult can be specified for a method."""

        def callable_object():
            return fixture.value_to_return
        remote_method = RemoteMethod('amethod', callable_object, default_result=fixture.method_result)
    
        wsgi_app = fixture.new_wsgi_app(remote_method=remote_method)
        browser = Browser(wsgi_app)
        
        browser.post('/_amethod_method', {})
        vassert( re.match(fixture.expected_response, browser.raw_html) )
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

