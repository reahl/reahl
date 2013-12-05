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


from webob.exc import HTTPNotFound
from webob import Request

from nose.tools import istest
from reahl.tofu import Fixture, test
from reahl.tofu import vassert, expected, NoException
from reahl.stubble import EmptyStub

from reahl.web_dev.fixtures import WebFixture, ReahlWebApplicationStub
from reahl.webdev.tools import Browser, XPath
from reahl.component.modelinterface import Event, Field, Action, exposed, IntegerField
from reahl.component.exceptions import ProgrammerError
from reahl.web.ui import Form, TwoColumnPage, Button, A
from reahl.web.fw import Region, ViewPreCondition, Redirect, Detour, Return, IdentityDictionary, UrlBoundView
from reahl.component.context import ExecutionContext


class FormWithButton(Form):
    def __init__(self, view, event):
        super(FormWithButton, self).__init__(view, u'test_events')
        self.add_child(Button(self, event))
                
@istest
class ControlledRegionsTests(object):
    @test(WebFixture)
    def basic_transition(self, fixture):
        """Transitions express how the browser is ferried between Views in reaction to user-initiated Events."""
        def do_something():
            fixture.did_something = True

        class RegionWithTwoViews(Region):
            def assemble(self):
                event = Event(label=u'Click me', action=Action(do_something))
                event.bind(u'anevent', None)
                slot_definitions = {u'main': FormWithButton.factory(event)}
                viewa = self.define_view(u'/viewa', title=u'View a', slot_definitions=slot_definitions)
                viewb = self.define_view(u'/viewb', title=u'View b', slot_definitions=slot_definitions)
                self.define_transition(event, viewa, viewb)

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/aregion',  RegionWithTwoViews,  IdentityDictionary(), name=u'testregion')

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)

        # The transition works from viewa
        fixture.did_something = False
        browser.open('/aregion/viewa')
        browser.click('//input[@value="Click me"]')
        vassert( browser.location_path == u'/aregion/viewb' )
        vassert( fixture.did_something )

        # The transition does not work from viewb
        fixture.did_something = False
        browser.open('/aregion/viewb')
        with expected(ProgrammerError):
            browser.click('//input[@value="Click me"]')
        vassert( not fixture.did_something )

    @test(WebFixture)
    def guards(self, fixture):
        """Guards can be set on Transitions. A Transition is only elegible for firing if its guard is True."""
        fixture.guard_value = None
        adjustable_guard = Action(lambda:fixture.guard_value)

        false_guard = Action(lambda:False)

        class RegionWithGuardedTransitions(Region):
            def assemble(self):
                event = Event(label=u'Click me')
                event.bind(u'anevent', None)
                slot_definitions = {u'main': FormWithButton.factory(event)}
                viewa = self.define_view(u'/viewa', title=u'View a', slot_definitions=slot_definitions)
                viewb = self.define_view(u'/viewb', title=u'View b')
                viewc = self.define_view(u'/viewc', title=u'View c')
                self.define_transition(event, viewa, viewb, guard=false_guard)
                self.define_transition(event, viewa, viewc, guard=adjustable_guard)

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/aregion',  RegionWithGuardedTransitions,  IdentityDictionary(), name=u'testregion')

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)

        # The transition with True guard is the one followed
        fixture.guard_value = True
        browser.open('/aregion/viewa')
        browser.click('//input[@value="Click me"]')
        vassert( browser.location_path == u'/aregion/viewc' )

        # If there is no Transition with a True guard, fail
        fixture.guard_value = False
        browser.open('/aregion/viewa')
        with expected(ProgrammerError):
            browser.click('//input[@value="Click me"]')

    @test(WebFixture)
    def local_transition(self, fixture):
        """A local Transition has its source as its target."""
        def do_something():
            fixture.did_something = True

        fixture.guard_passes = True
        guard = Action(lambda:fixture.guard_passes)
        
        class RegionWithAView(Region):
            def assemble(self):
                event = Event(label=u'Click me', action=Action(do_something))
                event.bind(u'anevent', None)
                slot_definitions = {u'main': FormWithButton.factory(event)}
                viewa = self.define_view(u'/viewa', title=u'View a', slot_definitions=slot_definitions)
                self.define_local_transition(event, viewa, guard=guard)

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/aregion',  RegionWithAView,  IdentityDictionary(), name=u'testregion')

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)

        # The transition works from viewa
        fixture.did_something = False
        browser.open('/aregion/viewa')
        browser.click('//input[@value="Click me"]')
        vassert( browser.location_path == u'/aregion/viewa' )
        vassert( fixture.did_something )

        # But it is also guarded
        fixture.guard_passes = False
        browser.open('/aregion/viewa')
        with expected(ProgrammerError):
            browser.click('//input[@value="Click me"]')


    @test(WebFixture)
    def transitions_to_parameterised_views(self, fixture):
        """When a Button is placed for an Event that may trigger a Transition to a parameterised View,
           the Event should be bound to the arguments to be used for the target View, using .with_arguments()"""

        class ModelObject(object):
            @exposed
            def events(self, events):
                events.an_event = Event(label=u'click me', event_argument1=IntegerField(), 
                                        event_argument2=IntegerField())

        model_object = ModelObject()

        class MyForm(Form):
            def __init__(self, view, name):
                super(MyForm, self).__init__(view, name)
                event = model_object.events.an_event.with_arguments(event_argument1=1, event_argument2=2, view_argument=3)
                self.add_child(Button(self, event))

        class ParameterisedView(UrlBoundView):
            def assemble(self, event_argument1=None, view_argument=None):
                self.title = u'View with event_argument1: %s%s and view_argument: %s%s' \
                            % (event_argument1, type(event_argument1), view_argument, type(view_argument))
                
        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                home = self.define_view(u'/', title=u'Home page')

                other_view = self.define_view(u'/page2', title=u'Page 2', 
                                              view_class=ParameterisedView, 
                                              event_argument1=IntegerField(required=True),
                                              view_argument=IntegerField(required=True))
                home.set_slot(u'main', MyForm.factory(u'myform'))

                self.define_transition(model_object.events.an_event, home, other_view)

        webapp = fixture.new_webapp(site_root=MainRegion)
        fixture.reahl_server.set_app(webapp)
        fixture.driver_browser.open('/')

        # when the Action is executed, the correct arguments are passed to the View
        fixture.driver_browser.click(u"//input[@value='click me']")
        vassert( fixture.driver_browser.title == u'View with event_argument1: 1<type \'int\'> and view_argument: 3<type \'int\'>' )


    @test(WebFixture)
    def transitions_to_parameterised_views_error(self, fixture):
        """If an Event triggers a Transition to a parameterised View, and it was not bound to the arguments
           expected by the target View, an error is raised."""

        class ModelObject(object):
            @exposed
            def events(self, events):
                events.an_event = Event(label=u'Click me')

        model_object = ModelObject()

        class FormWithIncorrectButtonToParameterisedView(Form):
            def __init__(self, view):
                super(FormWithIncorrectButtonToParameterisedView, self).__init__(view, u'test_events')
                self.add_child(Button(self, model_object.events.an_event.with_arguments(arg1='1', arg2='2')))

        class ParameterisedView(UrlBoundView):
            def assemble(self, object_key=None):
                self.title = u'View for: %s' % object_key

        class RegionWithParameterisedViews(Region):
            def assemble(self):
                slot_definitions = {u'main': FormWithIncorrectButtonToParameterisedView.factory()}
                normal_view = self.define_view(u'/static', title=u'Static', slot_definitions=slot_definitions)
                parameterised_view = self.define_view(u'/dynamic', view_class=ParameterisedView, object_key=Field(required=True))
                self.define_transition(model_object.events.an_event, normal_view, parameterised_view)

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/aregion',  RegionWithParameterisedViews,  IdentityDictionary(), name=u'testregion')

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)

        browser.open('/aregion/static')
        with expected(ProgrammerError):
            browser.click(XPath.button_labelled(u'Click me'))


    @test(WebFixture)
    def view_preconditions(self, fixture):
        """Views can have Conditions attached to them - if a ViewPreCondition fails upon a GET or HEAD request,
           the specified exception is raised. For all other requests, HTTPNotFound is raised."""
        class SomeException(Exception):
            pass
            
        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                slot_definitions = {u'main': Form.factory(u'the_form')}
                view = self.define_view(u'/', title=u'Hello', slot_definitions=slot_definitions)
                failing_precondition = ViewPreCondition(lambda: False, exception=SomeException)
                passing_precondition = ViewPreCondition(lambda: True)
                view.add_precondition(passing_precondition)
                view.add_precondition(failing_precondition)

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)

        with expected(SomeException):
            browser.open('/')

        browser.post('/_the_form', {}, status=404)
      
    @test(WebFixture)
    def inverse_view_preconditions(self, fixture):
        """A ViewPreCondition can give you another ViewPreCondition which it itself negated, optionally with its own exception."""
        class SomeException(Exception):
            pass
            
        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                view = self.define_view(u'/', title=u'Hello')
                passing_precondition = ViewPreCondition(lambda: True)
                failing_precondition = passing_precondition.negated(exception=SomeException)
                view.add_precondition(failing_precondition)

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)

        with expected(SomeException):
            browser.open('/')
      
    @test(WebFixture)
    def redirect(self, fixture):
        """Redirect is a special exception that will redirect the browser to another View."""
        class RegionWithRedirect(Region):
            def assemble(self):
                viewa = self.define_view(u'/viewa', title=u'A')
                viewb = self.define_view(u'/viewb', title=u'B')
                failing_precondition = ViewPreCondition(lambda: False, exception=Redirect(viewb.as_bookmark(self)))
                viewa.add_precondition(failing_precondition)
            
        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/aregion',  RegionWithRedirect,  IdentityDictionary(), name=u'testregion')

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)

        browser.open('/aregion/viewa')
        vassert( browser.location_path == u'/aregion/viewb' )

    @test(WebFixture)
    def detours_and_return_transitions(self, fixture):
        """Detour is a special exception that will redirect the browser to another View, but it also does the
           necessary housekeeping that will allow a return_transition to let the browser return to where the 
           Detour was thrown."""
        
        fixture.make_precondition_pass = False
        class RegionWithDetour(Region):
            def assemble(self):
                event = Event(label=u'Click me')
                event.bind(u'anevent', None)
                viewa = self.define_view(u'/viewa', title=u'View a')
                slot_with_button = {u'main': FormWithButton.factory(event)}
                
                step1 = self.define_view(u'/firstStepOfDetour', title=u'Step 1', slot_definitions=slot_with_button)
                step2 = self.define_view(u'/lastStepOfDetour', title=u'Step 2', slot_definitions=slot_with_button)

                viewa.add_precondition(ViewPreCondition(lambda: fixture.make_precondition_pass, exception=Detour(step1.as_bookmark(self))))
                self.define_transition(event, step1, step2)
                self.define_return_transition(event, step2)
            
        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/aregion',  RegionWithDetour,  IdentityDictionary(), name=u'testregion')

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)
        fixture.did_something = False

        fixture.make_precondition_pass = False
        browser.open(u'/aregion/viewa')
        vassert( browser.location_path == u'/aregion/firstStepOfDetour' )
        
        browser.click(u'//input[@type="submit"]')
        vassert( browser.location_path == u'/aregion/lastStepOfDetour' )
                
        fixture.make_precondition_pass = True
        browser.click(u'//input[@type="submit"]')
        vassert( browser.location_path == u'/aregion/viewa' )

        # The query string is cleared after such a return (it is used to remember where to return to)
        vassert( browser.location_query_string == u'' )
        
        
    @test(WebFixture)
    def detours_and_explicit_return_view(self, fixture):
        """A Detour can also explicitly set the View to return to."""
        
        class RegionWithDetour(Region):
            def assemble(self):
                event = Event(label=u'Click me')
                event.bind(u'anevent', None)
                viewa = self.define_view(u'/viewa', title=u'View a')
                explicit_return_view = self.define_view(u'/explicitReturnView', title=u'Explicit Return View')

                slot_with_button = {u'main': FormWithButton.factory(event)}
                detour = self.define_view(u'/detour', title=u'Detour', slot_definitions=slot_with_button)

                viewa.add_precondition(ViewPreCondition(lambda: False, exception=Detour(detour.as_bookmark(self), return_to=explicit_return_view.as_bookmark(self))))
                self.define_return_transition(event, detour)
            
        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/aregion',  RegionWithDetour,  IdentityDictionary(), name=u'testregion')

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)
        
        browser.open(u'/aregion/viewa')
        vassert( browser.location_path == u'/aregion/detour' )
        
        browser.click(u'//input[@type="submit"]')
        vassert( browser.location_path == u'/aregion/explicitReturnView' )

        # The query string is cleared after such a return (it is used to remember where to return to)
        vassert( browser.location_query_string == u'' )
                
        
    @test(WebFixture)
    def redirect_used_to_return(self, fixture):
        """A Return is an exception used with Preconditoins to return automatically to another View (as set by detour),
           instead of using a return_transition (the latter can only be triggered by a user)."""
        
        class RegionWithDetour(Region):
            def assemble(self):
                viewa = self.define_view(u'/viewa', title=u'View a')
                explicit_return_view = self.define_view(u'/explicitReturnView', title=u'Explicit Return View')
                default = self.define_view(u'/defaultReturnView', title=u'Default view to return to')
                detour = self.define_view(u'/detour', title=u'Detour')

                viewa.add_precondition(ViewPreCondition(lambda: False, exception=Detour(detour.as_bookmark(self), return_to=explicit_return_view.as_bookmark(self))))
                detour.add_precondition(ViewPreCondition(lambda: False, exception=Return(default.as_bookmark(self))))

            
        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/aregion',  RegionWithDetour,  IdentityDictionary(), name=u'testregion')

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)

        # Normal operation - when a caller can be determined
        browser.open(u'/aregion/viewa')
        vassert( browser.location_path == u'/aregion/explicitReturnView' )

        #  - the query string is cleared after such a return (it is used to remember where to return to)
        vassert( browser.location_query_string == u'' )
        
        # When a caller cannot be determined, the default is used
        browser.open(u'/aregion/detour')
        vassert( browser.location_path == u'/aregion/defaultReturnView' )
        
        #  - the query string is cleared after such a return (it is used to remember where to return to)
        vassert( browser.location_query_string == u'' )


    @test(WebFixture)
    def unconditional_redirection(self, fixture):
        """You can force an URL to always redirect to a given Bookmark."""

        class RegionWithRedirect(Region):
            def assemble(self):
                self.define_view(u'/target', title=u'')
                self.define_redirect(u'/redirected', self.get_bookmark(relative_path=u'/target'))

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                self.define_region(u'/aregion',  RegionWithRedirect,  IdentityDictionary(), name=u'testregion')

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)

        browser.open('/aregion/redirected')
        vassert( browser.location_path == u'/aregion/target' )

    @test(WebFixture)
    def linking_to_views_marked_as_detour(self, fixture):
        """A View can be marked as the start of a Detour. Where used, a Bookmark for such a View
           will automatically include a returnTo in the its query string. This allows an
           eventual return_transition (or similar) to return to where, eg, a link was clicked from.
           This mechanism works for returning across Regions."""

        class RegionWithLink(Region):
            def assemble(self, bookmark=None):
                self.bookmark = bookmark
                slot_definitions = {u'main': A.factory_from_bookmark(self.bookmark)}
                self.define_view(u'/initial', title=u'View a', slot_definitions=slot_definitions)

        class RegionWithDetour(Region):
            def assemble(self):
                event = Event(label=u'Click me')
                event.bind(u'anevent', None)
                slot_with_button = {u'main': FormWithButton.factory(event)}

                step1 = self.define_view(u'/firstStepOfDetour', title=u'Step 1', slot_definitions=slot_with_button, detour=True)
                step2 = self.define_view(u'/lastStepOfDetour', title=u'Step 2', slot_definitions=slot_with_button)

                self.define_transition(event, step1, step2)
                self.define_return_transition(event, step2)

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                detour_region = self.define_region(u'/regionWithDetour',  RegionWithDetour,  IdentityDictionary(), name=u'second_region')
                bookmark = detour_region.get_bookmark(relative_path='/firstStepOfDetour')
                self.define_region(u'/regionWithLink',  RegionWithLink,  IdentityDictionary(), name=u'first_region', bookmark=bookmark)

                
        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)

        browser.open(u'/regionWithLink/initial')
        browser.click(u'//a')
        vassert( browser.location_path == u'/regionWithDetour/firstStepOfDetour' )
                
        browser.click(u'//input[@type="submit"]')
        vassert( browser.location_path == u'/regionWithDetour/lastStepOfDetour' )

        browser.click(u'//input[@type="submit"]')
        vassert( browser.location_path == u'/regionWithLink/initial' )

        # The query string is cleared after such a return (it is used to remember where to return to)
        vassert( browser.location_query_string == u'' )
