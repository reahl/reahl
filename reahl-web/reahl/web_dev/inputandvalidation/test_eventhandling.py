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


import json
import re

from webob import Request
from sqlalchemy import Column, Integer

from reahl.tofu import Fixture, scenario, NoException, expected, uses
from reahl.tofu.pytestsupport import with_fixtures
from reahl.stubble import EmptyStub

from reahl.browsertools.browsertools import WidgetTester, XPath, Browser

from reahl.component.exceptions import DomainException, ProgrammerError, IsInstance
from reahl.component.modelinterface import IntegerField, EmailField, DateField, \
    ExposedNames, Field, Event, Action, MultiChoiceField, Choice
from reahl.webdeclarative.webdeclarative import PersistedException, UserInput

from reahl.sqlalchemysupport import Base, Session
from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture
from reahl.web.fw import Url, UserInterface, ValidationException
from reahl.web.ui import HTML5Page, Div, Form, TextInput, ButtonInput, NestedForm, SelectInput, P

from reahl.dev.fixtures import ReahlSystemFixture
from reahl.web_dev.fixtures import WebFixture, BasicPageLayout


@with_fixtures(WebFixture)
def test_basic_event_linkup(web_fixture):
    """When a user clicks on a Button, the Event to which the Button is linked is triggered on
       the server, and its corresponding action is executed. After this, the
       browser is transitioned to the target view as specified by the EventHandler.
    """
    fixture = web_fixture

    class ModelObject:
        handled_event = False
        def handle_event(self):
            self.handled_event = True

        events = ExposedNames()
        events.an_event = lambda i: Event(label='click me', action=Action(i.handle_event))

    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name, other_view):
            super().__init__(view, name)
            self.define_event_handler(model_object.events.an_event, target=other_view)
            self.add_child(ButtonInput(self, model_object.events.an_event))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            home = self.define_view('/', title='Home page')
            other_view = self.define_view('/page2', title='Page 2')
            home.set_slot('main', MyForm.factory('myform', other_view))

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    fixture.reahl_server.set_app(wsgi_app)
    fixture.driver_browser.open('/')

    # clicking on the button triggers the action of the event handler
    assert not model_object.handled_event
    fixture.driver_browser.click("//input[@value='click me']")
    assert model_object.handled_event

    # browser has been transitioned to target view
    assert fixture.driver_browser.current_url.path == '/page2'


@with_fixtures(WebFixture)
def test_button_submits_only_once(web_fixture):
    """ButtonInputs and associated forms are blocked upon successful submit to prevent a user from double-clicking a button."""

    fixture = web_fixture
    fixture.click_count = 0
    class MyForm(Form):
        def __init__(self, view):
            super().__init__(view, 'myform')
            self.set_attribute('target', '_blank')  # We want to make sure the initial page is not refreshed so we can check the button status
            self.define_event_handler(self.events.an_event)
            self.add_child(TextInput(self, self.fields.field_name))
            self.add_child(ButtonInput(self, self.events.an_event))

        def clicked(self):
            fixture.click_count += 1

        events = ExposedNames()
        events.an_event = lambda i: Event(label='click me', action=Action(i.clicked))

        fields = ExposedNames()
        fields.field_name = lambda i: IntegerField()

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=MyForm.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    button_xpath = "//input[@value='click me']"

    assert fixture.click_count == 0
    assert browser.is_on_top(button_xpath)
    assert not browser.does_element_have_attribute(button_xpath, 'readonly')

    # case : if there is a validation error, don't block
    fixture.driver_browser.type("//input[@type='text']", 'not a number', trigger_blur=False, wait_for_ajax=False)
    browser.press_tab() #trigger validation exception
    with browser.no_page_load_expected():
        browser.click(button_xpath)

    assert fixture.click_count == 0
    assert browser.is_on_top(button_xpath)
    assert not browser.does_element_have_attribute(button_xpath, 'readonly')

    # case : if the form is valid, do block
    fixture.driver_browser.type("//input[@type='text']", '1', trigger_blur=False, wait_for_ajax=False)
    browser.press_tab() #trigger validation
    with browser.new_tab_closed():
        browser.click(button_xpath)

    assert fixture.click_count == 1                   # The Event was submitted
    assert not browser.is_on_top(button_xpath)        # The Button cannot be clicked again
    assert browser.does_element_have_attribute(button_xpath, 'readonly')


