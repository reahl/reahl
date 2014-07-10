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
import six
from webob import Response
from webob.exc import HTTPMethodNotAllowed

from reahl.stubble import stubclass, exempt
from nose.tools import istest
from reahl.tofu import scenario
from reahl.tofu import test
from reahl.tofu import vassert

from reahl.component.modelinterface import Field
from reahl.webdev.tools import Browser
from reahl.web.fw import Resource
from reahl.web.fw import SubResource
from reahl.web.fw import Widget
from reahl.web_dev.fixtures import  WebFixture


@istest
class SubResourcesTests(object):
    @test(WebFixture)
    def resources(self, fixture):
        """A Resource has the responsibility to handle an HTTP Request. A Resource indicates that it can
           handle a particular HTTP method by having a method named for it. Such method should return
           a Response."""

        @stubclass(Resource)
        class ResourceStub(Resource):
            called = None
            @exempt
            def handle_something(self, request):
                self.called = True
                return 'something'
            @exempt
            def handle_anotherthing(self, request):
                pass
                 
        resource = ResourceStub()
        
        # Case where the HTTP method is not supported
        fixture.request.method = 'koos'
        response = resource.handle_request(fixture.request)
        vassert( isinstance(response, HTTPMethodNotAllowed) )
        vassert( not resource.called )
        vassert( response.headers['allow'] == 'anotherthing, something' )
        
        # Case where the HTTP method is supported
        fixture.request.method = 'SOMEthing'
        response = resource.handle_request(fixture.request)
        vassert( resource.called )
        vassert( response == 'something' )

    @test(WebFixture)
    def simple_sub_resources(self, fixture):
        """During their construction, Widgets can add SubResources to their View.  The SubResource
           will then be available via a special URL underneath the URL of the Widget's View."""
    
        @stubclass(SubResource)
        class ASimpleSubResource(SubResource):
            sub_regex = 'simple_resource'
            sub_path_template = 'simple_resource'
            @exempt
            def handle_get(self, request):
                return Response()

        @stubclass(Widget)
        class WidgetWithSubResource(Widget):
            def __init__(self, view):
                super(WidgetWithSubResource, self).__init__(view)
                view.add_resource(ASimpleSubResource('uniquename'))

        wsgi_app = fixture.new_wsgi_app(view_slots={'main': WidgetWithSubResource.factory()})
        browser = Browser(wsgi_app)
        browser.open('/_uniquename_simple_resource')
        
    @test(WebFixture)
    def dynamic_sub_resources(self, fixture):
        """Sometimes it is undesirable to instantiate a SubResource just for the purpose of adding it 
           to a View. In such cases, A Factory can be added that will construct the SubResource
           on demand, based on a regex which may contain parameters."""
        @stubclass(SubResource)
        class ParameterisedSubResource(SubResource):
            sub_regex = 'dynamic_(?P<param>[^/]+)'
            sub_path_template = 'dynamic_%(param)s'

            def __init__(self, unique_name, param):
                super(ParameterisedSubResource, self).__init__(unique_name)
                self.param = param
                
            @exempt
            def handle_get(self, request):
                return Response(unicode_body=six.text_type(self.param))

            @exempt
            @classmethod
            def create_resource(cls, unique_name, param=None):
                return cls(unique_name, param)

        @stubclass(Widget)
        class WidgetWithSubResource(Widget):
            def __init__(self, view):
                super(WidgetWithSubResource, self).__init__(view)
                view.add_resource_factory(ParameterisedSubResource.factory('uniquename', {'param': Field(required=True)}))


        wsgi_app = fixture.new_wsgi_app(view_slots={'main': WidgetWithSubResource.factory()})
        browser = Browser(wsgi_app)
        browser.open('/_uniquename_dynamic_one')
        vassert( browser.raw_html == 'one' )
        browser.open('/_uniquename_dynamic_two')
        vassert( browser.raw_html == 'two' )

    @test(WebFixture)
    def dynamic_sub_resources_factory_args(self, fixture):
        """Such dynamic SubResources can also be created with arguments specified to its Factory (instead of 
           only from the path)."""
        @stubclass(SubResource)
        class ParameterisedSubResource(SubResource):
            sub_regex = 'dynamic_(?P<path_param>[^/]+)'
            sub_path_template = 'dynamic_%(path_param)s'

            def __init__(self, unique_name, factory_arg, factory_kwarg, path_param):
                super(ParameterisedSubResource, self).__init__(unique_name)
                self.path_param = path_param
                self.factory_arg = factory_arg
                self.factory_kwarg = factory_kwarg
                
            @exempt
            def handle_get(self, request):
                args = '%s|%s|%s' % (self.factory_arg, self.factory_kwarg, self.path_param)
                return Response(unicode_body=six.text_type(args))

            @exempt
            @classmethod
            def create_resource(cls, unique_name, factory_arg, factory_kwarg=None, path_param=None):
                return cls(unique_name, factory_arg, factory_kwarg, path_param)

        @stubclass(Widget)
        class WidgetWithSubResource(Widget):
            def __init__(self, view):
                super(WidgetWithSubResource, self).__init__(view)
                factory = ParameterisedSubResource.factory('uniquename', {'path_param': Field(required=True)}, 'arg to factory', factory_kwarg='kwarg to factory')
                view.add_resource_factory(factory)

        wsgi_app = fixture.new_wsgi_app(view_slots={'main': WidgetWithSubResource.factory()})
        browser = Browser(wsgi_app)
        browser.open('/__uniquename_dynamic_one')
        vassert( browser.raw_html == 'arg to factory|kwarg to factory|one' )


    @test(WebFixture)
    def disambiguating_between_factories(self, fixture):
        """Sometimes, Widgets may need to add more than one SubResource (or Factories) of the same type.
           Since these are of the same type, they will both match the same urls based on their sub_regex.
           For this reason, one can use the unique_name passed to a SubResource or its Factory
           to disambiguate."""
        @stubclass(SubResource)
        class ParameterisedSubResource(SubResource):
            sub_regex = 'path'
            sub_path_template = 'path'

            @exempt
            def handle_get(self, request):
                # We send back the unique_name of the factory so we can test which factory handled the request
                return Response(unicode_body=six.text_type(self.unique_name))

            @exempt
            @classmethod
            def create_resource(cls, unique_name):
                return cls(unique_name)

        @stubclass(Widget)
        class WidgetWithAmbiguousSubResources(Widget):
            def __init__(self, view):
                super(WidgetWithAmbiguousSubResources, self).__init__(view)
                factory1 = ParameterisedSubResource.factory('factory1', {})
                view.add_resource_factory(factory1)
                factory2 = ParameterisedSubResource.factory('factory2', {})
                view.add_resource_factory(factory2)

        wsgi_app = fixture.new_wsgi_app(view_slots={'main': WidgetWithAmbiguousSubResources.factory()})
        browser = Browser(wsgi_app)
        browser.open('/__factory1_path')
        vassert( browser.raw_html == 'factory1' )
        browser.open('/__factory2_path')
        vassert( browser.raw_html == 'factory2' )


    class UrlScenarios(WebFixture):
        @scenario
        def ending_in_slash(self):
            self.view_path = '/a/'
            self.expected_path = '/a/__uniquename_sub_path'
        @scenario
        def not_ending_in_slash(self):
            self.view_path = '/a'
            self.expected_path = '/a/_uniquename_sub_path'
        @scenario
        def only_slash(self):
            self.view_path = '/'
            self.expected_path = '/__uniquename_sub_path'
        
    @test(UrlScenarios)
    def computation_of_url(self, fixture):
        """The URL of a SubResource can be different, depending on the scenario.  This is done so that 
           A SubResource can unambiguously determine the URL of its parent View."""
        @stubclass(SubResource)
        class ASimpleSubResource(SubResource):
            sub_regex = 'sub_path'
            sub_path_template = 'sub_path'

        sub_resource = ASimpleSubResource('uniquename')

        # Calculating the sub_resource's URL from the context of the View
        fixture.request.environ['PATH_INFO'] = fixture.view_path
        actual = sub_resource.get_url()
        vassert( actual.path == fixture.expected_path )

        # Calculating the URL of the parent View from the context of the SubResource
        fixture.request.environ['PATH_INFO'] = fixture.expected_path
        actual = SubResource.get_parent_url()
        vassert( actual.path == fixture.view_path )

        # Calculating the sub_resource's URL from the context of the SubResource
        fixture.request.environ['PATH_INFO'] = fixture.expected_path
        actual = sub_resource.get_url()
        vassert( actual.path == fixture.expected_path )

