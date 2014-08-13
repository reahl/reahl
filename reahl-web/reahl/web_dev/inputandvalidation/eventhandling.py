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
import json

from webob import Request

from nose.tools import istest
from reahl.tofu import Fixture, test, scenario, NoException, vassert, expected
from reahl.stubble import CallMonitor, EmptyStub

from reahl.web.ui import Button
from reahl.web.ui import Panel
from reahl.web.ui import Form
from reahl.web.ui import LabelledBlockInput
from reahl.web.ui import NestedForm
from reahl.web.ui import TextInput
from reahl.web.ui import TwoColumnPage
from reahl.web.fw import Url
from reahl.web.fw import UserInterface
from reahl.web.fw import ValidationException

from reahl.component.exceptions import DomainException, ProgrammerError, IsInstance
from reahl.component.modelinterface import IntegerField, BooleanField, EmailField, DateField, \
                                    exposed, Field, Event, Action
from reahl.webelixirimpl import PersistedException, UserInput

from reahl.web_dev.fixtures import WebBasicsMixin
from reahl.webdev.tools import WidgetTester, XPath, Browser

class FormFixture(Fixture, WebBasicsMixin):
    def new_error_xpath(self):
        return '//form[contains(@class, "reahl-form")]/label[contains(@class, "error")]'


@test(FormFixture)
def basic_event_linkup(fixture):
    """When a user clicks on a Button, the Event to which the Button is linked is triggered on 
       the server, and its corresponding action is executed. After this, the 
       browser is transitioned to the target view as specified by the EventHandler.
    """
    class ModelObject(object):
        handled_event = False
        def handle_event(self):
            self.handled_event = True

        @exposed
        def events(self, events):
            events.an_event = Event(label='click me', action=Action(self.handle_event))

    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name, other_view):
            super(MyForm, self).__init__(view, name)
            self.define_event_handler(model_object.events.an_event, target=other_view)
            self.add_child(Button(self, model_object.events.an_event))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(TwoColumnPage)
            home = self.define_view('/', title='Home page')
            other_view = self.define_view('/page2', title='Page 2')
            home.set_slot('main', MyForm.factory('myform', other_view))

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    fixture.reahl_server.set_app(wsgi_app)
    fixture.driver_browser.open('/')

    # clicking on the button triggers the action of the event handler
    vassert( not model_object.handled_event )
    fixture.driver_browser.click("//input[@value='click me']")
    vassert( model_object.handled_event )

    # browser has been transitioned to target view
    vassert( fixture.driver_browser.current_url.path == '/page2' )

@test(FormFixture)
def arguments_to_actions(fixture):
    """If a Button is created for an Event with_arguments, those arguments are passed to the backend 
       when the Button is clicked."""

    # how you link everything up in code
    class ModelObject(object):
        def handle_event(self, *args):
            self.args = args

        @exposed
        def events(self, events):
            events.an_event = Event(label='click me',
                                    action=Action(self.handle_event, ['one_argument', 'another_argument']),
                                    one_argument=IntegerField(),
                                    another_argument=Field())

    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name):
            super(MyForm, self).__init__(view, name)
            self.add_child(Button(self, model_object.events.an_event.with_arguments(one_argument=1, another_argument='another')))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(TwoColumnPage)
            home = self.define_view('/', title='Home page')
            other_view = self.define_view('/page2', title='Page 2')
            home.set_slot('main', MyForm.factory('myform'))
            self.define_transition(model_object.events.an_event, home, other_view)

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    fixture.reahl_server.set_app(wsgi_app)
    fixture.driver_browser.open('/')

    # when the Action is executed, the correct arguments are passed
    fixture.driver_browser.click("//input[@value='click me']")
    vassert( model_object.args == (1, 'another') )


@test(FormFixture)
def validation_of_event_arguments(fixture):
    """Buttons cannot be created for Events with invalid default arguments."""

    class ModelObject(object):
        @exposed
        def events(self, events):
            events.an_event = Event(label='Click me', argument=Field(required=True))

    model_object = ModelObject()
    
    form = Form(fixture.view, 'test')
    form.define_event_handler(model_object.events.an_event)
    
    with expected(ProgrammerError):
        Button(form, model_object.events.an_event)
        
    with expected(NoException):
        Button(form, model_object.events.an_event.with_arguments(argument='something'))


  
