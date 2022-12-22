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



import urllib.parse

from reahl.tofu import expected
from reahl.tofu.pytestsupport import with_fixtures

from reahl.browsertools.browsertools import Browser, XPath
from reahl.component.modelinterface import Event, Field, Action, ExposedNames, IntegerField
from reahl.component.exceptions import ProgrammerError

from reahl.web.fw import UserInterface, ViewPreCondition, Redirect, Detour, Return, IdentityDictionary, UrlBoundView
from reahl.web.ui import HTML5Page, Form, ButtonInput, A

from reahl.web_dev.fixtures import WebFixture, BasicPageLayout


class FormWithButton(Form):
    def __init__(self, view, event):
        super().__init__(view, 'test_events')
        self.add_child(ButtonInput(self, event))
                

@with_fixtures(WebFixture)
def test_basic_transition(web_fixture):
    """Transitions express how the browser is ferried between Views in reaction to user-initiated Events."""
    fixture  = web_fixture

    def do_something():
        fixture.did_something = True

    class UIWithTwoViews(UserInterface):
        def assemble(self):
            event = Event(label='Click me', action=Action(do_something))
            event.bind('anevent', None)
            viewa = self.define_view('/viewa', title='View a')
            viewa.set_slot('main', FormWithButton.factory(event))
            viewb = self.define_view('/viewb', title='View b')
            viewb.set_slot('main', FormWithButton.factory(event))
            self.define_transition(event, viewa, viewb)

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            self.define_user_interface('/a_ui',  UIWithTwoViews,  IdentityDictionary(), name='test_ui')

    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    # The transition works from viewa
    fixture.did_something = False
    browser.open('/a_ui/viewa')
    browser.click('//input[@value="Click me"]')
    assert browser.current_url.path == '/a_ui/viewb'
    assert fixture.did_something

    # The transition does not work from viewb
    fixture.did_something = False
    browser.open('/a_ui/viewb')
    with expected(ProgrammerError):
        browser.click('//input[@value="Click me"]')
    assert not fixture.did_something


@with_fixtures(WebFixture)
def test_guards(web_fixture):
    """Guards can be set on Transitions. A Transition is only elegible for firing if its guard is True."""
    fixture = web_fixture
    fixture.guard_value = None
    adjustable_guard = Action(lambda:fixture.guard_value)

    false_guard = Action(lambda:False)

    class UIWithGuardedTransitions(UserInterface):
        def assemble(self):
            event = Event(label='Click me')
            event.bind('anevent', None)
            viewa = self.define_view('/viewa', title='View a')
            viewa.set_slot('main', FormWithButton.factory(event))
            viewb = self.define_view('/viewb', title='View b')
            viewc = self.define_view('/viewc', title='View c')
            self.define_transition(event, viewa, viewb, guard=false_guard)
            self.define_transition(event, viewa, viewc, guard=adjustable_guard)

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            self.define_user_interface('/a_ui',  UIWithGuardedTransitions,  IdentityDictionary(), name='test_ui')


    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    # The transition with True guard is the one followed
    fixture.guard_value = True
    browser.open('/a_ui/viewa')
    browser.click('//input[@value="Click me"]')
    assert browser.current_url.path == '/a_ui/viewc'

    # If there is no Transition with a True guard, fail
    fixture.guard_value = False
    browser.open('/a_ui/viewa')
    with expected(ProgrammerError):
        browser.click('//input[@value="Click me"]')


@with_fixtures(WebFixture)
def test_local_transition(web_fixture):
    """A local Transition has its source as its target."""
    fixture = web_fixture
    def do_something():
        fixture.did_something = True

    fixture.guard_passes = True
    guard = Action(lambda:fixture.guard_passes)

    class UIWithAView(UserInterface):
        def assemble(self):
            event = Event(label='Click me', action=Action(do_something))
            event.bind('anevent', None)
            viewa = self.define_view('/viewa', title='View a')
            viewa.set_slot('main', FormWithButton.factory(event))
            self.define_local_transition(event, viewa, guard=guard)

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            self.define_user_interface('/a_ui',  UIWithAView,  IdentityDictionary(), name='test_ui')


    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    # The transition works from viewa
    fixture.did_something = False
    browser.open('/a_ui/viewa')
    browser.click('//input[@value="Click me"]')
    assert browser.current_url.path == '/a_ui/viewa'
    assert fixture.did_something

    # But it is also guarded
    fixture.guard_passes = False
    browser.open('/a_ui/viewa')
    with expected(ProgrammerError):
        browser.click('//input[@value="Click me"]')