@with_fixtures(WebFixture)
def test_arguments_to_actions(web_fixture):
    """If a Button is created for an Event with_arguments, those arguments are passed to the backend
       when the Button is clicked."""

    fixture = web_fixture

    # how you link everything up in code
    class ModelObject:
        def handle_event(self, *args):
            self.args = args

        events = ExposedNames()
        events.an_event = lambda i: Event(label='click me',
                                          action=Action(i.handle_event, ['one_argument', 'another_argument']),
                                          one_argument=IntegerField(),
                                          another_argument=Field())

    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name):
            super().__init__(view, name)
            self.add_child(ButtonInput(self, model_object.events.an_event.with_arguments(one_argument=1, another_argument='another')))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            home = self.define_view('/', title='Home page')
            other_view = self.define_view('/page2', title='Page 2')
            home.set_slot('main', MyForm.factory('myform'))
            self.define_transition(model_object.events.an_event, home, other_view)

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    fixture.reahl_server.set_app(wsgi_app)
    fixture.driver_browser.open('/')

    # when the Action is executed, the correct arguments are passed
    fixture.driver_browser.click("//input[@value='click me']")
    assert model_object.args == (1, 'another')


@with_fixtures(WebFixture)
def test_validation_of_event_arguments(web_fixture):
    """Buttons cannot be created for Events with invalid default arguments."""

    fixture = web_fixture

    class ModelObject:
        events = ExposedNames()
        events.an_event = lambda i: Event(label='Click me', argument=Field(required=True))

    model_object = ModelObject()

    form = Form(fixture.view, 'test')
    form.define_event_handler(model_object.events.an_event)

    with expected(ProgrammerError):
        ButtonInput(form, model_object.events.an_event)

    with expected(NoException):
        ButtonInput(form, model_object.events.an_event.with_arguments(argument='something'))


@with_fixtures(WebFixture)
def test_basic_field_linkup(web_fixture):
    """When a form is rendered, the Inputs on it display either the default value as specified
       by the Field with which the Input is associated, or (if set) the value of the attribute
       that Field is bound to.

       When a user clicks on a Button, the Input value is set via the Field on the
       model objects to which the Field is bound. This happens before the associated action
       is executed.
    """

    fixture = web_fixture

    class ModelObject:
        def handle_event(self):
            pass

        events = ExposedNames()
        events.an_event = lambda i: Event(label='click me', action=Action(i.handle_event))

        fields = ExposedNames()
        fields.field_name = lambda i: IntegerField(default=3)

    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name):
            super().__init__(view, name)
            self.define_event_handler(model_object.events.an_event)
            self.add_child(ButtonInput(self, model_object.events.an_event))
            self.add_child(TextInput(self, model_object.fields.field_name))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            home = self.define_view('/', title='Home page')
            home.set_slot('main', MyForm.factory('myform'))

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    fixture.reahl_server.set_app(wsgi_app)
    fixture.driver_browser.open('/')

    # the initial value rendered in the input
    assert not hasattr(model_object, 'field_name')
    initial_value = fixture.driver_browser.get_value("//input[@type='text']")
    assert initial_value == '3'

    # the user supplied value is marshalled and set on the model object when an event happens
    fixture.driver_browser.type("//input[@type='text']", '5')
    fixture.driver_browser.click("//input[@value='click me']")
    assert model_object.field_name == 5