@test(FormFixture)
def basic_field_linkup(fixture):
    """When a form is rendered, the Inputs on it display either the default value as specified
       by the Field with which the Input is associated, or (if set) the value of the attribute
       that Field is bound to.
       
       When a user clicks on a Button, the Input value is set via the Field on the
       model objects to which the Field is bound. This happens before the associated action
       is executed.
    """

    class ModelObject(object):
        def handle_event(self):
            pass

        @exposed
        def events(self, events):
            events.an_event = Event(label='click me', action=Action(self.handle_event))

        @exposed
        def fields(self, fields):
            fields.field_name = IntegerField(default=3)
            
    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name):
            super(MyForm, self).__init__(view, name)
            self.define_event_handler(model_object.events.an_event)
            self.add_child(Button(self, model_object.events.an_event))
            self.add_child(TextInput(self, model_object.fields.field_name))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(TwoColumnPage)
            home = self.define_view('/', title='Home page')
            home.set_slot('main', MyForm.factory('myform'))


    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    fixture.reahl_server.set_app(wsgi_app)
    fixture.driver_browser.open('/')

    # the initial value rendered in the input
    vassert( not hasattr(model_object, 'field_name') )
    initial_value = fixture.driver_browser.get_value("//input[@type='text']")
    vassert( initial_value == '3' )

    # the user supplied value is marshalled and set on the model object when an event happens
    fixture.driver_browser.type("//input[@type='text']", '5')
    fixture.driver_browser.click("//input[@value='click me']")
    vassert( model_object.field_name == 5 )


@test(FormFixture)
def distinguishing_identical_field_names(fixture):
    """A programmer can add different Inputs on the same Form even if their respective Fields are bound
       to identically named attributes of different objects."""

    class ModelObject(object):
        @exposed
        def fields(self, fields):
            fields.field_name = IntegerField()
            
    model_object1 = ModelObject()
    model_object2 = ModelObject()

    class MyForm(Form):
        @exposed
        def events(self, events):
            events.an_event = Event(label='click me')

        def __init__(self, view, name):
            super(MyForm, self).__init__(view, name)
            self.define_event_handler(self.events.an_event)
            self.add_child(Button(self, self.events.an_event))
            
            self.add_child(TextInput(self, model_object1.fields.field_name))
            self.add_child(TextInput(self, model_object2.fields.field_name))

    wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory('form'))
    fixture.reahl_server.set_app(wsgi_app)
    fixture.driver_browser.open('/')

    # the correct input value gets to the correct object despite referencing identically named attributes
    fixture.driver_browser.type('//input[@type="text"][1]', '0')
    fixture.driver_browser.type('//input[@type="text"][2]', '1')
    fixture.driver_browser.click(XPath.button_labelled('click me'))
    vassert( model_object1.field_name == 0 )
    vassert( model_object2.field_name == 1 )


@test(FormFixture)
def wrong_arguments_to_define_event_handler(fixture):
    """Passing anything other than an Event to define_event_handler is an error."""

    class MyForm(Form):
        def __init__(self, view, name):
            super(MyForm, self).__init__(view, name)
            self.define_event_handler(EmptyStub())

    wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory('form'))
    browser = Browser(wsgi_app)
    
    with expected(IsInstance):
        browser.open('/')

@test(FormFixture)
def define_event_handler_not_called(fixture):
    """."""
    class ModelObject(object):
        @exposed
        def events(self, events):
            events.an_event = Event()

    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name):
            super(MyForm, self).__init__(view, name)
            self.add_child(Button(self, model_object.events.an_event))

    wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory('form'))
    browser = Browser(wsgi_app)

    def check_exc(exc):
        vassert( six.text_type(exc) == 'no Event/Transition available for name an_event' )

    with expected(ProgrammerError, test=check_exc):
        browser.open('/')