@with_fixtures(WebFixture)
def test_transitions_to_parameterised_views(web_fixture):
    """When a Button is placed for an Event that may trigger a Transition to a parameterised View,
       the Event should be bound to the arguments to be used for the target View, using .with_arguments()"""

    class ModelObject:
        events = ExposedNames()
        events.an_event = lambda i: Event(label='click me', event_argument1=IntegerField(),
                                          event_argument2=IntegerField())

    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name):
            super().__init__(view, name)
            event = model_object.events.an_event.with_arguments(event_argument1=1, event_argument2=2, view_argument=3)
            self.add_child(ButtonInput(self, event))

    class ParameterisedView(UrlBoundView):
        def assemble(self, event_argument1=None, view_argument=None):
            self.title = 'View with event_argument1: %s%s and view_argument: %s%s' \
                        % (event_argument1, type(event_argument1), view_argument, type(view_argument))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            home = self.define_view('/', title='Home page')

            other_view = self.define_view('/page2', title='Page 2',
                                          view_class=ParameterisedView,
                                          event_argument1=IntegerField(required=True),
                                          view_argument=IntegerField(required=True))
            home.set_slot('main', MyForm.factory('myform'))

            self.define_transition(model_object.events.an_event, home, other_view)


    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    web_fixture.reahl_server.set_app(wsgi_app)
    web_fixture.driver_browser.open('/')

    # when the Action is executed, the correct arguments are passed to the View
    web_fixture.driver_browser.click("//input[@value='click me']")
    assert web_fixture.driver_browser.title == 'View with event_argument1: 1%s and view_argument: 3%s' % (type(1), type(3))


@with_fixtures(WebFixture)
def test_transitions_to_parameterised_views_error(web_fixture):
    """If an Event triggers a Transition to a parameterised View, and it was not bound to the arguments
       expected by the target View, an error is raised."""

    class ModelObject:
        events = ExposedNames()
        events.an_event = lambda i: Event(label='Click me')

    model_object = ModelObject()

    class FormWithIncorrectButtonToParameterisedView(Form):
        def __init__(self, view):
            super().__init__(view, 'test_events')
            self.add_child(ButtonInput(self, model_object.events.an_event.with_arguments(arg1='1', arg2='2')))

    class ParameterisedView(UrlBoundView):
        def assemble(self, object_key=None):
            self.title = 'View for: %s' % object_key

    class UIWithParameterisedViews(UserInterface):
        def assemble(self):
            normal_view = self.define_view('/static', title='Static')
            normal_view.set_slot('main', FormWithIncorrectButtonToParameterisedView.factory())
            parameterised_view = self.define_view('/dynamic', view_class=ParameterisedView, object_key=Field(required=True))
            self.define_transition(model_object.events.an_event, normal_view, parameterised_view)

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            self.define_user_interface('/a_ui',  UIWithParameterisedViews,  IdentityDictionary(), name='test_ui')


    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    browser.open('/a_ui/static')
    with expected(ProgrammerError):
        browser.click(XPath.button_labelled('Click me'))


@with_fixtures(WebFixture)
def test_view_preconditions(web_fixture):
    """Views can have Conditions attached to them - if a ViewPreCondition fails upon a GET or HEAD request,
       the specified exception is raised. For all other requests, HTTPNotFound is raised."""
    class SomeException(Exception):
        pass

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            view = self.define_view('/', title='Hello')
            view.set_slot('main', Form.factory('the_form'))
            failing_precondition = ViewPreCondition(lambda: False, exception=SomeException)
            passing_precondition = ViewPreCondition(lambda: True)
            view.add_precondition(passing_precondition)
            view.add_precondition(failing_precondition)

    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    with expected(SomeException):
        browser.open('/')

    browser.post('/_the_form', {}, status=404)


