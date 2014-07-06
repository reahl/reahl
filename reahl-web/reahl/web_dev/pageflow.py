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

from nose.tools import istest
from reahl.tofu import test
from reahl.tofu import expected
from reahl.tofu import vassert

from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import Browser, XPath
from reahl.component.modelinterface import Event, Field, Action, exposed, IntegerField
from reahl.component.exceptions import ProgrammerError
from reahl.web.ui import Form, TwoColumnPage, Button, A
from reahl.web.fw import UserInterface, ViewPreCondition, Redirect, Detour, Return, IdentityDictionary, UrlBoundView


class FormWithButton(Form):
    def __init__(self, view, event):
        super(FormWithButton, self).__init__(view, 'test_events')
        self.add_child(Button(self, event))
                
@istest
class ControlledUserInterfacesTests(object):
    @test(WebFixture)
    def basic_transition(self, fixture):
        """Transitions express how the browser is ferried between Views in reaction to user-initiated Events."""
        def do_something():
            fixture.did_something = True

        class UIWithTwoViews(UserInterface):
            def assemble(self):
                event = Event(label='Click me', action=Action(do_something))
                event.bind('anevent', None)
                slot_definitions = {'main': FormWithButton.factory(event)}
                viewa = self.define_view('/viewa', title='View a', slot_definitions=slot_definitions)
                viewb = self.define_view('/viewb', title='View b', slot_definitions=slot_definitions)
                self.define_transition(event, viewa, viewb)

        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                self.define_user_interface('/a_ui',  UIWithTwoViews,  IdentityDictionary(), name='test_ui')

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        # The transition works from viewa
        fixture.did_something = False
        browser.open('/a_ui/viewa')
        browser.click('//input[@value="Click me"]')
        vassert( browser.location_path == '/a_ui/viewb' )
        vassert( fixture.did_something )

        # The transition does not work from viewb
        fixture.did_something = False
        browser.open('/a_ui/viewb')
        with expected(ProgrammerError):
            browser.click('//input[@value="Click me"]')
        vassert( not fixture.did_something )

    @test(WebFixture)
    def guards(self, fixture):
        """Guards can be set on Transitions. A Transition is only elegible for firing if its guard is True."""
        fixture.guard_value = None
        adjustable_guard = Action(lambda:fixture.guard_value)

        false_guard = Action(lambda:False)

        class UIWithGuardedTransitions(UserInterface):
            def assemble(self):
                event = Event(label='Click me')
                event.bind('anevent', None)
                slot_definitions = {'main': FormWithButton.factory(event)}
                viewa = self.define_view('/viewa', title='View a', slot_definitions=slot_definitions)
                viewb = self.define_view('/viewb', title='View b')
                viewc = self.define_view('/viewc', title='View c')
                self.define_transition(event, viewa, viewb, guard=false_guard)
                self.define_transition(event, viewa, viewc, guard=adjustable_guard)

        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                self.define_user_interface('/a_ui',  UIWithGuardedTransitions,  IdentityDictionary(), name='test_ui')

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        # The transition with True guard is the one followed
        fixture.guard_value = True
        browser.open('/a_ui/viewa')
        browser.click('//input[@value="Click me"]')
        vassert( browser.location_path == '/a_ui/viewc' )

        # If there is no Transition with a True guard, fail
        fixture.guard_value = False
        browser.open('/a_ui/viewa')
        with expected(ProgrammerError):
            browser.click('//input[@value="Click me"]')

    @test(WebFixture)
    def local_transition(self, fixture):
        """A local Transition has its source as its target."""
        def do_something():
            fixture.did_something = True

        fixture.guard_passes = True
        guard = Action(lambda:fixture.guard_passes)
        
        class UIWithAView(UserInterface):
            def assemble(self):
                event = Event(label='Click me', action=Action(do_something))
                event.bind('anevent', None)
                slot_definitions = {'main': FormWithButton.factory(event)}
                viewa = self.define_view('/viewa', title='View a', slot_definitions=slot_definitions)
                self.define_local_transition(event, viewa, guard=guard)

        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                self.define_user_interface('/a_ui',  UIWithAView,  IdentityDictionary(), name='test_ui')

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        # The transition works from viewa
        fixture.did_something = False
        browser.open('/a_ui/viewa')
        browser.click('//input[@value="Click me"]')
        vassert( browser.location_path == '/a_ui/viewa' )
        vassert( fixture.did_something )

        # But it is also guarded
        fixture.guard_passes = False
        browser.open('/a_ui/viewa')
        with expected(ProgrammerError):
            browser.click('//input[@value="Click me"]')


    @test(WebFixture)
    def transitions_to_parameterised_views(self, fixture):
        """When a Button is placed for an Event that may trigger a Transition to a parameterised View,
           the Event should be bound to the arguments to be used for the target View, using .with_arguments()"""

        class ModelObject(object):
            @exposed
            def events(self, events):
                events.an_event = Event(label='click me', event_argument1=IntegerField(), 
                                        event_argument2=IntegerField())

        model_object = ModelObject()

        class MyForm(Form):
            def __init__(self, view, name):
                super(MyForm, self).__init__(view, name)
                event = model_object.events.an_event.with_arguments(event_argument1=1, event_argument2=2, view_argument=3)
                self.add_child(Button(self, event))

        class ParameterisedView(UrlBoundView):
            def assemble(self, event_argument1=None, view_argument=None):
                self.title = 'View with event_argument1: %s%s and view_argument: %s%s' \
                            % (event_argument1, type(event_argument1), view_argument, type(view_argument))
                
        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                home = self.define_view('/', title='Home page')

                other_view = self.define_view('/page2', title='Page 2', 
                                              view_class=ParameterisedView, 
                                              event_argument1=IntegerField(required=True),
                                              view_argument=IntegerField(required=True))
                home.set_slot('main', MyForm.factory('myform'))

                self.define_transition(model_object.events.an_event, home, other_view)

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        fixture.reahl_server.set_app(wsgi_app)
        fixture.driver_browser.open('/')

        # when the Action is executed, the correct arguments are passed to the View
        fixture.driver_browser.click("//input[@value='click me']")
        vassert( fixture.driver_browser.title == 'View with event_argument1: 1<type \'int\'> and view_argument: 3<type \'int\'>' )


    @test(WebFixture)
    def transitions_to_parameterised_views_error(self, fixture):
        """If an Event triggers a Transition to a parameterised View, and it was not bound to the arguments
           expected by the target View, an error is raised."""

        class ModelObject(object):
            @exposed
            def events(self, events):
                events.an_event = Event(label='Click me')

        model_object = ModelObject()

        class FormWithIncorrectButtonToParameterisedView(Form):
            def __init__(self, view):
                super(FormWithIncorrectButtonToParameterisedView, self).__init__(view, 'test_events')
                self.add_child(Button(self, model_object.events.an_event.with_arguments(arg1='1', arg2='2')))

        class ParameterisedView(UrlBoundView):
            def assemble(self, object_key=None):
                self.title = 'View for: %s' % object_key

        class UIWithParameterisedViews(UserInterface):
            def assemble(self):
                slot_definitions = {'main': FormWithIncorrectButtonToParameterisedView.factory()}
                normal_view = self.define_view('/static', title='Static', slot_definitions=slot_definitions)
                parameterised_view = self.define_view('/dynamic', view_class=ParameterisedView, object_key=Field(required=True))
                self.define_transition(model_object.events.an_event, normal_view, parameterised_view)

        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                self.define_user_interface('/a_ui',  UIWithParameterisedViews,  IdentityDictionary(), name='test_ui')

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        browser.open('/a_ui/static')
        with expected(ProgrammerError):
            browser.click(XPath.button_labelled('Click me'))


    @test(WebFixture)
    def view_preconditions(self, fixture):
        """Views can have Conditions attached to them - if a ViewPreCondition fails upon a GET or HEAD request,
           the specified exception is raised. For all other requests, HTTPNotFound is raised."""
        class SomeException(Exception):
            pass
            
        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                slot_definitions = {'main': Form.factory('the_form')}
                view = self.define_view('/', title='Hello', slot_definitions=slot_definitions)
                failing_precondition = ViewPreCondition(lambda: False, exception=SomeException)
                passing_precondition = ViewPreCondition(lambda: True)
                view.add_precondition(passing_precondition)
                view.add_precondition(failing_precondition)

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        with expected(SomeException):
            browser.open('/')

        browser.post('/_the_form', {}, status=404)
      
    @test(WebFixture)
    def inverse_view_preconditions(self, fixture):
        """A ViewPreCondition can give you another ViewPreCondition which it itself negated, optionally with its own exception."""
        class SomeException(Exception):
            pass
            
        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                view = self.define_view('/', title='Hello')
                passing_precondition = ViewPreCondition(lambda: True)
                failing_precondition = passing_precondition.negated(exception=SomeException)
                view.add_precondition(failing_precondition)

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        with expected(SomeException):
            browser.open('/')
      
    @test(WebFixture)
    def redirect(self, fixture):
        """Redirect is a special exception that will redirect the browser to another View."""
        class UIWithRedirect(UserInterface):
            def assemble(self):
                viewa = self.define_view('/viewa', title='A')
                viewb = self.define_view('/viewb', title='B')
                failing_precondition = ViewPreCondition(lambda: False, exception=Redirect(viewb.as_bookmark(self)))
                viewa.add_precondition(failing_precondition)
            
        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                self.define_user_interface('/a_ui',  UIWithRedirect,  IdentityDictionary(), name='test_ui')

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        browser.open('/a_ui/viewa')
        vassert( browser.location_path == '/a_ui/viewb' )

    @test(WebFixture)
    def detours_and_return_transitions(self, fixture):
        """Detour is a special exception that will redirect the browser to another View, but it also does the
           necessary housekeeping that will allow a return_transition to let the browser return to where the 
           Detour was thrown."""
        
        fixture.make_precondition_pass = False
        class UIWithDetour(UserInterface):
            def assemble(self):
                event = Event(label='Click me')
                event.bind('anevent', None)
                viewa = self.define_view('/viewa', title='View a')
                slot_with_button = {'main': FormWithButton.factory(event)}
                
                step1 = self.define_view('/firstStepOfDetour', title='Step 1', slot_definitions=slot_with_button)
                step2 = self.define_view('/lastStepOfDetour', title='Step 2', slot_definitions=slot_with_button)

                viewa.add_precondition(ViewPreCondition(lambda: fixture.make_precondition_pass, exception=Detour(step1.as_bookmark(self))))
                self.define_transition(event, step1, step2)
                self.define_return_transition(event, step2)
            
        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                self.define_user_interface('/a_ui',  UIWithDetour,  IdentityDictionary(), name='test_ui')

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)
        fixture.did_something = False

        fixture.make_precondition_pass = False
        browser.open('/a_ui/viewa')
        vassert( browser.location_path == '/a_ui/firstStepOfDetour' )
        
        browser.click('//input[@type="submit"]')
        vassert( browser.location_path == '/a_ui/lastStepOfDetour' )
                
        fixture.make_precondition_pass = True
        browser.click('//input[@type="submit"]')
        vassert( browser.location_path == '/a_ui/viewa' )

        # The query string is cleared after such a return (it is used to remember where to return to)
        vassert( browser.location_query_string == '' )
        
        
    @test(WebFixture)
    def detours_and_explicit_return_view(self, fixture):
        """A Detour can also explicitly set the View to return to."""
        
        class UIWithDetour(UserInterface):
            def assemble(self):
                event = Event(label='Click me')
                event.bind('anevent', None)
                viewa = self.define_view('/viewa', title='View a')
                explicit_return_view = self.define_view('/explicitReturnView', title='Explicit Return View')

                slot_with_button = {'main': FormWithButton.factory(event)}
                detour = self.define_view('/detour', title='Detour', slot_definitions=slot_with_button)

                viewa.add_precondition(ViewPreCondition(lambda: False, exception=Detour(detour.as_bookmark(self), return_to=explicit_return_view.as_bookmark(self))))
                self.define_return_transition(event, detour)
            
        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                self.define_user_interface('/a_ui',  UIWithDetour,  IdentityDictionary(), name='test_ui')

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)
        
        browser.open('/a_ui/viewa')
        vassert( browser.location_path == '/a_ui/detour' )
        
        browser.click('//input[@type="submit"]')
        vassert( browser.location_path == '/a_ui/explicitReturnView' )

        # The query string is cleared after such a return (it is used to remember where to return to)
        vassert( browser.location_query_string == '' )
                
        
    @test(WebFixture)
    def redirect_used_to_return(self, fixture):
        """A Return is an exception used with Preconditoins to return automatically to another View (as set by detour),
           instead of using a return_transition (the latter can only be triggered by a user)."""
        
        class UIWithDetour(UserInterface):
            def assemble(self):
                viewa = self.define_view('/viewa', title='View a')
                explicit_return_view = self.define_view('/explicitReturnView', title='Explicit Return View')
                default = self.define_view('/defaultReturnView', title='Default view to return to')
                detour = self.define_view('/detour', title='Detour')

                viewa.add_precondition(ViewPreCondition(lambda: False, exception=Detour(detour.as_bookmark(self), return_to=explicit_return_view.as_bookmark(self))))
                detour.add_precondition(ViewPreCondition(lambda: False, exception=Return(default.as_bookmark(self))))

            
        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                self.define_user_interface('/a_ui',  UIWithDetour,  IdentityDictionary(), name='test_ui')

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        # Normal operation - when a caller can be determined
        browser.open('/a_ui/viewa')
        vassert( browser.location_path == '/a_ui/explicitReturnView' )

        #  - the query string is cleared after such a return (it is used to remember where to return to)
        vassert( browser.location_query_string == '' )
        
        # When a caller cannot be determined, the default is used
        browser.open('/a_ui/detour')
        vassert( browser.location_path == '/a_ui/defaultReturnView' )
        
        #  - the query string is cleared after such a return (it is used to remember where to return to)
        vassert( browser.location_query_string == '' )


    @test(WebFixture)
    def unconditional_redirection(self, fixture):
        """You can force an URL to always redirect to a given Bookmark."""

        class UIWithRedirect(UserInterface):
            def assemble(self):
                self.define_view('/target', title='')
                self.define_redirect('/redirected', self.get_bookmark(relative_path='/target'))

        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                self.define_user_interface('/a_ui',  UIWithRedirect,  IdentityDictionary(), name='test_ui')

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        browser.open('/a_ui/redirected')
        vassert( browser.location_path == '/a_ui/target' )

    @test(WebFixture)
    def linking_to_views_marked_as_detour(self, fixture):
        """A View can be marked as the start of a Detour. Where used, a Bookmark for such a View
           will automatically include a returnTo in the its query string. This allows an
           eventual return_transition (or similar) to return to where, eg, a link was clicked from.
           This mechanism works for returning across UserInterfaces."""

        class UIWithLink(UserInterface):
            def assemble(self, bookmark=None):
                self.bookmark = bookmark
                slot_definitions = {'main': A.factory_from_bookmark(self.bookmark)}
                self.define_view('/initial', title='View a', slot_definitions=slot_definitions)

        class UIWithDetour(UserInterface):
            def assemble(self):
                event = Event(label='Click me')
                event.bind('anevent', None)
                slot_with_button = {'main': FormWithButton.factory(event)}

                step1 = self.define_view('/firstStepOfDetour', title='Step 1', slot_definitions=slot_with_button, detour=True)
                step2 = self.define_view('/lastStepOfDetour', title='Step 2', slot_definitions=slot_with_button)

                self.define_transition(event, step1, step2)
                self.define_return_transition(event, step2)

        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                detour_ui = self.define_user_interface('/uiWithDetour',  UIWithDetour,  IdentityDictionary(), name='second_ui')
                bookmark = detour_ui.get_bookmark(relative_path='/firstStepOfDetour')
                self.define_user_interface('/uiWithLink',  UIWithLink,  IdentityDictionary(), name='first_ui', bookmark=bookmark)

                
        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        browser.open('/uiWithLink/initial')
        browser.click('//a')
        vassert( browser.location_path == '/uiWithDetour/firstStepOfDetour' )
                
        browser.click('//input[@type="submit"]')
        vassert( browser.location_path == '/uiWithDetour/lastStepOfDetour' )

        browser.click('//input[@type="submit"]')
        vassert( browser.location_path == '/uiWithLink/initial' )

        # The query string is cleared after such a return (it is used to remember where to return to)
        vassert( browser.location_query_string == '' )
