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


from reahl.tofu import Fixture, scenario, uses
from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import EmptyStub

from reahl.browsertools.browsertools import WidgetTester, Browser, XPath

from reahl.component.modelinterface import Action, Allowed, Event, Field, ExposedNames
from reahl.web.fw import Widget, UserInterface
from reahl.web.ui import Div, P, HTML5Page
from reahl.web.ui import Form, TextInput, ButtonInput

from reahl.web_dev.fixtures import WebFixture, BasicPageLayout


@with_fixtures(WebFixture)
def test_security_sensitive(web_fixture):
    """A Widget is security sensitive if a read_check is specified for it; one of its
       children is security sensitive, or it was explixitly marked as security sensitive."""
    fixture = web_fixture

    widget = Widget(fixture.view)

    # Case: marked explicitly
    assert not widget.is_security_sensitive
    widget.set_as_security_sensitive()
    assert widget.is_security_sensitive

    # Case: derived from children
    parent_widget = Widget(fixture.view)
    parent_widget.add_child(widget)
    assert widget.is_security_sensitive

    # Case: derived from read rights
    def allow(self): return True
    widget_with_rights = Widget(fixture.view, read_check=allow)
    assert widget.is_security_sensitive


@with_fixtures(WebFixture)
def test_serving_security_sensitive_widgets(web_fixture):
    """If the page is security sensitive, it will only be served on config.web.encrypted_http_scheme,
       else it will only be served on config.web.default_http_scheme."""
    class TestPanel(Div):
        def __init__(self, view):
            super().__init__(view)
            widget = self.add_child(Widget(view))

            if fixture.security_sensitive:
                widget.set_as_security_sensitive()

    fixture = web_fixture

    wsgi_app = web_fixture.new_wsgi_app(child_factory=TestPanel.factory(), enable_js=True)
    fixture.reahl_server.set_app(wsgi_app)

    config = web_fixture.config
    assert config.web.encrypted_http_scheme == 'https'
    assert config.web.default_http_scheme == 'http'

    fixture.security_sensitive = False
    fixture.driver_browser.open('https://localhost:8363/')
    assert fixture.driver_browser.current_url.scheme == config.web.default_http_scheme

    fixture.security_sensitive = True
    fixture.driver_browser.open('http://localhost:8000/')
    assert fixture.driver_browser.current_url.scheme == config.web.encrypted_http_scheme


@with_fixtures(WebFixture)
def test_fields_have_access_rights(web_fixture):
    """Fields have access rights for reading and for writing. By default both reading and writing are allowed.
       This default can be changed by passing an Action (which returns a boolean) for each kind of
       access which will be called to determine whether that kind of access is allowed.
       """
    fixture = web_fixture

    def not_allowed(): return False

    # Case: the default
    field = Field()
    assert field.can_read()
    assert field.can_write()

    # Case: tailored rights
    field = Field(readable=Action(not_allowed), writable=Action(not_allowed))
    field.bind('field_name', fixture)
    assert not field.can_read()
    assert not field.can_write()


@with_fixtures(WebFixture)
def test_tailored_access_make_inputs_security_sensitive(web_fixture):
    """An Input is sensitive if explicitly set as sensitive, or if its Fields has non-defaulted
       mechanisms for determiing access rights."""


    form = Form(web_fixture.view, 'some_form')
    field = Field(default=3, readable=Allowed(True))
    field.bind('field_name', EmptyStub())
    input_widget = TextInput(form, field)

    assert input_widget.is_security_sensitive


@uses(web_fixture=WebFixture)
class InputRenderingScenarios(Fixture):

    def new_form(self):
        return Form(self.web_fixture.view, 'some_form')

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

        self.expected_html = '<input name="some_form-field_name" id="id-some_form-field_name" form="some_form" type="text" value="3" class="reahl-primitiveinput reahl-textinput">'

    @scenario
    def disabled_rendering(self):
        self.readable = Allowed(True)
        self.writable = Allowed(False)
        self.input_widget = TextInput(self.form, self.field)

        self.expected_html = '<input name="some_form-field_name" id="id-some_form-field_name" disabled="disabled" form="some_form" type="text" value="3" class="reahl-primitiveinput reahl-textinput">'

    @scenario
    def valueless_rendering(self):
        self.readable = Allowed(False)
        self.writable = Allowed(True)
        self.input_widget = TextInput(self.form, self.field)

        self.expected_html = '<input name="some_form-field_name" id="id-some_form-field_name" form="some_form" type="text" value="" class="reahl-primitiveinput reahl-textinput">'

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

        self.expected_html = '<input name="event.some_form-event_name?" id="id-event-46-some_form-event_name-63-" form="some_form" type="submit" value="event_name" class="reahl-primitiveinput">'

    @scenario
    def greyed_button_rendering(self):
        self.readable = Allowed(True)
        self.writable = Allowed(False)
        self.input_widget = ButtonInput(self.form, self.event)

        self.expected_html = '<input name="event.some_form-event_name?" id="id-event-46-some_form-event_name-63-" disabled="disabled" form="some_form" type="submit" value="event_name" class="reahl-primitiveinput">'

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
        self.input_widget = Widget(self.web_fixture.view, read_check=self.disallowed)
        self.input_widget.add_child(P(self.web_fixture.view, text='some text in a p'))

        self.expected_html = ''

    @scenario
    def readable_but_not_writable_widget(self):
        self.input_widget = Widget(self.web_fixture.view, read_check=self.allowed, write_check=self.disallowed)
        self.input_widget.add_child(P(self.web_fixture.view, text='some text in a p'))

        self.expected_html = '<p>some text in a p</p>'

    @scenario
    def readable_and_writable_widget(self):
        self.input_widget = Widget(self.web_fixture.view, read_check=self.allowed, write_check=self.allowed)
        self.input_widget.add_child(P(self.web_fixture.view, text='some text in a p'))

        self.expected_html = '<p>some text in a p</p>'

    @scenario
    def not_readable_but_writable_widget(self):
        # Think of password field, where the input's value is not readable by a human
        self.input_widget = Widget(self.web_fixture.view, read_check=self.disallowed, write_check=self.allowed)
        self.input_widget.add_child(P(self.web_fixture.view, text='some text in a p'))

        self.expected_html = ''