@with_fixtures(WebFixture)
def test_distinguishing_identical_field_names(web_fixture):
    """A programmer can add different Inputs on the same Form even if their respective Fields are bound
       to identically named attributes of different objects by specifying a name_discriminator that is
       different for different inputs."""

    fixture = web_fixture

    class ModelObject:
        fields = ExposedNames()
        fields.field_name = lambda i: IntegerField()

    model_object1 = ModelObject()
    model_object2 = ModelObject()

    class MyForm(Form):
        events = ExposedNames()
        events.an_event = lambda i: Event(label='click me')

        def __init__(self, view, name):
            super().__init__(view, name)
            self.define_event_handler(self.events.an_event)
            self.add_child(ButtonInput(self, self.events.an_event))

            self.add_child(TextInput(self, model_object1.fields.field_name))
            self.add_child(TextInput(self, model_object2.fields.field_name.with_discriminator('object2')))

    wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory('form'))
    fixture.reahl_server.set_app(wsgi_app)
    fixture.driver_browser.open('/')

    # the correct input value gets to the correct object despite referencing identically named attributes
    fixture.driver_browser.type('//input[@type="text"][1]', '0')
    fixture.driver_browser.type('//input[@type="text"][2]', '1')
    fixture.driver_browser.click(XPath.button_labelled('click me'))
    assert model_object1.field_name == 0
    assert model_object2.field_name == 1


@with_fixtures(WebFixture)
def test_wrong_arguments_to_define_event_handler(web_fixture):
    """Passing anything other than an Event to define_event_handler is an error."""

    fixture = web_fixture

    class MyForm(Form):
        def __init__(self, view, name):
            super().__init__(view, name)
            self.define_event_handler(EmptyStub())

    wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory('form'))
    browser = Browser(wsgi_app)

    with expected(IsInstance):
        browser.open('/')


@with_fixtures(WebFixture)
def test_define_event_handler_not_called(web_fixture):
    """."""
    fixture = web_fixture

    class ModelObject:
        events = ExposedNames()
        events.an_event = lambda i: Event()

    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name):
            super().__init__(view, name)
            self.add_child(ButtonInput(self, model_object.events.an_event))

    wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory('form'))
    browser = Browser(wsgi_app)

    with expected(ProgrammerError, test='no Event/Transition available for name an_event'):
        browser.open('/')


@with_fixtures(ReahlSystemFixture, WebFixture, SqlAlchemyFixture)
def test_exception_handling(reahl_system_fixture, web_fixture, sql_alchemy_fixture):
    """When a DomainException happens during the handling of an Event:

       The database is rolled back.
       The browser is redirected to GET the original view again (not the target).
       The screen still displays the values the user initially typed, not those on the ModelObject.
    """

    fixture = web_fixture

    class ModelObject(Base):
        __tablename__ = 'test_event_handling_exception_handling'
        id = Column(Integer, primary_key=True)
        field_name = Column(Integer)
        def handle_event(self):
            self.field_name = 1
            raise DomainException()
        events = ExposedNames()
        events.an_event = lambda i: Event(label='click me', action=Action(i.handle_event))
        fields = ExposedNames()
        fields.field_name = lambda i: IntegerField(default=3)

    with sql_alchemy_fixture.persistent_test_classes(ModelObject):
        model_object = ModelObject()
        Session.add(model_object)

        class MyForm(Form):
            def __init__(self, view, name, other_view):
                super().__init__(view, name)
                self.define_event_handler(model_object.events.an_event, target=other_view)
                self.add_child(ButtonInput(self, model_object.events.an_event))
                self.add_child(TextInput(self, model_object.fields.field_name))

        class MainUI(UserInterface):
            def assemble(self):
                self.define_page(HTML5Page).use_layout(BasicPageLayout())
                home = self.define_view('/', title='Home page')
                other_view = self.define_view('/page2', title='Page 2')
                home.set_slot('main', MyForm.factory('myform', other_view))

        wsgi_app = fixture.new_wsgi_app(site_root=MainUI)

        browser = Browser(wsgi_app)  # Dont use a real browser, because it will also hit many other URLs for js and css which confuse the issue
        browser.open('/')

        assert not model_object.field_name
        browser.type("//input[@type='text']", '5')

        # any database stuff that happened when the form was submitted was rolled back