@test(FormFixture)
def exception_handling(fixture):
    """When a DomainException happens during the handling of an Event:

       The database is rolled back.
       The browser is redirected to GET the original view again (not the target).
       The screen still displays the values the user initially typed, not those on the ModelObject.
    """

    class ModelObject(object):
        def handle_event(self):
            self.field_name = 1
            raise DomainException()
        @exposed
        def events(self, events):
            events.an_event = Event(label='click me', action=Action(self.handle_event))
        @exposed
        def fields(self, fields):
            fields.field_name = IntegerField(default=3)

    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name, other_view):
            super(MyForm, self).__init__(view, name)
            self.define_event_handler(model_object.events.an_event, target=other_view)
            self.add_child(Button(self, model_object.events.an_event))
            self.add_child(TextInput(self, model_object.fields.field_name))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(TwoColumnPage)
            home = self.define_view('/', title='Home page')
            other_view = self.define_view('/page2', title='Page 2')
            home.set_slot('main', MyForm.factory('myform', other_view))

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    fixture.reahl_server.set_app(wsgi_app)

    fixture.driver_browser.open('/')

    vassert( not hasattr(model_object, 'field_name') )
    fixture.driver_browser.type("//input[@type='text']", '5')

    # any database stuff that happened when the form was submitted was rolled back
    with CallMonitor(fixture.system_control.orm_control.rollback) as monitor:
        fixture.driver_browser.click("//input[@value='click me']")
    vassert( monitor.times_called == 1 )

    # the value input by the user is still displayed on the form, NOT the actual value on the model object        
    vassert( model_object.field_name == 1 )
    retained_value = fixture.driver_browser.get_value("//input[@type='text']")
    vassert( retained_value == '5' )

    # the browser is still on the page with the form which triggered the exception
    vassert( fixture.driver_browser.current_url.path == '/' )

@test(FormFixture)
def rendering_of_form(fixture):
    """A Form is always set up to POST to its EventChannel url.  The current page's query string is
       propagated with the POST url if any.  The Form has an id and class to help style it etc."""

    form = Form(fixture.view, 'test_channel')
    tester = WidgetTester(form)
    
    fixture.context.set_request(Request.blank('/a/b?x=y', charset='utf8'))
    actual = tester.render_html()

    expected = '<form id="test_channel" action="/a/b/_test_channel_method?x=y" data-formatter="/__test_channel_format_method" method="POST" class="reahl-form"></form>'
    vassert( actual == expected )
    
    # Case: without querystring
    fixture.context.set_request(Request.blank('/a/b', charset='utf8'))
    actual = tester.render_html_tree()

    action = actual.xpath('//form')[0].attrib['action']
    vassert( action == '/a/b/_test_channel_method' )


@test(FormFixture)
def duplicate_forms(fixture):
    """It is an error to add more than one form with the same unique_name to a page."""

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(TwoColumnPage)
            home = self.define_view('/', title='Home page')
            home.set_slot('main', Form.factory('myform'))
            home.set_slot('secondary', Form.factory('myform'))

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    def check_exc(ex):
        vassert( six.text_type(ex).startswith('More than one form was added using the same unique_name') )
    
    with expected(ProgrammerError, test=check_exc):
        browser.open('/')



@test(FormFixture)
def check_input_placement(fixture):
    """When a web request is handled, the framework throws an exception if an input might be seperated conceptually from the form they are bound to."""
    
    class ModelObject(object):
        @exposed
        def fields(self, fields):
            fields.name = Field()

    class MainUI(UserInterface):
        def assemble(self):
            page = self.define_page(TwoColumnPage)
            home = self.define_view('/', title='Home page')
            home.set_slot('main', MyForm.factory())

    class MyForm(Form):
        def __init__(self, view):
            super(MyForm, self).__init__(view, 'my_form')
            self.add_child(RerenderableInputPanel(view, self))
            
    class RerenderableInputPanel(Panel):
        def __init__(self, view, form):
            super(RerenderableInputPanel, self).__init__(view, css_id='my_refresh_id')
            self.enable_refresh()
            model_object = ModelObject()
            self.add_child(TextInput(form, model_object.fields.name))

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)            
    browser = Browser(wsgi_app)
    
    def check_exc(ex):
        vassert( 'Inputs are not allowed where they can be refreshed separately from their forms.' in six.text_type(ex))
    
    with expected(ProgrammerError, test=check_exc):
        browser.open('/')
            

