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


import json

from webob import Request

from nose.tools import istest
from reahl.tofu import Fixture, test, scenario, NoException, vassert, expected
from reahl.stubble import CallMonitor, EmptyStub

from reahl.web.ui import Form, NestedForm, Button, Input, TextInput, LabelledBlockInput, TwoColumnPage
from reahl.web.fw import WebExecutionContext, ValidationException, Url, Region
from reahl.component.exceptions import DomainException, ProgrammerError, IsInstance
from reahl.component.modelinterface import IntegerField, BooleanField, EmailField, DateField, \
                                    exposed, Field, Event, Action
from reahl.component.context import ExecutionContext
from reahl.webelixirimpl import PersistedException, UserInput

from reahl.web_dev.fixtures import WebBasicsMixin
from reahl.webdev.tools import WidgetTester, XPath, Browser

class FormFixture(Fixture, WebBasicsMixin):
    def new_error_xpath(self):
        return u'//form[contains(@class, "reahl-form")]/label[contains(@class, "error")]'


@istest
class FormTests(object):
    @test(FormFixture)
    def basic_event_linkup(self, fixture):
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
                events.an_event = Event(label=u'click me', action=Action(self.handle_event))

        model_object = ModelObject()

        class MyForm(Form):
            def __init__(self, view, name, other_view):
                super(MyForm, self).__init__(view, name)
                self.define_event_handler(model_object.events.an_event, target=other_view)
                self.add_child(Button(self, model_object.events.an_event))

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                home = self.define_view(u'/', title=u'Home page')
                other_view = self.define_view(u'/page2', title=u'Page 2')
                home.set_slot(u'main', MyForm.factory(u'myform', other_view))

        webapp = fixture.new_webapp(site_root=MainRegion)
        fixture.reahl_server.set_app(webapp)
        fixture.driver_browser.open('/')

        # clicking on the button triggers the action of the event handler
        vassert( not model_object.handled_event )
        fixture.driver_browser.click(u"//input[@value='click me']")
        vassert( model_object.handled_event )

        # browser has been transitioned to target view
        vassert( fixture.driver_browser.current_url.path == u'/page2' )

    @test(FormFixture)
    def arguments_to_actions(self, fixture):
        """If a Button is created for an Event with_arguments, those arguments are passed to the backend 
           when the Button is clicked."""

        # how you link everything up in code
        class ModelObject(object):
            def handle_event(self, *args):
                self.args = args

            @exposed
            def events(self, events):
                events.an_event = Event(label=u'click me',
                                        action=Action(self.handle_event, [u'one_argument', u'another_argument']),
                                        one_argument=IntegerField(),
                                        another_argument=Field())

        model_object = ModelObject()

        class MyForm(Form):
            def __init__(self, view, name):
                super(MyForm, self).__init__(view, name)
                self.add_child(Button(self, model_object.events.an_event.with_arguments(one_argument=1, another_argument=u'another')))

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                home = self.define_view(u'/', title=u'Home page')
                other_view = self.define_view(u'/page2', title=u'Page 2')
                home.set_slot(u'main', MyForm.factory(u'myform'))
                self.define_transition(model_object.events.an_event, home, other_view)

        webapp = fixture.new_webapp(site_root=MainRegion)
        fixture.reahl_server.set_app(webapp)
        fixture.driver_browser.open('/')

        # when the Action is executed, the correct arguments are passed
        fixture.driver_browser.click(u"//input[@value='click me']")
        vassert( model_object.args == (1, u'another') )


    @test(FormFixture)
    def validation_of_event_arguments(self, fixture):
        """Buttons cannot be created for Events with invalid default arguments."""

        class ModelObject(object):
            @exposed
            def events(self, events):
                events.an_event = Event(label=u'Click me', argument=Field(required=True))

        model_object = ModelObject()
        
        form = Form(fixture.view, u'test')
        form.define_event_handler(model_object.events.an_event)
        
        with expected(ProgrammerError):
            Button(form, model_object.events.an_event)
            
        with expected(NoException):
            Button(form, model_object.events.an_event.with_arguments(argument=u'something'))


      
    @test(FormFixture)
    def basic_field_linkup(self, fixture):
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
                events.an_event = Event(label=u'click me', action=Action(self.handle_event))

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

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                home = self.define_view(u'/', title=u'Home page')
                home.set_slot(u'main', MyForm.factory(u'myform'))


        webapp = fixture.new_webapp(site_root=MainRegion)
        fixture.reahl_server.set_app(webapp)
        fixture.driver_browser.open('/')

        # the initial value rendered in the input
        vassert( not hasattr(model_object, u'field_name') )
        initial_value = fixture.driver_browser.get_value(u"//input[@type='text']")
        vassert( initial_value == u'3' )

        # the user supplied value is marshalled and set on the model object when an event happens
        fixture.driver_browser.type(u"//input[@type='text']", u'5')
        fixture.driver_browser.click(u"//input[@value='click me']")
        vassert( model_object.field_name == 5 )

    @test(FormFixture)
    def wrong_arguments_to_define_event_handler(self, fixture):
        """Passing anything other than an Event to define_event_handler is an error."""

        class MyForm(Form):
            def __init__(self, view, name):
                super(MyForm, self).__init__(view, name)
                self.define_event_handler(EmptyStub())

        webapp = fixture.new_webapp(child_factory=MyForm.factory(u'form'))
        browser = Browser(webapp)
        
        with expected(IsInstance):
            browser.open('/')

    @test(FormFixture)
    def define_event_handler_not_called(self, fixture):
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

        webapp = fixture.new_webapp(child_factory=MyForm.factory(u'form'))
        browser = Browser(webapp)

        def check_exc(exc):
            vassert( str(exc) == u'no Event/Transition available for name an_event' )

        with expected(ProgrammerError, test=check_exc):
            browser.open('/')


    @test(FormFixture)
    def exception_handling(self, fixture):
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
                events.an_event = Event(label=u'click me', action=Action(self.handle_event))
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

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                home = self.define_view(u'/', title=u'Home page')
                other_view = self.define_view(u'/page2', title=u'Page 2')
                home.set_slot(u'main', MyForm.factory(u'myform', other_view))

        webapp = fixture.new_webapp(site_root=MainRegion)
        fixture.reahl_server.set_app(webapp)

        fixture.driver_browser.open('/')

        vassert( not hasattr(model_object, u'field_name') )
        fixture.driver_browser.type(u"//input[@type='text']", u'5')

        # any database stuff that happened when the form was submitted was rolled back
        with CallMonitor(fixture.system_control.orm_control.rollback) as monitor:
            fixture.driver_browser.click(u"//input[@value='click me']")
        vassert( monitor.times_called == 1 )

        # the value input by the user is still displayed on the form, NOT the actual value on the model object        
        vassert( model_object.field_name == 1 )
        retained_value = fixture.driver_browser.get_value(u"//input[@type='text']")
        vassert( retained_value == u'5' )

        # the browser is still on the page with the form which triggered the exception
        vassert( fixture.driver_browser.current_url.path == u'/' )

    @test(FormFixture)
    def rendering_of_form(self, fixture):
        """A Form is always set up to POST to its EventChannel url.  The current page's query string is
           propagated with the POST url if any.  The Form has an id and class to help style it etc."""

        form = Form(fixture.view, u'test_channel')
        tester = WidgetTester(form)
        
        fixture.context.set_request(Request.blank(u'/a/b?x=y', charset='utf8'))
        actual = tester.render_html()

        expected = u'<form id="test_channel" action="/a/b/_test_channel_method?x=y" data-formatter="/__test_channel_format_method" method="POST" class="reahl-form"></form>'
        vassert( actual == expected )
        
        # Case: without querystring
        fixture.context.set_request(Request.blank(u'/a/b', charset='utf8'))
        actual = tester.render_html_tree()

        action = actual.xpath(u'//form')[0].attrib[u'action']
        vassert( action == u'/a/b/_test_channel_method' )
        
    @test(FormFixture)
    def duplicate_forms(self, fixture):
        """It is an error to add more than one form with the same unique_name to a page."""

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                home = self.define_view(u'/', title=u'Home page')
                home.set_slot(u'main', Form.factory(u'myform'))
                home.set_slot(u'secondary', Form.factory(u'myform'))

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)

        def check_exc(ex):
            vassert( str(ex).startswith(u'More than one form was added using the same unique_name') )
        
        with expected(ProgrammerError, test=check_exc):
            browser.open('/')


    @test(FormFixture)
    def nested_forms(self, fixture):
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
                events.nested_event = Event(label=u'click nested', action=Action(self.handle_event))
            @exposed
            def fields(self, fields):
                fields.nested_field = Field(label=u'input nested')

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
                events.outer_event = Event(label=u'click outer', action=Action(self.handle_event))
        outer_model_object = OuterModelObject()
        class OuterForm(Form):
            def __init__(self, view, name):
                super(OuterForm, self).__init__(view, name)
                self.add_child(MyNestedForm(view, u'my_nested_form'))
                self.define_event_handler(outer_model_object.events.outer_event)
                self.add_child(Button(self, outer_model_object.events.outer_event))

        webapp = fixture.new_webapp(child_factory=OuterForm.factory(u'outer_form'))
        fixture.reahl_server.set_app(webapp)
        browser = fixture.driver_browser
        
        browser.open('/')
        browser.type(XPath.input_labelled(u'input nested'), u'some nested input')
        
        browser.click(XPath.button_labelled(u'click nested'))
        
        vassert( nested_model_object.handled_event )
        vassert( not outer_model_object.handled_event )
        
        vassert( nested_model_object.nested_field == u'some nested input' )
        

    @test(FormFixture)
    def form_input_validation(self, fixture):
        """Validation of input happens in JS on the client, but also on the server if JS is bypassed."""
        class ModelObject(object):
            def handle_event(self):
                pass
            @exposed
            def events(self, events):
                events.an_event = Event(label=u'click me', action=Action(self.handle_event))
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

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                home = self.define_view(u'/', title=u'Home page')
                other_view = self.define_view(u'/page2', title=u'Page 2')
                home.set_slot(u'main', MyForm.factory(u'myform', other_view))

        webapp = fixture.new_webapp(site_root=MainRegion, enable_js=True)

        # Case: form validation fails in JS on the client
        #  - Form submission is blocked
        #  - Error message is displayed
        fixture.reahl_server.set_app(webapp)
        fixture.driver_browser.open(u'/')
        fixture.driver_browser.wait_for_element_not_visible(fixture.error_xpath)
        fixture.driver_browser.type(u'//input[@type="text"]', u'not@notvalid')
        fixture.driver_browser.wait_for_element_visible(fixture.error_xpath)

        with fixture.driver_browser.no_page_load_expected():
            fixture.driver_browser.click(u"//input[@value='click me']")

        error_text = fixture.driver_browser.get_text(fixture.error_xpath)
        vassert( error_text == u'field_name should be a valid email address' )

        # Case: form validation fails on the server (assuming no JS on the client to block submission)
        #  - ValidationException is raised (which is dealt with as any DomainException)
        browser = Browser(webapp)
        browser.open('/')
        browser.type('//input[@type="text"]', u'not@notvalid')

        browser.click('//input[@type="submit"]')
        vassert( not hasattr(model_object, 'field_name') )        
        label = browser.get_html_for('//label')
        vassert( label == u'<label for="field_name" class="error">field_name should be a valid email address</label>' )

        vassert( UserInput.query.filter_by(key=u'field_name').count() == 1 ) # The invalid input was persisted
        exception = PersistedException.query.one().exception
        vassert( isinstance(exception, ValidationException) ) # Is was persisted
        vassert( not exception.commit )

        # Case: form validation passes (no-js)
        #  - no ValidationException
        #  - all input is translated to python and set as values on the model objects
        #  - any saved input on the form is cleared
        browser.type(u'//input[@type="text"]', u'valid@home.org')
        browser.click(u"//input[@value='click me']")
        vassert( model_object.field_name == u'valid@home.org' )

        vassert( UserInput.query.filter_by(key=u'field_name').count() == 0 ) # The invalid input was removed
        vassert( PersistedException.query.count() == 0 ) # The exception was removed

        vassert( browser.location_path == u'/page2' )

        # Case: form validation passes (js)
        #  - no ValidationException
        #  - all input is translated to python and set as values on the model objects
        fixture.driver_browser.type(u'//input[@type="text"]', u'valid@home.org')
        fixture.driver_browser.wait_for_element_not_visible(fixture.error_xpath)
        fixture.driver_browser.click(u"//input[@value='click me']")
        vassert( model_object.field_name == u'valid@home.org' )

        vassert( fixture.driver_browser.current_url.path == u'/page2' )



    class QueryStringScenarios(FormFixture):
        def new_other_view(self):
            return self.webapp.define_view(u'/page2', title=u'Page 2')

        def new_form(self):
            form = Form(self.view, u'some_form')
            event = Event(label=u'click me', action=Action(self.action))
            event.bind(u'an_event', None)
            form.define_event_handler(event, target=self.target)
            form.add_child(Button(form, event))
            return form

        @property
        def query_string_on_form_submit(self):
            form_action = self.driver_browser.get_attribute(u'//form', u'action')
            return Url(form_action).query

        @scenario
        def different_target(self):
            self.break_on_submit = False
            self.target_is_other_view = True
            self.initial_qs = u'a=b'
            self.final_qs = u''

        @scenario
        def same_target_by_intent(self):
            self.break_on_submit = False
            self.target_is_other_view = False
            self.target = self.view.as_factory()
            self.initial_qs = u'a=b'
            self.final_qs = u'a=b'

        @scenario
        def same_target_by_exception(self):
            self.break_on_submit = True
            self.target_is_other_view = True
            self.initial_qs = u'a=b'
            self.final_qs = u'a=b'


    @test(QueryStringScenarios)
    def propagation_of_querystring(self, fixture):
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
                events.an_event = Event(label=u'click me', action=Action(self.handle_event))

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

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                home = self.define_view(u'/', title=u'Home page')
                other_view = self.define_view(u'/page2', title=u'Page 2')
                home.set_slot(u'main', MyForm.factory(u'myform', other_view))

        webapp = fixture.new_webapp(site_root=MainRegion)
        fixture.reahl_server.set_app(webapp)
        fixture.driver_browser.open('/?%s' % fixture.initial_qs)

        vassert( fixture.query_string_on_form_submit == fixture.initial_qs )
        fixture.driver_browser.click(u"//input[@value='click me']")
        vassert( fixture.driver_browser.current_url.query == fixture.final_qs )


    @test(FormFixture)
    def event_names_are_canonicalised(self, fixture):
        """The name= attribute of a button is an url encoded string. There is more than one way
           to url encode the same string. The server ensures that different encodings of the same
           string are not mistaken for different names.
        """

        class ModelObject(object):
            def handle_event(self, some_argument):
                self.received_argument = some_argument

            @exposed
            def events(self, events):
                events.an_event = Event(label=u'click me',
                                        action=Action(self.handle_event, [u'some_argument']),
                                        some_argument=Field(default=u'default value'))

        model_object = ModelObject()

        class MyForm(Form):
            def __init__(self, view, name):
                super(MyForm, self).__init__(view, name)
                self.define_event_handler(model_object.events.an_event)
                self.add_child(Button(self, model_object.events.an_event.with_arguments(some_argument=u'f~nnystuff')))

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                home = self.define_view(u'/', title=u'Home page')
                home.set_slot(u'main', MyForm.factory(u'myform'))

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)

        # when the Action is executed, the correct arguments are passed
        browser.post(u'/__myform_method', {u'event.an_event?some_argument=f~nnystuff': ''})
        vassert( model_object.received_argument == u'f~nnystuff' )
        
    @test(FormFixture)
    def alternative_event_trigerring(self, fixture):
        """Events can also be triggered by submitting a Form via Ajax. In such cases the normal redirect-after-submit
           behaviour of the underlying EventChannel is not desirable. This behaviour can be switched off by submitting
           an extra argument along with the Form in order to request the alternative behaviour.
        """

        class ModelObject(object):
            def handle_event(self):
                self.handled_event = True

            @exposed
            def events(self, events):
                events.an_event = Event(label=u'click me',
                                        action=Action(self.handle_event))


        model_object = ModelObject()

        class MyForm(Form):
            def __init__(self, view, name, other_view):
                super(MyForm, self).__init__(view, name)
                self.define_event_handler(model_object.events.an_event, target=other_view)
                self.add_child(Button(self, model_object.events.an_event))

        class MainRegion(Region):
            def assemble(self):
                self.define_main_window(TwoColumnPage)
                home = self.define_view(u'/', title=u'Home page')
                other_view = self.define_view(u'/page2', title=u'Page 2')
                home.set_slot(u'main', MyForm.factory(u'myform', other_view))

        webapp = fixture.new_webapp(site_root=MainRegion)
        browser = Browser(webapp)

        # when POSTing with _noredirect, the Action is executed, but the browser is not redirected to /page2 as usual
        browser.post(u'/__myform_method', {u'event.an_event?': u'', u'_noredirect': u''})
        browser.follow_response()  # Needed to make the test break should a HTTPTemporaryRedirect response be sent
        vassert( model_object.handled_event )
        vassert( browser.location_path != '/page2' )  
        vassert( browser.location_path == '/__myform_method' )  
        
        # the response is a json object reporting the success of the event and a new rendition of the form
        json_dict = json.loads(browser.raw_html)
        vassert( json_dict[u'success'] )

        browser.open('/')
        expected_html = browser.get_inner_html_for(u'//form[1]')
        vassert( json_dict[u'widget'].startswith(expected_html+u'<script') )


    @test(FormFixture)
    def remote_field_validation(self, fixture):
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

        webapp = fixture.new_webapp(child_factory=MyForm.factory('myform'))
        browser = Browser(webapp)

        browser.open(u'/_myform_validate_method?a_field=invalid email address')
        vassert( browser.raw_html == u'"a_field should be a valid email address"' )

        browser.open(u'/_myform_validate_method?a_field=valid@email.org')
        vassert( browser.raw_html == u'true' )
        

    @test(FormFixture)
    def remote_field_formatting(self, fixture):
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

        webapp = fixture.new_webapp(child_factory=MyForm.factory('myform'))
        browser = Browser(webapp)

        browser.open(u'/_myform_format_method?a_field=13 November 2012')
        vassert( browser.raw_html == u'13 Nov 2012' )

        browser.open(u'/_myform_format_method?a_field=invaliddate')
        vassert( browser.raw_html == u'' )