#        with CallMonitor(reahl_system_fixture.system_control.orm_control.rollback) as monitor:
#            browser.click(XPath.button_labelled('click me'))
#        assert monitor.times_called == 1
        browser.click(XPath.button_labelled('click me'))

        # the value input by the user is still displayed on the form, NOT the actual value on the model object
        assert not model_object.field_name
        retained_value = browser.get_value("//input[@type='text']")
        assert retained_value == '5'

        # the browser is still on the page with the form which triggered the exception
        assert browser.current_url.path == '/'


@with_fixtures(WebFixture)
def test_form_preserves_user_input_after_validation_exceptions_multichoice(web_fixture):
    """When a form is submitted and validation fails on the server, the user
     is presented with the values that were originally entered (even if they were invalid)."""

    fixture = web_fixture

    class ModelObject:
        events = ExposedNames()
        events.an_event = lambda i: Event(label='click me')
            
        choices = [Choice(1, IntegerField(label='One')),
                   Choice(2, IntegerField(label='Two')),
                   Choice(3, IntegerField(label='Three'))]
        fields = ExposedNames()
        fields.no_validation_exception_field = lambda i: MultiChoiceField(i.choices, label='Make your invalid choice', default=[])
        fields.validation_exception_field = lambda i: MultiChoiceField(i.choices, label='Make your choice', default=[], required=True)

    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view):
            super().__init__(view, 'my_form')
            self.define_event_handler(model_object.events.an_event)
            self.add_child(ButtonInput(self, model_object.events.an_event))
            select_input = self.add_child(SelectInput(self, model_object.fields.no_validation_exception_field))
            if select_input.validation_error:
                self.add_child(self.create_error_label(select_input))
            select_input = self.add_child(SelectInput(self, model_object.fields.validation_exception_field))
            if select_input.validation_error:
                self.add_child(self.create_error_label(select_input))

    wsgi_app = web_fixture.new_wsgi_app(child_factory=MyForm.factory())
    browser = Browser(wsgi_app)

    browser.open('/')

    no_validation_exception_input = '//select[@name="my_form-no_validation_exception_field[]"]'
    validation_exception_input = '//select[@name="my_form-validation_exception_field[]"]'

    browser.select_many(no_validation_exception_input, ['One', 'Two'])
    browser.select_none(validation_exception_input) # select none to trigger the RequiredConstraint
    browser.click(XPath.button_labelled('click me'))

    assert browser.get_value(no_validation_exception_input) == ['1', '2']
    assert not browser.get_value(validation_exception_input)

    label = browser.get_html_for('//label')
    input_id = browser.get_id_of(validation_exception_input)
    assert label == '<label for="%s" class="error">Make your choice is required</label>' % input_id

    #2. Submit again ths time not expecting validation exceptions, also expecting the validation error to be cleared and the domain should have all input
    browser.select_many(validation_exception_input, ['Two', 'Three'])
    browser.click(XPath.button_labelled('click me'))

    assert not browser.is_element_present('//label[@class="error"]')
    assert browser.get_value(no_validation_exception_input) == ['1', '2']
    assert browser.get_value(validation_exception_input) == ['2', '3']


@with_fixtures(WebFixture)
def test_rendering_of_form(web_fixture):
    """A Form is always set up to POST to its EventChannel url.  The current page's query string is
       propagated with the POST url if any.  The Form has an id and class to help style it etc."""

    fixture = web_fixture

    form = Form(fixture.view, 'test_channel')
    tester = WidgetTester(form)

    fixture.context.request = Request.blank('/a/b?x=y', charset='utf8')
    actual = tester.render_html()

    expected = '''<form id="test_channel" action="/a/b/_test_channel_method\?x=y" data-formatter="/__test_channel_format_method" method="POST" class="reahl-form">''' \
               '''<div id="test_channel_hashes">'''\
               '''<input name="test_channel-_reahl_csrf_token" id="id-test_channel-_reahl_csrf_token" form="test_channel" type="hidden" value=".*" class="reahl-primitiveinput">''' \
               '''<input name="test_channel-_reahl_database_concurrency_digest" id="id-test_channel-_reahl_database_concurrency_digest" form="test_channel" type="hidden" value="" class="reahl-primitiveinput">''' \
               '''</div>''' \
               '''</form>'''
    assert re.match(expected, actual)

    # Case: without querystring
    fixture.context.request = Request.blank('/a/b', charset='utf8')
    actual = tester.render_html_tree()

    action = actual.xpath('//form')[0].attrib['action']
    assert action == '/a/b/_test_channel_method'