@with_fixtures(WebFixture)
def test_inverse_view_preconditions(web_fixture):
    """A ViewPreCondition can give you another ViewPreCondition which it itself negated, optionally with its own exception."""
    class SomeException(Exception):
        pass

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page)
            view = self.define_view('/', title='Hello')
            passing_precondition = ViewPreCondition(lambda: True)
            failing_precondition = passing_precondition.negated(exception=SomeException)
            view.add_precondition(failing_precondition)


    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    with expected(SomeException):
        browser.open('/')


@with_fixtures(WebFixture)
def test_redirect(web_fixture):
    """Redirect is a special exception that will redirect the browser to another View."""
    class UIWithRedirect(UserInterface):
        def assemble(self):
            viewa = self.define_view('/viewa', title='A')
            viewb = self.define_view('/viewb', title='B')
            failing_precondition = ViewPreCondition(lambda: False, exception=Redirect(viewb.as_bookmark(self)))
            viewa.add_precondition(failing_precondition)

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page)
            self.define_user_interface('/a_ui',  UIWithRedirect,  IdentityDictionary(), name='test_ui')


    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    browser.open('/a_ui/viewa')
    assert browser.current_url.path == '/a_ui/viewb'


@with_fixtures(WebFixture)
def test_detours_and_return_transitions(web_fixture):
    """Detour is a special exception that will redirect the browser to another View, but it also does the
       necessary housekeeping that will allow a return_transition to let the browser return to where the
       Detour was thrown."""
    fixture = web_fixture

    fixture.make_precondition_pass = False
    class UIWithDetour(UserInterface):
        def assemble(self):
            event = Event(label='Click me')
            event.bind('anevent', None)
            viewa = self.define_view('/viewa', title='View a')

            step1 = self.define_view('/firstStepOfDetour', title='Step 1')
            step1.set_slot('main', FormWithButton.factory(event))
            step2 = self.define_view('/lastStepOfDetour', title='Step 2')
            step2.set_slot('main', FormWithButton.factory(event))

            viewa.add_precondition(ViewPreCondition(lambda: fixture.make_precondition_pass, exception=Detour(step1.as_bookmark(self))))
            self.define_transition(event, step1, step2)
            self.define_return_transition(event, step2)

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            self.define_user_interface('/a_ui',  UIWithDetour,  IdentityDictionary(), name='test_ui')


    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)
    fixture.did_something = False

    fixture.make_precondition_pass = False
    browser.open('/a_ui/viewa')
    assert browser.current_url.path == '/a_ui/firstStepOfDetour'

    browser.click('//input[@type="submit"]')
    assert browser.current_url.path == '/a_ui/lastStepOfDetour'

    fixture.make_precondition_pass = True
    browser.click('//input[@type="submit"]')
    assert browser.current_url.path == '/a_ui/viewa'

    # The query string is cleared after such a return (it is used to remember where to return to)
    assert browser.current_url.query == ''


@with_fixtures(WebFixture)
def test_detours_and_explicit_return_view(web_fixture):
    """A Detour can also explicitly set the View to return to."""

    class UIWithDetour(UserInterface):
        def assemble(self):
            event = Event(label='Click me')
            event.bind('anevent', None)
            viewa = self.define_view('/viewa', title='View a')
            explicit_return_view = self.define_view('/explicitReturnView', title='Explicit Return View')

            detour = self.define_view('/detour', title='Detour')
            detour.set_slot('main', FormWithButton.factory(event))

            viewa.add_precondition(ViewPreCondition(lambda: False, exception=Detour(detour.as_bookmark(self), return_to=explicit_return_view.as_bookmark(self))))
            self.define_return_transition(event, detour)

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            self.define_user_interface('/a_ui',  UIWithDetour,  IdentityDictionary(), name='test_ui')


    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    browser.open('/a_ui/viewa')
    assert browser.current_url.path == '/a_ui/detour'

    browser.click('//input[@type="submit"]')
    assert browser.current_url.path == '/a_ui/explicitReturnView'

    # The query string is cleared after such a return (it is used to remember where to return to)
    assert browser.current_url.query == ''