@test(FormFixture)
def check_missing_form(fixture):
    """All forms referred to by inputs on a page have to be present on that page."""
    
    class ModelObject(object):
        @exposed
        def fields(self, fields):
            fields.name = Field()
           
    class MyPanel(Panel):
        def __init__(self, view):
            super(MyPanel, self).__init__(view)
            model_object = ModelObject()
            forgotten_form = Form(view, 'myform')
            self.add_child(TextInput(forgotten_form, model_object.fields.name))

    wsgi_app = fixture.new_wsgi_app(child_factory=MyPanel.factory())            
    browser = Browser(wsgi_app)
    
    def check_exc(ex):
        expected_message = 'Could not find form for <TextInput name=name>. '\
                           'Its form, <Form form id=myform> is not present on the current page'
        vassert( six.text_type(ex) == expected_message )
    
    with expected(ProgrammerError, test=check_exc):
        browser.open('/')
            

@test(FormFixture)
def nested_forms(fixture):
    """HTML disallows nesting of forms. A NestedForm can be used to simulate 
       a form which is visually part of another Form. A NestedForm provides a
       form attribute which should be used when creating an Inputs for it.
    """

    class NestedModelObject(object):
        handled_event = False
        def handle_event(self):
            self.handled_event = True
        @exposed
        def events(self, events):
            events.nested_event = Event(label='click nested', action=Action(self.handle_event))
        @exposed
        def fields(self, fields):
            fields.nested_field = Field(label='input nested')

    nested_model_object = NestedModelObject()
    class MyNestedForm(NestedForm):
        def __init__(self, view, name):
            super(MyNestedForm, self).__init__(view, name)
            self.define_event_handler(nested_model_object.events.nested_event)
            self.add_child(Button(self.form, nested_model_object.events.nested_event))
            self.add_child(LabelledBlockInput(TextInput(self.form, nested_model_object.fields.nested_field)))

    class OuterModelObject(object):
        handled_event = False
        def handle_event(self):
            self.handled_event = True
        @exposed
        def events(self, events):
            events.outer_event = Event(label='click outer', action=Action(self.handle_event))
    outer_model_object = OuterModelObject()
    class OuterForm(Form):
        def __init__(self, view, name):
            super(OuterForm, self).__init__(view, name)
            self.add_child(MyNestedForm(view, 'my_nested_form'))
            self.define_event_handler(outer_model_object.events.outer_event)
            self.add_child(Button(self, outer_model_object.events.outer_event))

    wsgi_app = fixture.new_wsgi_app(child_factory=OuterForm.factory('outer_form'))
    fixture.reahl_server.set_app(wsgi_app)
    browser = fixture.driver_browser
    
    browser.open('/')
    browser.type(XPath.input_labelled('input nested'), 'some nested input')
    
    browser.click(XPath.button_labelled('click nested'))
    
    vassert( nested_model_object.handled_event )
    vassert( not outer_model_object.handled_event )
    
    vassert( nested_model_object.nested_field == 'some nested input' )
    