@with_fixtures(WebFixture)
def test_duplicate_forms(web_fixture):
    """It is an error to add more than one form with the same unique_name to a page."""

    fixture = web_fixture

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout(slots=['main', 'secondary']))
            home = self.define_view('/', title='Home page')
            home.set_slot('main', Form.factory('myform'))
            home.set_slot('secondary', Form.factory('myform'))

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    with expected(ProgrammerError, test='More than one form was added using the same unique_name.*'):
        browser.open('/')


@with_fixtures(WebFixture)
def test_check_missing_form(web_fixture):
    """All forms referred to by inputs on a page have to be present on that page."""

    fixture = web_fixture

    class ModelObject:
        fields = ExposedNames()
        fields.name = lambda i: Field()

    class MyPanel(Div):
        def __init__(self, view):
            super().__init__(view)
            model_object = ModelObject()
            forgotten_form = Form(view, 'myform')
            self.add_child(TextInput(forgotten_form, model_object.fields.name))

    wsgi_app = fixture.new_wsgi_app(child_factory=MyPanel.factory())
    browser = Browser(wsgi_app)

    expected_message = 'Could not find form for <TextInput name=myform-name>. '\
                       'Its form, <Form form id="myform".*> is not present on the current page'

    with expected(ProgrammerError, test=expected_message):
        browser.open('/')


@with_fixtures(WebFixture)
def test_nested_forms(web_fixture):
    """HTML disallows nesting of forms. A NestedForm can be used to simulate
       a form which is visually part of another Form. A NestedForm provides a
       form attribute which should be used when creating an Inputs for it.
    """

    fixture = web_fixture

    class NestedModelObject:
        handled_event = False
        def handle_event(self):
            self.handled_event = True
        events = ExposedNames()
        events.nested_event = lambda i: Event(label='click nested', action=Action(i.handle_event))
        fields = ExposedNames()
        fields.nested_field = lambda i: Field(label='input nested')

    nested_model_object = NestedModelObject()
    class MyNestedForm(NestedForm):
        def __init__(self, view, name):
            super().__init__(view, name)
            self.define_event_handler(nested_model_object.events.nested_event)
            self.add_child(ButtonInput(self.form, nested_model_object.events.nested_event))
            self.add_child(TextInput(self.form, nested_model_object.fields.nested_field))

    class OuterModelObject:
        handled_event = False
        def handle_event(self):
            self.handled_event = True
        events = ExposedNames()
        events.outer_event = lambda i: Event(label='click outer', action=Action(i.handle_event))
    outer_model_object = OuterModelObject()
    class OuterForm(Form):
        def __init__(self, view, name):
            super().__init__(view, name)
            self.add_child(MyNestedForm(view, 'my_nested_form'))
            self.define_event_handler(outer_model_object.events.outer_event)
            self.add_child(ButtonInput(self, outer_model_object.events.outer_event))

    wsgi_app = fixture.new_wsgi_app(child_factory=OuterForm.factory('outer_form'))
    fixture.reahl_server.set_app(wsgi_app)
    browser = fixture.driver_browser

    browser.open('/')
    browser.type(XPath.input_named('my_nested_form-nested_field'), 'some nested input')

    browser.click(XPath.button_labelled('click nested'))

    assert nested_model_object.handled_event
    assert not outer_model_object.handled_event

    assert nested_model_object.nested_field == 'some nested input'


