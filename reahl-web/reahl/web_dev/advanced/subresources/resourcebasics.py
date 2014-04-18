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



from webob import Response
from webob.exc import HTTPMethodNotAllowed

from reahl.stubble import stubclass, exempt
from nose.tools import istest
from reahl.tofu import test, Fixture, scenario
from reahl.tofu import vassert

from reahl.component.modelinterface import Field
from reahl.webdev.tools import Browser
from reahl.web.fw import Resource, SubResource, UserInterface, Widget
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
                return u'something'
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
        vassert( response == u'something' )

    @test(WebFixture)
    def simple_sub_resources(self, fixture):
        """During their construction, Widgets can add SubResources to their View.  The SubResource
           will then be available via a special URL underneath the URL of the Widget's View."""
    
        @stubclass(SubResource)
        class ASimpleSubResource(SubResource):
            sub_regex = u'simple_resource'
            sub_path_template = u'simple_resource'
            @exempt
            def handle_get(self, request):
                return Response()

        @stubclass(Widget)
        class WidgetWithSubResource(Widget):
            def __init__(self, view):
                super(WidgetWithSubResource, self).__init__(view)
                view.add_resource(ASimpleSubResource(u'uniquename'))

        wsgi_app = fixture.new_wsgi_app(view_slots={u'main': WidgetWithSubResource.factory()})
        browser = Browser(wsgi_app)
        browser.open('/_uniquename_simple_resource')
        
    @test(WebFixture)
    def dynamic_sub_resources(self, fixture):
        """Sometimes it is undesirable to instantiate a SubResource just for the purpose of adding it 
           to a View. In such cases, A Factory can be added that will construct the SubResource
           on demand, based on a regex which may contain parameters."""
        @stubclass(SubResource)
        class ParameterisedSubResource(SubResource):
            sub_regex = u'dynamic_(?P<param>[^/]+)'
            sub_path_template = u'dynamic_%(param)s'

            def __init__(self, unique_name, param):
                super(ParameterisedSubResource, self).__init__(unique_name)
                self.param = param
                
            @exempt
            def handle_get(self, request):
                return Response(body=str(self.param))

            @exempt
            @classmethod
            def create_resource(cls, unique_name, param=None):
                return cls(unique_name, param)

        @stubclass(Widget)
        class WidgetWithSubResource(Widget):
            def __init__(self, view):
                super(WidgetWithSubResource, self).__init__(view)
                view.add_resource_factory(ParameterisedSubResource.factory(u'uniquename', {u'param': Field(required=True)}))


        wsgi_app = fixture.new_wsgi_app(view_slots={u'main': WidgetWithSubResource.factory()})
        browser = Browser(wsgi_app)
        browser.open('/_uniquename_dynamic_one')
        vassert( browser.raw_html == u'one' )
        browser.open('/_uniquename_dynamic_two')
        vassert( browser.raw_html == u'two' )

    @test(WebFixture)
    def dynamic_sub_resources_factory_args(self, fixture):
        """Such dynamic SubResources can also be created with arguments specified to its Factory (instead of 
           only from the path)."""
        @stubclass(SubResource)
        class ParameterisedSubResource(SubResource):
            sub_regex = u'dynamic_(?P<path_param>[^/]+)'
            sub_path_template = u'dynamic_%(path_param)s'

            def __init__(self, unique_name, factory_arg, factory_kwarg, path_param):
                super(ParameterisedSubResource, self).__init__(unique_name)
                self.path_param = path_param
                self.factory_arg = factory_arg
                self.factory_kwarg = factory_kwarg
                
            @exempt
            def handle_get(self, request):
                args = u'%s|%s|%s' % (self.factory_arg, self.factory_kwarg, self.path_param)
                return Response(body=str(args))

            @exempt
            @classmethod
            def create_resource(cls, unique_name, factory_arg, factory_kwarg=None, path_param=None):
                return cls(unique_name, factory_arg, factory_kwarg, path_param)

        @stubclass(Widget)
        class WidgetWithSubResource(Widget):
            def __init__(self, view):
                super(WidgetWithSubResource, self).__init__(view)
                factory = ParameterisedSubResource.factory(u'uniquename', {u'path_param': Field(required=True)}, u'arg to factory', factory_kwarg=u'kwarg to factory')
                view.add_resource_factory(factory)

        wsgi_app = fixture.new_wsgi_app(view_slots={u'main': WidgetWithSubResource.factory()})
        browser = Browser(wsgi_app)
        browser.open('/__uniquename_dynamic_one')
        vassert( browser.raw_html == u'arg to factory|kwarg to factory|one' )


    @test(WebFixture)
    def disambiguating_between_factories(self, fixture):
        """Sometimes, Widgets may need to add more than one SubResource (or Factories) of the same type.
           Since these are of the same type, they will both match the same urls based on their sub_regex.
           For this reason, one can use the unique_name passed to a SubResource or its Factory
           to disambiguate."""
        @stubclass(SubResource)
        class ParameterisedSubResource(SubResource):
            sub_regex = u'path'
            sub_path_template = u'path'

            @exempt
            def handle_get(self, request):
                # We send back the unique_name of the factory so we can test which factory handled the request
                return Response(body=str(self.unique_name))

            @exempt
            @classmethod
            def create_resource(cls, unique_name):
                return cls(unique_name)

        @stubclass(Widget)
        class WidgetWithAmbiguousSubResources(Widget):
            def __init__(self, view):
                super(WidgetWithAmbiguousSubResources, self).__init__(view)
                factory1 = ParameterisedSubResource.factory(u'factory1', {})
                view.add_resource_factory(factory1)
                factory2 = ParameterisedSubResource.factory(u'factory2', {})
                view.add_resource_factory(factory2)

        wsgi_app = fixture.new_wsgi_app(view_slots={u'main': WidgetWithAmbiguousSubResources.factory()})
        browser = Browser(wsgi_app)
        browser.open('/__factory1_path')
        vassert( browser.raw_html == u'factory1' )
        browser.open('/__factory2_path')
        vassert( browser.raw_html == u'factory2' )


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
            sub_regex = u'sub_path'
            sub_path_template = u'sub_path'

        sub_resource = ASimpleSubResource(u'uniquename')

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