@test(FormFixture)
def form_input_validation(fixture):
    """Validation of input happens in JS on the client, but also on the server if JS is bypassed."""
    class ModelObject(object):
        def handle_event(self):
            pass
        @exposed
        def events(self, events):
            events.an_event = Event(label='click me', action=Action(self.handle_event))
        @exposed
        def fields(self, fields):
            fields.field_name = EmailField()

    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name, other_view):
            super(MyForm, self).__init__(view, name)
            self.define_event_handler(model_object.events.an_event, target=other_view)
            self.add_child(Button(self, model_object.events.an_event))
            self.add_child(TextInput(self, model_object.fields.field_name))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(TwoColumnPage)
            home = self.define_view('/', title='Home page')
            other_view = self.define_view('/page2', title='Page 2')
            home.set_slot('main', MyForm.factory('myform', other_view))

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI, enable_js=True)

    # Case: form validation fails in JS on the client
    #  - Form submission is blocked
    #  - Error message is displayed
    fixture.reahl_server.set_app(wsgi_app)
    fixture.driver_browser.open('/')
    fixture.driver_browser.wait_for_element_not_visible(fixture.error_xpath)
    fixture.driver_browser.type('//input[@type="text"]', 'not@notvalid')
    fixture.driver_browser.wait_for_element_visible(fixture.error_xpath)

    with fixture.driver_browser.no_page_load_expected():
        fixture.driver_browser.click("//input[@value='click me']")

    error_text = fixture.driver_browser.get_text(fixture.error_xpath)
    vassert( error_text == 'field_name should be a valid email address' )

    # Case: form validation fails on the server (assuming no JS on the client to block submission)
    #  - ValidationException is raised (which is dealt with as any DomainException)
    browser = Browser(wsgi_app)
    browser.open('/')
    browser.type('//input[@type="text"]', 'not@notvalid')

    browser.click('//input[@type="submit"]')
    vassert( not hasattr(model_object, 'field_name') )        
    label = browser.get_html_for('//label')
    vassert( label == '<label for="field_name" class="error">field_name should be a valid email address</label>' )

    vassert( UserInput.query.filter_by(key='field_name').count() == 1 ) # The invalid input was persisted
    exception = PersistedException.query.one().exception
    vassert( isinstance(exception, ValidationException) ) # Is was persisted
    vassert( not exception.commit )

    # Case: form validation passes (no-js)
    #  - no ValidationException
    #  - all input is translated to python and set as values on the model objects
    #  - any saved input on the form is cleared
    browser.type('//input[@type="text"]', 'valid@home.org')
    browser.click("//input[@value='click me']")
    vassert( model_object.field_name == 'valid@home.org' )

    vassert( UserInput.query.filter_by(key='field_name').count() == 0 ) # The invalid input was removed
    vassert( PersistedException.query.count() == 0 ) # The exception was removed

    vassert( browser.location_path == '/page2' )

    # Case: form validation passes (js)
    #  - no ValidationException
    #  - all input is translated to python and set as values on the model objects
    fixture.driver_browser.type('//input[@type="text"]', 'valid@home.org')
    fixture.driver_browser.wait_for_element_not_visible(fixture.error_xpath)
    fixture.driver_browser.click("//input[@value='click me']")
    vassert( model_object.field_name == 'valid@home.org' )

    vassert( fixture.driver_browser.current_url.path == '/page2' )



class QueryStringScenarios(FormFixture):
    def new_other_view(self):
        return self.wsgi_app.define_view('/page2', title='Page 2')

    def new_form(self):
        form = Form(self.view, 'some_form')
        event = Event(label='click me', action=Action(self.action))
        event.bind('an_event', None)
        form.define_event_handler(event, target=self.target)
        form.add_child(Button(form, event))
        return form

    @property
    def query_string_on_form_submit(self):
        form_action = self.driver_browser.get_attribute('//form', 'action')
        return Url(form_action).query

    @scenario
    def different_target(self):
        self.break_on_submit = False
        self.target_is_other_view = True
        self.initial_qs = 'a=b'
        self.final_qs = ''

    @scenario
    def same_target_by_intent(self):
        self.break_on_submit = False
        self.target_is_other_view = False
        self.target = self.view.as_factory()
        self.initial_qs = 'a=b'
        self.final_qs = 'a=b'

    @scenario
    def same_target_by_exception(self):
        self.break_on_submit = True
        self.target_is_other_view = True
        self.initial_qs = 'a=b'
        self.final_qs = 'a=b'


@test(QueryStringScenarios)
def propagation_of_querystring(fixture):
    """The query string of the original View visited is maintained through the GET/POST cycle.
       If, for whatever reason (exception or intent) the browser should stay on the same
       View after POSTing, the query string is maintained to that point.
       Else, the query string is cleared.
    """
    class ModelObject(object):
        def handle_event(self):
            if fixture.break_on_submit:
                raise DomainException()
        @exposed
        def events(self, events):
            events.an_event = Event(label='click me', action=Action(self.handle_event))

    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name, other_view):
            super(MyForm, self).__init__(view, name)
            if fixture.target_is_other_view:
                target = other_view
            else:
                target = view.as_factory()
            self.define_event_handler(model_object.events.an_event, target=target)
            self.add_child(Button(self, model_object.events.an_event))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(TwoColumnPage)
            home = self.define_view('/', title='Home page')
            other_view = self.define_view('/page2', title='Page 2')
            home.set_slot('main', MyForm.factory('myform', other_view))

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    fixture.reahl_server.set_app(wsgi_app)
    fixture.driver_browser.open('/?%s' % fixture.initial_qs)

    vassert( fixture.query_string_on_form_submit == fixture.initial_qs )
    fixture.driver_browser.click("//input[@value='click me']")
    vassert( fixture.driver_browser.current_url.query == fixture.final_qs )