@with_fixtures(WebFixture)
def test_form_input_validation(web_fixture):
    """Validation of input happens in JS on the client, but also on the server if JS is bypassed."""

    error_xpath = '//form[contains(@class, "reahl-form")]/label[contains(@class, "error")]'

    fixture = web_fixture

    class ModelObject:
        def handle_event(self):
            pass
        events = ExposedNames()
        events.an_event = lambda i: Event(label='click me', action=Action(i.handle_event))
        fields = ExposedNames()
        fields.field_name = lambda i: EmailField()

    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name, other_view):
            super().__init__(view, name)
            if self.exception:
                 self.add_child(P(view, ','.join(self.exception.detail_messages)))
            self.define_event_handler(model_object.events.an_event, target=other_view)
            self.add_child(ButtonInput(self, model_object.events.an_event))
            text_input = self.add_child(TextInput(self, model_object.fields.field_name))
            if text_input.validation_error:
                self.add_child(self.create_error_label(text_input))


    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            home = self.define_view('/', title='Home page')
            other_view = self.define_view('/page2', title='Page 2')
            home.set_slot('main', MyForm.factory('myform', other_view))

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI, enable_js=True)

    # Case: form validation fails in JS on the client
    #  - Form submission is blocked
    #  - Error message is displayed
    fixture.reahl_server.set_app(wsgi_app)
    fixture.driver_browser.open('/')
    fixture.driver_browser.wait_for_element_not_visible(error_xpath)
    fixture.driver_browser.type('//input[@type="text"]', 'not@notvalid', trigger_blur=False, wait_for_ajax=False)
    fixture.driver_browser.press_tab()
    fixture.driver_browser.wait_for_element_visible(error_xpath)

    with fixture.driver_browser.no_page_load_expected():
        fixture.driver_browser.click("//input[@value='click me']")

    error_text = fixture.driver_browser.get_text(error_xpath)
    assert error_text == 'field_name should be a valid email address'

    # .. but the error is removed again upon valid input
    fixture.driver_browser.type('//input[@type="text"]', 'valid@home.org')
    fixture.driver_browser.wait_for_element_not_visible(error_xpath)

    # Case: form validation fails on the server (assuming no JS on the client to block submission)
    #  - ValidationException is raised (which is dealt with as any DomainException)
    browser = Browser(wsgi_app)
    browser.open('/')
    browser.type('//input[@type="text"]', 'not@notvalid')

    browser.click('//input[@type="submit"]')
    assert not hasattr(model_object, 'field_name')
    label = browser.get_html_for('//label')
    input_id = browser.get_id_of('//input[@type="text"]')
    assert label == '<label for="%s" class="error">field_name should be a valid email address</label>' % input_id

    assert Session.query(UserInput).filter_by(key='myform-field_name').count() == 1  # The invalid input was persisted
    exception = Session.query(PersistedException).one().exception
    assert isinstance(exception, ValidationException)  # Is was persisted
    assert not exception.commit

    # Case: form validation passes (no-js)
    #  - no ValidationException
    #  - all input is translated to python and set as values on the model objects
    #  - any saved input on the form is cleared
    browser.type('//input[@type="text"]', 'valid@home.org')
    browser.click("//input[@value='click me']")
    assert model_object.field_name == 'valid@home.org'

    assert Session.query(UserInput).filter_by(key='myform-field_name').count() == 0  # The invalid input was removed
    assert Session.query(PersistedException).count() == 0  # The exception was removed

    assert browser.current_url.path == '/page2'

    # Case: form validation passes (js)
    #  - no ValidationException
    #  - all input is translated to python and set as values on the model objects
    fixture.driver_browser.open('/')
    fixture.driver_browser.type('//input[@type="text"]', 'valid@home.org')
    fixture.driver_browser.wait_for_element_not_visible(error_xpath)
    fixture.driver_browser.click("//input[@value='click me']")
    assert model_object.field_name == 'valid@home.org'

    assert fixture.driver_browser.current_url.path == '/page2'


