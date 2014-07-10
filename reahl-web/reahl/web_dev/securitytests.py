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
from reahl.tofu import Fixture
from reahl.tofu import scenario
from reahl.tofu import test
from reahl.tofu import vassert
from reahl.stubble import EmptyStub

from reahl.webdev.tools import WidgetTester, Browser, XPath
from reahl.web_dev.fixtures import WebFixture
from reahl.web.fw import Widget, UserInterface
from reahl.web.ui import Form, TextInput, ButtonInput, Button, Panel, P, TwoColumnPage
from reahl.component.modelinterface import Action
from reahl.component.modelinterface import Allowed
from reahl.component.modelinterface import Event
from reahl.component.modelinterface import Field
from reahl.component.modelinterface import exposed


    
@istest
class SecurityTests(object):
    @test(WebFixture)
    def security_sensitive(self, fixture):
        """A Widget is security sensitive if a read_check is specified for it; one of its
           children is security sensitive, or it was explixitly marked as security sensitive."""
        
        widget = Widget(fixture.view)

        # Case: marked explicitly        
        vassert( not widget.is_security_sensitive )
        widget.set_as_security_sensitive()
        vassert( widget.is_security_sensitive )

        # Case: derived from children
        parent_widget = Widget(fixture.view)
        parent_widget.add_child(widget)        
        vassert( widget.is_security_sensitive )

        # Case: derived from read rights
        def allow(self): return True
        widget_with_rights = Widget(fixture.view, read_check=allow)
        vassert( widget.is_security_sensitive )

    @test(WebFixture)
    def serving_security_sensitive_widgets(self, fixture):
        """If the page is security sensitive, it will only be served on config.web.encrypted_http_scheme,
           else it will only be served on config.web.default_http_scheme."""
        class TestPanel(Panel):
            def __init__(self, view):
                super(TestPanel, self).__init__(view)
                widget = self.add_child(Widget(view))

                if fixture.security_sensitive:
                    widget.set_as_security_sensitive()

        wsgi_app = fixture.new_wsgi_app(child_factory=TestPanel.factory(), enable_js=True)
        fixture.reahl_server.set_app(wsgi_app)

        vassert( fixture.config.web.encrypted_http_scheme == 'https' )
        vassert( fixture.config.web.default_http_scheme == 'http' )

        fixture.security_sensitive = False
        fixture.driver_browser.open('https://localhost:8363/')
        vassert( fixture.driver_browser.current_url.scheme == fixture.config.web.default_http_scheme )
        
        fixture.security_sensitive = True
        fixture.driver_browser.open('http://localhost:8000/')
        vassert( fixture.driver_browser.current_url.scheme == fixture.config.web.encrypted_http_scheme )
        
    @test(Fixture)
    def fields_have_access_rights(self, fixture):
        """Fields have access rights for reading and for writing. By default both reading and writing are allowed.
           This default can be changed by passing an Action (which returns a boolean) for each kind of
           access which will be called to determine whether that kind of access is allowed.
           """

        def not_allowed(): return False

        # Case: the default
        field = Field()
        vassert( field.can_read() )
        vassert( field.can_write() )

        # Case: tailored rights
        field = Field(readable=Action(not_allowed), writable=Action(not_allowed))
        field.bind('field_name', fixture)
        vassert( not field.can_read() )
        vassert( not field.can_write() )
        
    @test(WebFixture)
    def tailored_access_make_inputs_security_sensitive(self, fixture):
        """An Input is sensitive if explicitly set as sensitive, or if its Fields has non-defaulted
           mechanisms for determiing access rights."""

        form = Form(fixture.view, 'some_form')
        field = Field(default=3, readable=Allowed(True))
        field.bind('field_name', EmptyStub())
        input_widget = TextInput(form, field)

        vassert( input_widget.is_security_sensitive )

    class InputRenderingScenarios(WebFixture):
        def new_form(self):
            return Form(self.view, 'some_form')
        def new_field(self):
            field = Field(default=3, readable=self.readable, writable=self.writable)
            field.bind('field_name', EmptyStub())
            return field
        def new_event(self):
            event = Event(readable=self.readable, writable=self.writable)
            event.bind('event_name', EmptyStub())
            self.form.define_event_handler(event)
            return event

        @scenario
        def normal_rendering(self):
            self.readable = Allowed(True)
            self.writable = Allowed(True)
            self.input_widget = TextInput(self.form, self.field)

            self.expected_html = '<input name="field_name" form="some_form" type="text" value="3" class="reahl-textinput">'

        @scenario
        def disabled_rendering(self):
            self.readable = Allowed(True)
            self.writable = Allowed(False)
            self.input_widget = TextInput(self.form, self.field)

            self.expected_html = '<input name="field_name" disabled="disabled" form="some_form" type="text" value="3" class="reahl-textinput">'

        @scenario
        def valueless_rendering(self):
            self.readable = Allowed(False)
            self.writable = Allowed(True)
            self.input_widget = TextInput(self.form, self.field)

            self.expected_html = '<input name="field_name" form="some_form" type="text" value="" class="reahl-textinput">'
        
        @scenario
        def empty_rendering(self):
            self.readable = Allowed(False)
            self.writable = Allowed(False)
            self.input_widget = TextInput(self.form, self.field)

            self.expected_html = ''
            
        @scenario
        def normal_button_rendering(self):
            self.readable = Allowed(True)
            self.writable = Allowed(True)
            self.input_widget = ButtonInput(self.form, self.event)

            self.expected_html = '<input name="event.event_name?" form="some_form" type="submit" value="event_name">'

        @scenario
        def greyed_button_rendering(self):
            self.readable = Allowed(True)
            self.writable = Allowed(False)
            self.input_widget = ButtonInput(self.form, self.event)

            self.expected_html = '<input name="event.event_name?" disabled="disabled" form="some_form" type="submit" value="event_name">'

        @scenario
        def buttons_must_be_readable_to_be_present(self):
            self.readable = Allowed(False)
            self.writable = Allowed(True)
            self.input_widget = ButtonInput(self.form, self.event)

            self.expected_html = ''

        @scenario
        def nothing_allowed_on_button(self):
            self.readable = Allowed(False)
            self.writable = Allowed(False)
            self.input_widget = ButtonInput(self.form, self.event)

            self.expected_html = ''

        def allowed(self):
            return True
        def disallowed(self):
            return False

        @scenario
        def not_readable_widget(self):
            self.input_widget = Widget(self.view, read_check=self.disallowed)
            self.input_widget.add_child(P(self.view, text='some text in a p'))

            self.expected_html = ''

        @scenario
        def readable_but_not_writable_widget(self):
            self.input_widget = Widget(self.view, read_check=self.allowed, write_check=self.disallowed)
            self.input_widget.add_child(P(self.view, text='some text in a p'))

            self.expected_html = '<p>some text in a p</p>'

        @scenario
        def readable_and_writable_widget(self):
            self.input_widget = Widget(self.view, read_check=self.allowed, write_check=self.allowed)
            self.input_widget.add_child(P(self.view, text='some text in a p'))

            self.expected_html = '<p>some text in a p</p>'

        @scenario
        def not_readable_but_writable_widget(self):
            # Think of password field, where the input's value is not readable by a human
            self.input_widget = Widget(self.view, read_check=self.disallowed, write_check=self.allowed)
            self.input_widget.add_child(P(self.view, text='some text in a p'))

            self.expected_html = ''


    @test(InputRenderingScenarios)
    def rendering_inputs(self, fixture):
        """How Inputs render, depending on the rights."""

        tester = WidgetTester(fixture.input_widget)
        
        actual = tester.render_html()
        vassert( actual == fixture.expected_html )


    @test(WebFixture)
    def non_writable_input_is_dealt_with_like_invalid_input(self, fixture):
        """If a form submits a value for an Input that is linked to Field with access rights that prohibit writing,
           the input is silently ignored."""

        class ModelObject(object):
            field_name = 'Original value'
            @exposed
            def events(self, events):
                events.an_event = Event(label='click me')

            @exposed
            def fields(self, fields):
                fields.field_name = Field(default='abc', writable=Allowed(False), disallowed_message='you are not allowed to write this')
        model_object = ModelObject()

        class TestPanel(Panel):
            def __init__(self, view):
                super(TestPanel, self).__init__(view)
                form = self.add_child(Form(view, 'some_form'))
                form.define_event_handler(model_object.events.an_event)
                form.add_child(Button(form, model_object.events.an_event))
                form.add_child(TextInput(form, model_object.fields.field_name))
                fixture.form = form

        wsgi_app = fixture.new_wsgi_app(child_factory=TestPanel.factory())
        browser = Browser(wsgi_app)
        browser.open('/')

        browser.post(fixture.form.event_channel.get_url().path, {'event.an_event?':'', 'field_name': 'illigitimate value'})
        browser.follow_response()
        vassert( model_object.field_name == 'Original value' )


    @test(WebFixture)
    def non_writable_events_are_dealt_with_like_invalid_input(self, fixture):
        """If a form submits an Event with access rights that prohibit writing, a ValidationException is raised."""

        class ModelObject(object):
            @exposed
            def events(self, events):
                events.an_event = Event(label='click me', writable=Allowed(False), 
                                        disallowed_message='you cannot do this')

        model_object = ModelObject()
        class TestPanel(Panel):
            def __init__(self, view):
                super(TestPanel, self).__init__(view)
                form = self.add_child(Form(view, 'some_form'))
                form.define_event_handler(model_object.events.an_event)
                form.add_child(Button(form, model_object.events.an_event))
                fixture.form = form

        wsgi_app = fixture.new_wsgi_app(child_factory=TestPanel.factory())
        browser = Browser(wsgi_app)
        browser.open('/')

        browser.post(fixture.form.event_channel.get_url().path, {'event.an_event?':''})
        browser.follow_response()
        error_label = browser.get_html_for('//label')
        vassert( error_label == '<label for="event.an_event?" class="error">you cannot do this</label>' )

    @test(WebFixture)
    def getting_view(self, fixture):
        """ONLY If a View is readable, it can be GET"""
        def disallowed(): return False
        
        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                self.define_view('/view', 'Title', read_check=disallowed)
        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)
        browser.open('/view', status=403)

    @test(WebFixture)
    def posting_to_view(self, fixture):
        """ONLY If a View is writable, may it be POSTed to"""
        def disallowed(): return False
        
        class MyForm(Form):
            def __init__(self, view):
                super(MyForm, self).__init__(view, 'myform')
                self.define_event_handler(self.events.an_event)
                self.add_child(Button(self, self.events.an_event))
            @exposed
            def events(self, events):
                events.an_event = Event(label='Click me')

        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(TwoColumnPage)
                home = self.define_view('/a_view', 'Title', write_check=disallowed)
                home.set_slot('main', MyForm.factory())
        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
        browser = Browser(wsgi_app)

        browser.open('/a_view')
        browser.click(XPath.button_labelled('Click me'), status=403)

    