@test(FormFixture)
def event_names_are_canonicalised(fixture):
    """The name= attribute of a button is an url encoded string. There is more than one way
       to url encode the same string. The server ensures that different encodings of the same
       string are not mistaken for different names.
    """

    class ModelObject(object):
        def handle_event(self, some_argument):
            self.received_argument = some_argument

        @exposed
        def events(self, events):
            events.an_event = Event(label='click me',
                                    action=Action(self.handle_event, ['some_argument']),
                                    some_argument=Field(default='default value'))

    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name):
            super(MyForm, self).__init__(view, name)
            self.define_event_handler(model_object.events.an_event)
            self.add_child(Button(self, model_object.events.an_event.with_arguments(some_argument='f~nnystuff')))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(TwoColumnPage)
            home = self.define_view('/', title='Home page')
            home.set_slot('main', MyForm.factory('myform'))

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    # when the Action is executed, the correct arguments are passed
    browser.post('/__myform_method', {'event.an_event?some_argument=f~nnystuff': ''})
    vassert( model_object.received_argument == 'f~nnystuff' )


@test(FormFixture)
def alternative_event_trigerring(fixture):
    """Events can also be triggered by submitting a Form via Ajax. In such cases the normal redirect-after-submit
       behaviour of the underlying EventChannel is not desirable. This behaviour can be switched off by submitting
       an extra argument along with the Form in order to request the alternative behaviour.
    """

    class ModelObject(object):
        def handle_event(self):
            self.handled_event = True

        @exposed
        def events(self, events):
            events.an_event = Event(label='click me',
                                    action=Action(self.handle_event))


    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name, other_view):
            super(MyForm, self).__init__(view, name)
            self.define_event_handler(model_object.events.an_event, target=other_view)
            self.add_child(Button(self, model_object.events.an_event))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(TwoColumnPage)
            home = self.define_view('/', title='Home page')
            other_view = self.define_view('/page2', title='Page 2')
            home.set_slot('main', MyForm.factory('myform', other_view))

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    # when POSTing with _noredirect, the Action is executed, but the browser is not redirected to /page2 as usual
    browser.post('/__myform_method', {'event.an_event?': '', '_noredirect': ''})
    browser.follow_response()  # Needed to make the test break should a HTTPTemporaryRedirect response be sent
    vassert( model_object.handled_event )
    vassert( browser.location_path != '/page2' )  
    vassert( browser.location_path == '/__myform_method' )  
    
    # the response is a json object reporting the success of the event and a new rendition of the form
    json_dict = json.loads(browser.raw_html)
    vassert( json_dict['success'] )

    browser.open('/')
    expected_html = browser.get_inner_html_for('//form[1]')
    vassert( json_dict['widget'].startswith(expected_html+'<script') )


@test(FormFixture)
def remote_field_validation(fixture):
    """A Form contains a RemoteMethod that can be used to validate any of its fields via HTTP.
    """

    class ModelObject(object):
        @exposed
        def fields(self, fields):
            fields.a_field = EmailField()

    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name):
            super(MyForm, self).__init__(view, name)
            self.add_child(TextInput(self, model_object.fields.a_field))

    wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory('myform'))
    browser = Browser(wsgi_app)

    browser.open('/_myform_validate_method?a_field=invalid email address')
    vassert( browser.raw_html == '"a_field should be a valid email address"' )

    browser.open('/_myform_validate_method?a_field=valid@email.org')
    vassert( browser.raw_html == 'true' )
    

@test(FormFixture)
def remote_field_formatting(fixture):
    """A Form contains a RemoteMethod that can be used to reformat any of its fields via HTTP.
    """

    class ModelObject(object):
        @exposed
        def fields(self, fields):
            fields.a_field = DateField()

    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name):
            super(MyForm, self).__init__(view, name)
            self.add_child(TextInput(self, model_object.fields.a_field))

    wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory('myform'))
    browser = Browser(wsgi_app)

    browser.open('/_myform_format_method?a_field=13 November 2012')
    vassert( browser.raw_html == '13 Nov 2012' )

    browser.open('/_myform_format_method?a_field=invaliddate')
    vassert( browser.raw_html == '' )