@with_fixtures(WebFixture, InputRenderingScenarios)
def test_rendering_inputs(web_fixture, input_rendering_scenarios):
    """How Inputs render, depending on the rights."""

    fixture = input_rendering_scenarios

    tester = WidgetTester(fixture.input_widget)

    actual = tester.render_html()
    assert actual == fixture.expected_html


@with_fixtures(WebFixture)
def test_non_writable_input_is_dealt_with_like_invalid_input(web_fixture):
    """If a form submits a value for an Input that is linked to Field with access rights that prohibit writing,
       the input is silently ignored."""
    fixture = web_fixture

    class ModelObject:
        field_name = 'Original value'
        events = ExposedNames()
        events.an_event = lambda i: Event(label='click me')

        fields = ExposedNames()
        fields.field_name = lambda i: Field(default='abc', writable=Allowed(False), disallowed_message='you are not allowed to write this')
        
    model_object = ModelObject()

    class TestPanel(Div):
        def __init__(self, view):
            super().__init__(view)
            form = self.add_child(Form(view, 'some_form'))
            form.define_event_handler(model_object.events.an_event)
            form.add_child(ButtonInput(form, model_object.events.an_event))
            form.add_child(TextInput(form, model_object.fields.field_name))

            fixture.form = form


    wsgi_app = web_fixture.new_wsgi_app(child_factory=TestPanel.factory())
    browser = Browser(wsgi_app)
    browser.open('/')

    csrf_token = browser.get_value('//input[@name="some_form-_reahl_csrf_token"]')
    browser.post(fixture.form.event_channel.get_url().path, {'event.some_form-an_event?':'', 'some_form-field_name': 'illigitimate value', 'some_form-_reahl_database_concurrency_digest':'', 'some_form-_reahl_csrf_token': csrf_token})
    browser.follow_response()
    assert model_object.field_name == 'Original value'


@with_fixtures(WebFixture)
def test_non_writable_events_are_dealt_with_like_invalid_input(web_fixture):
    """If a form submits an Event with access rights that prohibit writing, a ValidationException is raised."""
    fixture = web_fixture

    class ModelObject:
        events = ExposedNames()
        events.an_event = lambda i: Event(label='click me', writable=Allowed(False),
                                          disallowed_message='you cannot do this')

    model_object = ModelObject()
    class TestPanel(Div):
        def __init__(self, view):
            super().__init__(view)
            form = self.add_child(Form(view, 'some_form'))
            form.define_event_handler(model_object.events.an_event)
            button = form.add_child(ButtonInput(form, model_object.events.an_event))
            if button.validation_error:
                form.add_child(form.create_error_label(button))
            fixture.form = form


    wsgi_app = web_fixture.new_wsgi_app(child_factory=TestPanel.factory())
    browser = Browser(wsgi_app)
    browser.open('/')

    csrf_token = browser.get_value('//input[@name="some_form-_reahl_csrf_token"]')
    browser.post(fixture.form.event_channel.get_url().path, {'event.some_form-an_event?':'', 'some_form-_reahl_database_concurrency_digest':'', 'some_form-_reahl_csrf_token': csrf_token})
    browser.follow_response()
    error_label = browser.get_html_for('//label')
    input_id = browser.get_id_of('//input[@name="event.some_form-an_event?"]')
    assert error_label == '<label for="%s" class="error">you cannot do this</label>' % input_id


@with_fixtures(WebFixture)
def test_getting_view(web_fixture):
    """ONLY If a View is readable, it can be GET"""
    fixture = web_fixture

    def disallowed(): return False

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page)
            self.define_view('/view', 'Title', read_check=disallowed)


    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)
    browser.open('/view', status=403)


@with_fixtures(WebFixture)
def test_posting_to_view(web_fixture):
    """ONLY If a View is writable, may it be POSTed to"""
    def disallowed(): return False

    class MyForm(Form):
        def __init__(self, view):
            super().__init__(view, 'myform')
            self.define_event_handler(self.events.an_event)
            self.add_child(ButtonInput(self, self.events.an_event))
        events = ExposedNames()
        events.an_event = lambda i: Event(label='Click me')

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            home = self.define_view('/a_view', 'Title', write_check=disallowed)
            home.set_slot('main', MyForm.factory())


    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    browser.open('/a_view')
    browser.click(XPath.button_labelled('Click me'), status=403)