@uses(web_fixture=WebFixture)
class QueryStringScenarios(Fixture):
    def new_other_view(self):
        return self.web_fixture.wsgi_app.define_view('/page2', title='Page 2')

    def new_form(self):
        form = Form(self.web_fixture.view, 'some_form')
        event = Event(label='click me', action=Action(i.action))
        event.bind('an_event', None)
        form.define_event_handler(event, target=self.target)
        form.add_child(ButtonInput(form, event))
        return form

    @property
    def query_string_on_form_submit(self):
        form_action = self.web_fixture.driver_browser.get_attribute('//form', 'action')
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
        self.target = self.web_fixture.view.as_factory()
        self.initial_qs = 'a=b'
        self.final_qs = 'a=b'

    @scenario
    def same_target_by_exception(self):
        self.break_on_submit = True
        self.target_is_other_view = True
        self.initial_qs = 'a=b'
        self.final_qs = 'a=b'


@with_fixtures(WebFixture, QueryStringScenarios)
def test_propagation_of_querystring(web_fixture, query_string_scenarios):
    """The query string of the original View visited is maintained through the GET/POST cycle.
       If, for whatever reason (exception or intent) the browser should stay on the same
       View after POSTing, the query string is maintained to that point.
       Else, the query string is cleared.
    """
    fixture = query_string_scenarios

    class ModelObject:
        def handle_event(self):
            if fixture.break_on_submit:
                raise DomainException()
        events = ExposedNames()
        events.an_event = lambda i: Event(label='click me', action=Action(i.handle_event))

    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name, other_view):
            super().__init__(view, name)
            if fixture.target_is_other_view:
                target = other_view
            else:
                target = view.as_factory()
            self.define_event_handler(model_object.events.an_event, target=target)
            self.add_child(ButtonInput(self, model_object.events.an_event))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            home = self.define_view('/', title='Home page')
            other_view = self.define_view('/page2', title='Page 2')
            home.set_slot('main', MyForm.factory('myform', other_view))

    wsgi_app = web_fixture.new_wsgi_app(site_root=MainUI, enable_js=True)
    web_fixture.reahl_server.set_app(wsgi_app)
    web_fixture.driver_browser.open('/?%s' % fixture.initial_qs)

    assert fixture.query_string_on_form_submit == fixture.initial_qs
    web_fixture.driver_browser.click("//input[@value='click me']")
    assert web_fixture.driver_browser.current_url.query == fixture.final_qs


@with_fixtures(WebFixture)
def test_event_names_are_canonicalised(web_fixture):
    """The name= attribute of a button is an url encoded string. There is more than one way
       to url encode the same string. The server ensures that different encodings of the same
       string are not mistaken for different names.
    """

    fixture = web_fixture

    class ModelObject:
        def handle_event(self, some_argument):
            self.received_argument = some_argument

        events = ExposedNames()
        events.an_event = lambda i: Event(label='click me',
                                          action=Action(i.handle_event, ['some_argument']),
                                          some_argument=Field(default='default value'))

    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name):
            super().__init__(view, name)
            self.define_event_handler(model_object.events.an_event)
            self.add_child(ButtonInput(self, model_object.events.an_event.with_arguments(some_argument='f~nnystuff')))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            home = self.define_view('/', title='Home page')
            home.set_slot('main', MyForm.factory('myform'))

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    # when the Action is executed, the correct arguments are passed
    browser.open('/')
    csrf_token = browser.get_value('//input[@name="myform-_reahl_csrf_token"]')
    browser.post('/__myform_method', {'event.myform-an_event?some_argument=f~nnystuff': '', 'myform-_reahl_database_concurrency_digest':'', 'myform-_reahl_csrf_token': csrf_token})
    assert model_object.received_argument == 'f~nnystuff'