@with_fixtures(WebFixture)
def test_redirect_used_to_return(web_fixture):
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
            self.define_page(HTML5Page)
            self.define_user_interface('/a_ui',  UIWithDetour,  IdentityDictionary(), name='test_ui')


    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    # Normal operation - when a caller can be determined
    browser.open('/a_ui/viewa')
    assert browser.current_url.path == '/a_ui/explicitReturnView'

    #  - the query string is cleared after such a return (it is used to remember where to return to)
    assert browser.current_url.query == ''

    # When a caller cannot be determined, the default is used
    browser.open('/a_ui/detour')
    assert browser.current_url.path == '/a_ui/defaultReturnView'

    #  - the query string is cleared after such a return (it is used to remember where to return to)
    assert browser.current_url.query == ''


@with_fixtures(WebFixture)
def test_unconditional_redirection(web_fixture):
    """You can force an URL to always redirect to a given Bookmark."""

    class UIWithRedirect(UserInterface):
        def assemble(self):
            self.define_view('/target', title='')
            self.define_redirect('/redirected', self.get_bookmark(relative_path='/target'))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page)
            self.define_user_interface('/a_ui',  UIWithRedirect,  IdentityDictionary(), name='test_ui')


    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    browser.open('/a_ui/redirected')
    assert browser.current_url.path == '/a_ui/target'


@with_fixtures(WebFixture)
def test_linking_to_views_marked_as_detour(web_fixture):
    """A View can be marked as the start of a Detour. Where used, a Bookmark for such a View
       will automatically include a returnTo in the its query string. This allows an
       eventual return_transition (or similar) to return to where, eg, a link was clicked from.
       This mechanism works for returning across UserInterfaces."""

    class UIWithLink(UserInterface):
        def assemble(self, bookmark=None):
            self.bookmark = bookmark
            self.define_view('/initial', title='View a').set_slot('main', A.factory_from_bookmark(self.bookmark))


    class UIWithDetour(UserInterface):
        def assemble(self):
            event = Event(label='Click me')
            event.bind('anevent', None)

            step1 = self.define_view('/firstStepOfDetour', title='Step 1', detour=True)
            step1.set_slot('main', FormWithButton.factory(event))
            step2 = self.define_view('/lastStepOfDetour', title='Step 2')
            step2.set_slot('main', FormWithButton.factory(event))

            self.define_transition(event, step1, step2)
            self.define_return_transition(event, step2)

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            detour_ui = self.define_user_interface('/uiWithDetour',  UIWithDetour,  IdentityDictionary(), name='second_ui')
            bookmark = detour_ui.get_bookmark(relative_path='/firstStepOfDetour')
            self.define_user_interface('/uiWithLink',  UIWithLink,  IdentityDictionary(), name='first_ui', bookmark=bookmark)


    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    browser.open('/uiWithLink/initial')
    browser.click('//a')
    assert browser.current_url.path == '/uiWithDetour/firstStepOfDetour'

    browser.click('//input[@type="submit"]')
    assert browser.current_url.path == '/uiWithDetour/lastStepOfDetour'

    browser.click('//input[@type="submit"]')
    assert browser.current_url.path == '/uiWithLink/initial'

    # The query string is cleared after such a return (it is used to remember where to return to)
    assert browser.current_url.query == ''


@with_fixtures(WebFixture)
def test_detour_is_non_reentrant(web_fixture):
    """Once detoured to a View marked as the start of a Detour, a Bookmark to that View itself
    will not re-enter the detour.
    """

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())

            step1 = self.define_view('/firstStepOfDetour', title='Step 1', detour=True)
            step1.set_slot('main', A.factory_from_bookmark(step1.as_bookmark(self)))

            home = self.define_view('/initial', title='View a')
            home.set_slot('main', A.factory_from_bookmark(step1.as_bookmark(self)))


    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    def locationIsSetToReturnTo(url_path):
        return urllib.parse.parse_qs(browser.current_url.query)['returnTo'] == [url_path]

    browser.open('/initial')
    browser.click(XPath.link().with_text('Step 1'))
    assert browser.current_url.path == '/firstStepOfDetour'
    assert locationIsSetToReturnTo('http://localhost/initial')

    browser.click(XPath.link().with_text('Step 1'))
    assert browser.current_url.path == '/firstStepOfDetour'
    assert locationIsSetToReturnTo('http://localhost/initial')