@with_fixtures(WebFixture)
def test_alternative_event_trigerring(web_fixture):
    """Events can also be triggered by submitting a Form via Ajax. In such cases the normal redirect-after-submit
       behaviour of the underlying EventChannel is not desirable. This behaviour can be switched off by submitting
       an extra argument along with the Form in order to request the alternative behaviour.
    """

    fixture = web_fixture

    class ModelObject:
        def handle_event(self):
            self.handled_event = True

        events = ExposedNames()
        events.an_event = lambda i: Event(label='click me',
                                    action=Action(i.handle_event))

    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name, other_view):
            super().__init__(view, name)
            self.define_event_handler(model_object.events.an_event, target=other_view)
            self.add_child(ButtonInput(self, model_object.events.an_event))

    class MainUI(UserInterface):
        def assemble(self):
            self.define_page(HTML5Page).use_layout(BasicPageLayout())
            home = self.define_view('/', title='Home page')
            other_view = self.define_view('/page2', title='Page 2')
            home.set_slot('main', MyForm.factory('myform', other_view))

    wsgi_app = fixture.new_wsgi_app(site_root=MainUI)
    browser = Browser(wsgi_app)

    # when POSTing with _noredirect, the Action is executed, but the browser is not redirected to /page2 as usual
    browser.open('/')
    csrf_token = browser.get_value('//input[@name="myform-_reahl_csrf_token"]')
    browser.post('/__myform_method', {'event.myform-an_event?': '', '_noredirect': '', 'myform-_reahl_database_concurrency_digest':'', 'myform-_reahl_csrf_token': csrf_token})
    browser.follow_response()  # Needed to make the test break should a HTTPTemporaryRedirect response be sent
    assert model_object.handled_event
    assert browser.current_url.path != '/page2'
    assert browser.current_url.path == '/__myform_method'

    # the response is a json object reporting the success of the event and a new rendition of the form
    json_dict = json.loads(browser.raw_html)
    assert json_dict['success']
    expected_html = '<div id="myform_hashes">'
    assert json_dict['result']['myform'].startswith(expected_html)


@with_fixtures(WebFixture)
def test_remote_field_validation(web_fixture):
    """A Form contains a RemoteMethod that can be used to validate any of its fields via HTTP.
    """

    fixture = web_fixture

    class ModelObject:
        fields = ExposedNames()
        fields.a_field = lambda i: EmailField()

    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name):
            super().__init__(view, name)
            self.add_child(TextInput(self, model_object.fields.a_field))

    wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory('myform'))
    browser = Browser(wsgi_app)
    browser.open('/')
    csrf_token_string = web_fixture.get_csrf_token_string(browser=browser)

    browser.open('/_myform_validate_method?myform-a_field=invalid email address', headers={'X-CSRF-TOKEN':csrf_token_string})
    assert browser.raw_html == '"a_field should be a valid email address"'

    browser.open('/_myform_validate_method?myform-a_field=valid@email.org', headers={'X-CSRF-TOKEN':csrf_token_string})
    assert browser.raw_html == 'true'


@with_fixtures(WebFixture)
def test_remote_field_formatting(web_fixture):
    """A Form contains a RemoteMethod that can be used to reformat any of its fields via HTTP.
    """

    fixture = web_fixture

    class ModelObject:
        fields = ExposedNames()
        fields.a_field = lambda i: DateField()

    model_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view, name):
            super().__init__(view, name)
            self.add_child(TextInput(self, model_object.fields.a_field))

    wsgi_app = fixture.new_wsgi_app(child_factory=MyForm.factory('myform'))
    browser = Browser(wsgi_app)
    browser.open('/')
    csrf_token_string = web_fixture.get_csrf_token_string(browser=browser)

    browser.open('/_myform_format_method?myform-a_field=13 November 2012', headers={'X-CSRF-TOKEN':csrf_token_string})
    assert browser.raw_html == '13 Nov 2012'

    browser.open('/_myform_format_method?myform-a_field=invaliddate', headers={'X-CSRF-TOKEN':csrf_token_string})
    assert browser.raw_html == ''


