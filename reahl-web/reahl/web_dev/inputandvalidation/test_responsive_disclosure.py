# Copyright 2018-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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



import threading

from sqlalchemy import Column, Integer

from reahl.tofu import Fixture, scenario, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.web_dev.fixtures import WebFixture
from reahl.browsertools.browsertools import XPath
from reahl.web.fw import Widget, Url
from reahl.web.ui import Form, Div, SelectInput, Label, P, RadioButtonSelectInput, CheckboxSelectInput, \
    CheckboxInput, ButtonInput, TextInput, FormLayout, A
from reahl.component.modelinterface import Field, BooleanField, MultiChoiceField, ChoiceField, Choice, ExposedNames, \
    IntegerField, EmailField, Event, Action, Allowed
from reahl.component.exceptions import DomainException
from reahl.web_dev.inputandvalidation.test_widgetqueryargs import QueryStringFixture
from reahl.sqlalchemysupport import Base, Session
from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture


@uses(web_fixture=WebFixture)
class ResponsiveDisclosureFixture(Fixture):

    def new_ModelObject(self):
        class ModelObject:
            def __init__(self):
                self.choice = 1

            fields = ExposedNames()
            fields.choice = lambda i: ChoiceField([Choice(1, IntegerField(label='One')),
                                                   Choice(2, IntegerField(label='Two')),
                                                   Choice(3, IntegerField(label='Three'))],
                                                  label='Choice')
        return ModelObject

    def new_MainWidget(self):
        fixture = self
        class MainWidget(Widget):
            def __init__(self, view):
                super().__init__(view)
                an_object = fixture.ModelObject()
                self.add_child(fixture.MyForm(view, an_object))

        return MainWidget

    def new_MyForm(self):
        fixture = self
        class MyForm(Form):
            def __init__(self, view, an_object):
                super().__init__(view, 'myform')
                self.enable_refresh()
                self.use_layout(FormLayout())
                self.layout.add_input(fixture.create_trigger_input(self, an_object))
                self.add_child(P(self.view, text='My state is now %s' % an_object.choice))

        return MyForm

    def create_trigger_input(self, form, an_object):
        return SelectInput(form, an_object.fields.choice, refresh_widget=form)



class ResponsiveWidgetScenarios(ResponsiveDisclosureFixture):
    @scenario
    def select_input(self):
        self.expected_focussed_element = XPath.select_labelled('Choice')
        def change_value(browser):
            browser.select(self.expected_focussed_element, 'Three')
        self.change_value = change_value
        self.initial_state = 1
        self.changed_state = 3

    @scenario
    def radio_buttons(self):
        def create_trigger_input(form, an_object):
            return RadioButtonSelectInput(form, an_object.fields.choice, refresh_widget=form)
        self.create_trigger_input = create_trigger_input

        self.expected_focussed_element = XPath.input_labelled('Three')
        def change_value(browser):
            browser.click(self.expected_focussed_element)
        self.change_value = change_value
        self.initial_state = 1
        self.changed_state = 3

    @scenario
    def single_valued_checkbox(self):
        class ModelObject:
            def __init__(self):
                self.choice = False
            fields = ExposedNames()
            fields.choice = lambda i: BooleanField(label=u'Choice',
                                                   true_value=u'true_value', false_value=u'false_value')
        self.ModelObject = ModelObject

        def create_trigger_input(form, an_object):
            the_input = CheckboxInput(form, an_object.fields.choice, refresh_widget=form)
            the_input.set_id('marvin')
            return the_input
        self.create_trigger_input = create_trigger_input

        self.expected_focussed_element = XPath.input_labelled('Choice')
        def change_value(browser):
            browser.click(self.expected_focussed_element)
        self.change_value = change_value
        self.initial_state = False
        self.changed_state = True

    @scenario
    def multi_valued_checkbox_select(self):
        class ModelObject:
            def __init__(self):
                self.choice = [1]

            fields = ExposedNames()
            fields.choice = lambda i: MultiChoiceField([Choice(1, IntegerField(label='One')),
                                                        Choice(2, IntegerField(label='Two')),
                                                        Choice(3, IntegerField(label='Three'))],
                                                       label='Choice')
        self.ModelObject = ModelObject

        def create_trigger_input(form, an_object):
            the_input = CheckboxSelectInput(form, an_object.fields.choice, refresh_widget=form)
            the_input.set_id('marvin')
            return the_input
        self.create_trigger_input = create_trigger_input

        self.expected_focussed_element = XPath.input_labelled('Three')
        def change_value(browser):
            browser.click(self.expected_focussed_element)
        self.change_value = change_value
        self.initial_state = [1]
        self.changed_state = [1, 3]

    @scenario
    def multi_valued_checkbox_select_with_single_choice_corner_case_empty_a_list(self):
        self.multi_valued_checkbox_select()
        class ModelObject:
            def __init__(self):
                self.choice = [1]

            fields = ExposedNames()
            fields.choice = lambda i: MultiChoiceField([Choice(1, IntegerField(label='One'))],
                                                       label='Choice')
        self.ModelObject = ModelObject

        self.expected_focussed_element = XPath.input_labelled('One')
        def change_value(browser):
            browser.click(self.expected_focussed_element)
        self.change_value = change_value
        self.initial_state = [1]
        self.changed_state = []

    @scenario
    def multi_valued_checkbox_select_with_single_choice_corner_case_add_to_empty_list(self):
        self.multi_valued_checkbox_select()
        class ModelObject:
            def __init__(self):
                self.choice = []

            fields = ExposedNames()
            fields.choice = lambda i: MultiChoiceField([Choice(1, IntegerField(label='One'))],
                                                       label='Choice')
        self.ModelObject = ModelObject
        #self.MyForm from multi_valued_checkbox_select

        self.expected_focussed_element = XPath.input_labelled('One')
        def change_value(browser):
            browser.click(self.expected_focussed_element)
        self.change_value = change_value
        self.initial_state = []
        self.changed_state = [1]

    @scenario
    def multi_valued_select(self):
        class ModelObject:
            def __init__(self):
                self.choice = [1]

            fields = ExposedNames()
            fields.choice = lambda i: MultiChoiceField([Choice(1, IntegerField(label='One')),
                                                        Choice(2, IntegerField(label='Two')),
                                                        Choice(3, IntegerField(label='Three'))],
                                                       label='Choice')
        self.ModelObject = ModelObject

        def create_trigger_input(form, an_object):
            the_input = SelectInput(form, an_object.fields.choice, refresh_widget=form)
            the_input.set_id('marvin')
            return the_input
        self.create_trigger_input = create_trigger_input

        self.expected_focussed_element = XPath.select_labelled('Choice')
        def change_value(browser):
            browser.select(self.expected_focussed_element, 'Three')
        self.change_value = change_value
        self.initial_state = [1]
        self.changed_state = [1, 3]


@with_fixtures(WebFixture, QueryStringFixture, ResponsiveWidgetScenarios)
def test_inputs_can_refresh_parent_widgets(web_fixture, query_string_fixture, responsive_widget_scenarios):
    """An Input can cause another Widget to be re-rendered if the input value changes."""

    fixture = responsive_widget_scenarios

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    assert browser.wait_for(query_string_fixture.is_state_now, fixture.initial_state)
    fixture.change_value(browser)
    assert browser.wait_for(query_string_fixture.is_state_now, fixture.changed_state)


@with_fixtures(WebFixture, QueryStringFixture, ResponsiveDisclosureFixture)
def test_refresh_input_can_be_set_after_input_is_created(web_fixture, query_string_fixture, responsive_disclosure_fixture):
    """`set_refresh_widgets` can be called after construction of the Input to instruct it to refresh a given list of Widgets."""
    fixture = responsive_disclosure_fixture

    class MyForm(Form):
        def __init__(self, view, an_object):
            super().__init__(view, 'myform')
            self.use_layout(FormLayout())
            trigger_input = self.layout.add_input(SelectInput(self, an_object.fields.choice))
            refreshed_widget = self.add_child(P(self.view, text='My state is now %s' % an_object.choice))
            refreshed_widget.set_id('refreshing-paragraph')
            refreshed_widget.enable_refresh()
            
            another_widget_to_refresh = self.add_child(P(self.view, text='Another widget state is now %s' % an_object.choice))
            another_widget_to_refresh.set_id('another-refreshing-paragraph')
            another_widget_to_refresh.enable_refresh()
            
            trigger_input.set_refresh_widgets([refreshed_widget, another_widget_to_refresh])

    fixture.MyForm = MyForm

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    assert browser.wait_for(query_string_fixture.is_state_now, 1)
    assert browser.wait_for(query_string_fixture.is_state_on_another_widget_now, 1)
    browser.select(XPath.select_labelled('Choice'), 'Three')
    assert browser.wait_for(query_string_fixture.is_state_now, 3)
    assert browser.wait_for(query_string_fixture.is_state_on_another_widget_now, 3)


@with_fixtures(WebFixture, QueryStringFixture, ResponsiveDisclosureFixture)
def test_refresh_widgets_with_widget_arguments(web_fixture, query_string_fixture, responsive_disclosure_fixture):
    """Widget arguemnts are taken into account when widgets are refreshed by an input"""
    fixture = responsive_disclosure_fixture

    class MyForm(Form):
        def __init__(self, view, an_object):
            self.arg = 'default'
            super().__init__(view, 'myform')
            self.enable_refresh()
            self.use_layout(FormLayout())
            trigger_input = self.layout.add_input(SelectInput(self, an_object.fields.choice))

            refreshed_widget = self.add_child(P(self.view, text='%s My state is now %s' % (self.arg, an_object.choice)))
            refreshed_widget.set_id('refreshing-paragraph1')
            refreshed_widget.enable_refresh()

            trigger_input.set_refresh_widgets([refreshed_widget])

            link = self.add_child(A(view, Url('#arg=changed'), description='Hash change link'))

        query_fields = ExposedNames()
        query_fields.arg = lambda i: Field()

    fixture.MyForm = MyForm

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    assert browser.wait_for(query_string_fixture.is_state_labelled_now, 'default My state',  1)
    browser.select(XPath.select_labelled('Choice'), 'Three')
    assert browser.wait_for(query_string_fixture.is_state_labelled_now, 'default My state',  3)

    browser.click(XPath.link().with_text('Hash change link'))
    assert browser.wait_for(query_string_fixture.is_state_labelled_now, 'changed My state',  3)
    browser.select(XPath.select_labelled('Choice'), 'Two')
    assert browser.wait_for(query_string_fixture.is_state_labelled_now, 'changed My state',  2)


@with_fixtures(WebFixture, QueryStringFixture, ResponsiveDisclosureFixture)
def test_handle_ajax_error(web_fixture, query_string_fixture, responsive_disclosure_fixture):
    """."""
    fixture = responsive_disclosure_fixture

    class MyForm(fixture.MyForm):
        def __init__(self, view, an_object):
            super().__init__(view, an_object)
            if an_object.choice == 2:
                raise Exception('Intentionally breaking')

    fixture.MyForm = MyForm

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser

    wsgi_app.config.reahlsystem.debug = False #causes redirect to the error page and not stacktrace

    browser.open('/')

    assert browser.wait_for(query_string_fixture.is_state_now, 1)
    browser.select(XPath.select_labelled('Choice'), 'Two')
    assert browser.wait_for_element_visible(XPath.heading(1).with_text('An error occurred:'))
    assert browser.wait_for_element_visible(XPath.paragraph().including_text('Intentionally breaking'))


@with_fixtures(WebFixture, QueryStringFixture, ResponsiveDisclosureFixture)
def test_overridden_names(web_fixture, query_string_fixture, responsive_disclosure_fixture):
    """The overridden names of inputs correctly ensures that that input's state is distinguished from another with the same name."""
    fixture = responsive_disclosure_fixture

    class ModelObject:
        def __init__(self):
            self.choice = [1]

        fields = ExposedNames()
        fields.choice = lambda i: MultiChoiceField([Choice(1, IntegerField(label='One')),
                                                    Choice(2, IntegerField(label='Two')),
                                                    Choice(3, IntegerField(label='Three'))],
                                                   label='Choice')
    fixture.ModelObject = ModelObject

    def create_trigger_input(form, an_object):
        the_input = CheckboxSelectInput(form, an_object.fields.choice.with_discriminator('first'), refresh_widget=form)
        the_input.set_id('marvin')
        return the_input
    fixture.create_trigger_input = create_trigger_input

    class MyForm(fixture.MyForm):
        def __init__(self, view, an_object):
            super().__init__(view, an_object)
            another_model_object = fixture.ModelObject()
            self.layout.add_input(CheckboxSelectInput(self, another_model_object.fields.choice))

    fixture.MyForm = MyForm

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    browser.click('//input[@name="myform-first-choice[]" and @value="3"]')
    assert browser.wait_for(query_string_fixture.is_state_now, [1,3])


class BlockingRefreshFixture(ResponsiveDisclosureFixture):
    should_pause_to_simulate_long_refresh = False

    def new_block_event(self):
        return threading.Event()

    def simulate_long_refresh_start(self):
        self.block_event.wait()

    def simulate_long_refresh_done(self):
        self.block_event.set()

    def new_MyForm(self):
        fixture = self
        class MyFormThatPauses(super().new_MyForm()):
            def __init__(self, view, model_object):
                super().__init__(view, model_object)
                if fixture.should_pause_to_simulate_long_refresh:
                    fixture.simulate_long_refresh_start()

        return MyFormThatPauses

    def is_form_blocked(self, browser):
        form_xpath = XPath('//form[@id="myform"]')
        form_blocked_xpath = XPath('%s/div[@class="blockUI"]' % form_xpath)
        return browser.is_element_present(form_blocked_xpath)


@with_fixtures(WebFixture, BlockingRefreshFixture, QueryStringFixture)
def test_the_form_is_blocked_while_the_widget_is_being_refreshed(web_fixture, blocking_refresh_fixture, query_string_fixture):
    """The form is blocked until the responsive widget has refreshed it contents."""

    fixture = blocking_refresh_fixture

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser

    fixture.should_pause_to_simulate_long_refresh = False
    browser.open('/')

    fixture.should_pause_to_simulate_long_refresh = True
    with web_fixture.reahl_server.in_background(wait_till_done_serving=False):
        browser.click(XPath.option().with_text('Three'), wait_for_ajax=False)

    assert fixture.is_form_blocked(browser)

    fixture.simulate_long_refresh_done()

    assert browser.wait_for(query_string_fixture.is_state_now, 3)
    assert not fixture.is_form_blocked(browser)


@with_fixtures(WebFixture, ResponsiveDisclosureFixture, SqlAlchemyFixture, QueryStringFixture)
def test_form_values_are_not_persisted_until_form_is_submitted(web_fixture, responsive_disclosure_fixture, sql_alchemy_fixture, query_string_fixture):
    """Values submitted via ajax are used only to redraw the screen; they are only changed on the underlying domain once the form is submitted."""

    fixture = responsive_disclosure_fixture

    class ModelObject(Base):
        __tablename__ = 'test_responsive_disclosure_rollback'
        id = Column(Integer, primary_key=True)
        choice = Column(Integer, default=1)

        fields = ExposedNames()
        fields.choice = lambda i: ChoiceField([Choice(1, IntegerField(label='One')),
                                               Choice(2, IntegerField(label='Two')),
                                               Choice(3, IntegerField(label='Three'))],
                                              label='Choice')
    fixture.ModelObject = ModelObject

    class FormWithButton(fixture.MyForm):
        def __init__(self, view, an_object):
            super().__init__(view, an_object)

            self.define_event_handler(self.events.submit)
            self.add_child(ButtonInput(self, self.events.submit))

        events = ExposedNames()
        events.submit = lambda i: Event(label='Submit')

    fixture.MyForm = FormWithButton

    with sql_alchemy_fixture.persistent_test_classes(ModelObject):

        fixture.model_object = ModelObject()
        Session.add(fixture.model_object)

        class MainWidgetWithPersistentModelObject(Widget):
            def __init__(self, view):
                super().__init__(view)
                an_object = fixture.model_object
                self.add_child(fixture.MyForm(view, an_object))

        wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=MainWidgetWithPersistentModelObject.factory())
        web_fixture.reahl_server.set_app(wsgi_app)
        browser = web_fixture.driver_browser
        browser.open('/')

        assert fixture.model_object.choice == 1
        browser.click(XPath.option().with_text('Three'))

        assert browser.wait_for(query_string_fixture.is_state_now, 3)  # The screen was updated,
        assert fixture.model_object.choice == 1                                # but the database not.

        browser.click(XPath.button_labelled('Submit'))
        assert browser.wait_for(query_string_fixture.is_state_now, 3)
        assert fixture.model_object.choice == 3                                # Now the database is updated too.


class DisclosedInputFixture(Fixture):

    def new_trigger_input_type(self):
        return CheckboxInput

    def new_raise_domain_exception_on_submit(self):
        return False

    def new_default_trigger_field_value(self):
        return True

    def new_MyForm(self):
        fixture = self
        class ModelObject:
            def __init__(self):
                self.trigger_field = fixture.default_trigger_field_value
                self.email = None

            events = ExposedNames()
            events.an_event = lambda i: Event(label='click me', action=Action(i.submit))

            def submit(self):
                if fixture.raise_domain_exception_on_submit:
                    raise DomainException()
                fixture.submitted_model_object = self

            fields = ExposedNames()
            fields.trigger_field = lambda i: BooleanField(label='Trigger field')
            fields.email = lambda i: EmailField(required=True, label='Email')

        class MyForm(Form):
            def __init__(self, view):
                super().__init__(view, 'myform')
                self.enable_refresh()
                self.use_layout(FormLayout())

                if self.exception:
                    self.add_child(P(view, text='Exception raised'))

                model_object = ModelObject()
                self.layout.add_input(fixture.trigger_input_type(self, model_object.fields.trigger_field, refresh_widget=self))

                if model_object.trigger_field:
                    self.layout.add_input(TextInput(self, model_object.fields.email))

                self.define_event_handler(model_object.events.an_event)
                self.add_child(ButtonInput(self, model_object.events.an_event))
        return MyForm


@with_fixtures(WebFixture, DisclosedInputFixture)
def test_validation_of_undisclosed_yet_required_input(web_fixture, disclosed_input_fixture):
    """If a Field has a required constraint, but its Input is not currently displayed as part of the form (because of the
       state of another Input), and the form is submitted, the constraint should not cause an exception(input was omitted)."""

    fixture = disclosed_input_fixture

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MyForm.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    assert browser.is_element_present(XPath.input_labelled('Email'))
    browser.click(XPath.input_labelled('Trigger field'))
    assert not browser.is_element_present(XPath.input_labelled('Email'))
    browser.click(XPath.button_labelled('click me'))

    assert not fixture.submitted_model_object.email


@with_fixtures(WebFixture, DisclosedInputFixture)
def test_input_values_retained_upon_domain_exception(web_fixture, disclosed_input_fixture):
    """When a domain exception occurs the values typed into an input are retained on the error page."""
    # Note: the implementation of this is different for dynamic stuff than for plain old forms.
    #
    # Client state is maintained (for a subsequent GET) by posting it to the server in a hidden input; and also saved on an exception.
    # This state is used at Widget construction stage (before the POST is handled) to ensure all Widgets on the View are built as 
    # before, and as per the client state.
    # 
    # This test is about how that state is managed and when which version of the state (saved in DB, POSTed etc) takes precedence.

    fixture = disclosed_input_fixture

    fixture.raise_domain_exception_on_submit = True
    fixture.default_trigger_field_value = False

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MyForm.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    assert not browser.is_element_present(XPath.input_labelled('Email'))
    browser.click(XPath.input_labelled('Trigger field'))
    browser.type(XPath.input_labelled('Email'), 'expectme@example.org')
    browser.click(XPath.button_labelled('click me'))

    assert browser.is_element_present(XPath.paragraph().including_text('Exception raised'))
    assert browser.is_selected(XPath.input_labelled('Trigger field'))
    assert browser.get_value(XPath.input_labelled('Email')) == 'expectme@example.org'


@with_fixtures(WebFixture, DisclosedInputFixture)
def test_inputs_cleared_after_domain_exception_resubmit(web_fixture, disclosed_input_fixture):
    """After a domain exception followed by a successful submit, saved state on the server is 
       cleared, so that newly rendered inputs on the same URL will have defaulted values again."""
    # Also see related comment on test_input_values_retained_upon_domain_exception

    fixture = disclosed_input_fixture

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MyForm.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser

    # First get a domain exception
    fixture.raise_domain_exception_on_submit = True
    fixture.default_trigger_field_value = False
    browser.open('/')

    browser.click(XPath.input_labelled('Trigger field'))
    browser.type(XPath.input_labelled('Email'), 'expectme@example.org')
    browser.click(XPath.button_labelled('click me'))
    assert browser.is_element_present(XPath.paragraph().including_text('Exception raised'))

    # Then successful commit
    fixture.raise_domain_exception_on_submit = False

    browser.click(XPath.button_labelled('click me'))

    # Values are all defaulted like on a first render
    assert not browser.is_element_present(XPath.paragraph().including_text('Exception raised'))
    assert not browser.is_selected(XPath.input_labelled('Trigger field'))
    assert not browser.is_element_present(XPath.paragraph().including_text('Email'))
    browser.click(XPath.input_labelled('Trigger field'))
    assert browser.get_value(XPath.input_labelled('Email')) == ''


class DirectionScenarios(Fixture):
    @scenario
    def forwards(self):
        self.going_forwards = True

    @scenario
    def backwards(self):
        self.going_forwards = False


class InputOrderScenarios(Fixture):
    @scenario
    def next_input_appears(self):
        self.start_with_other_present = False
        self.add_button = True
        self.expected_next_focussed = XPath.input_labelled('Other')

    @scenario
    def next_input_disappears(self):
        self.start_with_other_present = True
        self.add_button = True
        self.expected_next_focussed = XPath.button_labelled('click me')

    @scenario
    def last_input_disappears(self):
        self.start_with_other_present = True
        self.add_button = False
        self.expected_next_focussed = XPath.input_labelled('Edge')


@uses(direction=DirectionScenarios, input_order=InputOrderScenarios)
class TabOrderFixture(Fixture):

    @property
    def going_forwards(self):
        return self.direction.going_forwards

    @property
    def add_button(self):
        return self.input_order.add_button

    @property
    def start_with_other_present(self):
        return self.input_order.start_with_other_present

    def new_MyForm(self):
        fixture = self
        class ModelObject:
            def __init__(self):
                self.trigger_field = fixture.start_with_other_present
                self.other = None
                self.edge = None

            events = ExposedNames()
            events.an_event = lambda i: Event(label='click me')

            fields = ExposedNames()
            fields.trigger_field = lambda i: BooleanField(label='Trigger field')
            fields.other = lambda i: Field(label='Other')
            fields.edge = lambda i: Field(label='Edge')

        class MyForm(Form):
            def __init__(self, view):
                super().__init__(view, 'myform')
                self.enable_refresh()
                self.use_layout(FormLayout())
                if self.exception:
                    self.add_child(P(view, text='Exception raised'))

                model_object = ModelObject()

                trigger_input = TextInput(self, model_object.fields.trigger_field, refresh_widget=self)
                self.define_event_handler(model_object.events.an_event)

                if fixture.going_forwards:
                    self.layout.add_input(TextInput(self, model_object.fields.edge))
                else:
                    if fixture.add_button:
                        self.add_child(ButtonInput(self, model_object.events.an_event))
                    if model_object.trigger_field:
                        self.layout.add_input(TextInput(self, model_object.fields.other))

                self.layout.add_input(trigger_input)

                if fixture.going_forwards:
                    if model_object.trigger_field:
                        self.layout.add_input(TextInput(self, model_object.fields.other))
                    if fixture.add_button:
                        self.add_child(ButtonInput(self, model_object.events.an_event))
                else:
                    self.layout.add_input(TextInput(self, model_object.fields.edge))
        return MyForm


@with_fixtures(WebFixture, TabOrderFixture)
def test_correct_tab_order_for_responsive_widgets(web_fixture, disclosed_input_trigger_fixture):
    """When a user TABs out of an input that then triggers a change, focus is shifted to the correct element as per the page after the refresh."""

    fixture = disclosed_input_trigger_fixture

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MyForm.factory())

    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    current_value = browser.get_value(XPath.input_labelled('Trigger field'))
    new_value = 'on' if current_value == 'off' else 'off'

    browser.type(XPath.input_labelled('Trigger field'), new_value, trigger_blur=False, wait_for_ajax=False)
    browser.press_tab(shift=not fixture.going_forwards)
    assert browser.wait_for(browser.is_focus_on, fixture.input_order.expected_next_focussed)


@with_fixtures(WebFixture, QueryStringFixture, ResponsiveWidgetScenarios)
def test_focus_location_after_refresh_without_tabbing(web_fixture, query_string_fixture, responsive_widget_scenarios):
    """Check that focus remains on changed widget after refresh, without having to trigger the change by pressing TAB."""

    fixture = responsive_widget_scenarios

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    assert browser.wait_for(query_string_fixture.is_state_now, fixture.initial_state)
    fixture.change_value(browser)
    assert browser.wait_for(query_string_fixture.is_state_now, fixture.changed_state)
    assert browser.is_focus_on(fixture.expected_focussed_element)


class TimingFixture(BlockingRefreshFixture):
    def new_ModelObject(self):
        class ModelObject:
            def __init__(self):
                self.choice = 1

            fields = ExposedNames()
            fields.some_text = lambda i: Field(label='Some Text')
            fields.trigger_field = lambda i: Field(label='Trigger')
        return ModelObject

    def new_MyForm(self):
        fixture = self
        class MyFormWithTextInput(super().new_MyForm()):
            def __init__(self, view, model_object):
                super().__init__(view, model_object)
                self.layout.add_input(TextInput(self, model_object.fields.some_text))
        return MyFormWithTextInput

    def create_trigger_input(self, form, an_object):
        return TextInput(form, an_object.fields.trigger_field, refresh_widget=form)


@with_fixtures(WebFixture, TimingFixture, QueryStringFixture)
def test_while_refreshing_typed_input_is_discarded(web_fixture, blocking_refresh_fixture, query_string_fixture):
    """When the user tabs out all keyboard input is ignored until after the page has changed."""

    fixture = blocking_refresh_fixture

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser

    fixture.should_pause_to_simulate_long_refresh = False
    browser.open('/')

    fixture.should_pause_to_simulate_long_refresh = True
    with web_fixture.reahl_server.in_background():
        browser.type(XPath.input_labelled('Trigger'), 'qwerty', trigger_blur=False, wait_for_ajax=False)
        browser.press_tab()
        browser.type_focussed('abc')
        assert 'abc' not in browser.get_value(XPath.input_labelled('Some Text'))
        assert 'abc' not in browser.get_value(XPath.input_labelled('Trigger'))
        fixture.simulate_long_refresh_done()
    
    assert browser.wait_for_not(fixture.is_form_blocked, browser)

    assert 'abc' not in browser.get_value(XPath.input_labelled('Some Text'))
    assert 'abc' not in browser.get_value(XPath.input_labelled('Trigger'))
    browser.type_focussed('asd')
    assert 'asd' in browser.get_value(XPath.input_labelled('Some Text'))


@with_fixtures(WebFixture, DisclosedInputFixture)
def test_ignore_button_click_on_change(web_fixture, disclosed_input_trigger_fixture):
    """If a button click triggers a change to the page (due to a modified TextInput losing focus), the click is ignored."""

    fixture = disclosed_input_trigger_fixture
    fixture.trigger_input_type = TextInput
    fixture.default_trigger_field_value = False

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MyForm.factory())

    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    assert browser.get_value(XPath.input_labelled('Trigger field')) == 'off'
    assert not browser.is_element_present(XPath.input_labelled('Email'))

    browser.type(XPath.input_labelled('Trigger field'), 'on', trigger_blur=False)
    with browser.no_page_load_expected():
        browser.click(XPath.button_labelled('click me'))

    assert browser.is_focus_on(XPath.input_labelled('Trigger field'))
    assert browser.is_element_present(XPath.input_labelled('Email'))
    assert browser.is_on_top(XPath.button_labelled('click me'))


class NestedResponsiveDisclosureFixture(Fixture):

    def new_ModelObject(self):
        class ModelObject:
            def __init__(self):
                self.trigger_field = False
                self.nested_trigger_field = False

            fields = ExposedNames()
            fields.trigger_field = lambda i: BooleanField(label='Trigger field')
            fields.nested_trigger_field = lambda i: BooleanField(label='Nested trigger field')

        return ModelObject

    def new_MyForm(self):
        fixture = self
        class MyNestedChangingWidget(Div):
            def __init__(self, form, model_object):
                self.model_object = model_object
                super().__init__(form.view, css_id='nested_changing_widget')
                self.enable_refresh()

                nested_checkbox_input = CheckboxInput(form, model_object.fields.nested_trigger_field, refresh_widget=self)
                self.add_child(Label(self.view, for_input=nested_checkbox_input))
                self.add_child(nested_checkbox_input)

                if self.model_object.nested_trigger_field:
                    self.add_child(P(self.view, 'My state is now showing nested responsive content'))

        class MyForm(Form):
            def __init__(self, view):
                super().__init__(view, 'myform')
                self.enable_refresh()
                self.use_layout(FormLayout())
                model_object = fixture.ModelObject()

                self.layout.add_input(CheckboxInput(self, model_object.fields.trigger_field, refresh_widget=self))

                if model_object.trigger_field:
                    self.add_child(P(self.view, 'My state is now showing outer responsive content'))
                    self.add_child(MyNestedChangingWidget(self, model_object))


        return MyForm

    def are_all_parts_enabled(self, browser):
        return browser.is_interactable(XPath.input_labelled('Trigger field')) and \
            browser.is_interactable(XPath.input_labelled('Nested trigger field')) and \
            browser.is_on_top(XPath.paragraph().including_text('showing nested responsive content'))


@with_fixtures(WebFixture, QueryStringFixture, NestedResponsiveDisclosureFixture)
def test_inputs_and_widgets_work_when_nested(web_fixture, query_string_fixture, nested_responsive_disclosure_fixture):
    """Refreshable widgets can be nested inside a target widget."""

    fixture = nested_responsive_disclosure_fixture
    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MyForm.factory())

    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    assert browser.wait_for_not(query_string_fixture.is_state_now, 'showing outer responsive content')
    assert browser.wait_for_not(query_string_fixture.is_state_now, 'showing nested responsive content')

    browser.click(XPath.input_labelled('Trigger field'))
    assert browser.wait_for(query_string_fixture.is_state_now, 'showing outer responsive content')
    assert browser.wait_for_not(query_string_fixture.is_state_now, 'showing nested responsive content')

    browser.click(XPath.input_labelled('Nested trigger field'))
    assert browser.wait_for(query_string_fixture.is_state_now, 'showing outer responsive content')
    assert browser.wait_for(query_string_fixture.is_state_now, 'showing nested responsive content')

    assert browser.wait_for(fixture.are_all_parts_enabled, browser)

    browser.click(XPath.input_labelled('Trigger field'))
    assert browser.wait_for_not(query_string_fixture.is_state_now, 'showing outer responsive content')
    assert browser.wait_for_not(query_string_fixture.is_state_now, 'showing nested responsive content')

    # Case: after having loaded the nested bits via ajax (and their Javascript - a second time)
    #  the nested case still works (necessary to test because loading JS a second time can cause bugs)
    browser.click(XPath.input_labelled('Trigger field'))
    assert browser.wait_for(query_string_fixture.is_state_now, 'showing outer responsive content')
    assert browser.wait_for_not(query_string_fixture.is_state_now, 'showing nested responsive content')

    browser.click(XPath.input_labelled('Nested trigger field'))
    assert browser.wait_for(query_string_fixture.is_state_now, 'showing outer responsive content')
    assert browser.wait_for(query_string_fixture.is_state_now, 'showing nested responsive content')

    assert browser.wait_for(fixture.are_all_parts_enabled, browser)


@with_fixtures(WebFixture, DisclosedInputFixture)
def test_clear_previously_given_user_input(web_fixture, disclosed_input_fixture):
    """If an input is refreshed as part of a Widget, and disappears, then reappears after a second refresh, its input is defaulted to the model value."""

    fixture = disclosed_input_fixture
    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MyForm.factory())

    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser

    user_input = 'valid.email@example.org'
    browser.open('/')

    browser.type(XPath.input_labelled('Email'), user_input)

    browser.click(XPath.input_labelled('Trigger field'))
    browser.wait_for_not(browser.is_visible, XPath.input_labelled('Email'))
    browser.click(XPath.input_labelled('Trigger field'))
    retained_value = browser.get_value(XPath.input_labelled('Email'))
    assert retained_value == ''
    assert retained_value != user_input


@with_fixtures(WebFixture, QueryStringFixture, ResponsiveDisclosureFixture)
def test_browser_back_after_state_changes_goes_to_previous_url(web_fixture, query_string_fixture, responsive_disclosure_fixture):
    """If a browser stores an URL in its history, which is the same as the one a user is currently on, 
       when you navigate history to get back to that URL, the page is rendered with newer state."""

    fixture = responsive_disclosure_fixture

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser

    class FormWithButton(fixture.MyForm):
        def __init__(self, view, an_object):
            super().__init__(view, an_object)

            self.define_event_handler(self.events.submit)
            self.add_child(ButtonInput(self, self.events.submit))

        events = ExposedNames()
        events.submit = lambda i: Event(label='Submit')

    fixture.MyForm = FormWithButton

    # create some state on the server side for this URL
    browser.open('/')
    assert browser.wait_for(query_string_fixture.is_state_now, 1)
    browser.select(XPath.select_labelled('Choice'), 'Two')
    assert browser.wait_for(query_string_fixture.is_state_now, 2)

    # submit the page, so we get redirected to the same URL, leaving itself in browser history (webkit only)
    browser.click(XPath.button_labelled('Submit'))
    assert browser.current_url.path == '/'

    # create different state on the same URL we were redirected to 
    browser.select(XPath.select_labelled('Choice'), 'Three')

    # when the user navigates back to the same url in history, the page retains the youngest state
    browser.refresh()
    assert browser.current_url.path == '/'
    assert browser.wait_for(query_string_fixture.is_state_now, 3)



@uses(query_string_fixture=QueryStringFixture)
class RecalculateWidgetFixture(Fixture):
    break_on_recalculate = False
    read_only = False
    def new_ModelObject(self):
        fixture = self
        class ModelObject(Base):
            __tablename__ = 'test_responsive_disclosure_recalculate'
            id = Column(Integer, primary_key=True)
            choice = Column(Integer)
            calculated_state = Column(Integer)

            def __init__(self):
                super().__init__()
                self.choice = 1
                self.recalculate()

            def recalculate(self):
                if fixture.break_on_recalculate and self.choice == 2:
                    raise DomainException(message='Breaking intentionally on recalculate')
                self.calculated_state = self.choice * 10

            def submit(self):
                raise DomainException(message='An exception happened on submit')

            events = ExposedNames()
            events.choice_changed = lambda i: Event(action=Action(i.recalculate))
            events.submit = lambda i: Event(action=Action(i.submit))

            fields = ExposedNames()
            fields.choice = lambda i: ChoiceField([Choice(1, IntegerField(label='One')),
                                                   Choice(2, IntegerField(label='Two')),
                                                   Choice(3, IntegerField(label='Three'))],
                                                  label='Choice')
            fields.calculated_state = lambda i: IntegerField(label='Calculated', writable=Allowed(not fixture.read_only))
        return ModelObject

    def new_model_object(self):
        return self.ModelObject()

    def new_MyForm(self):
        fixture = self
        class MyForm(Form):
            def __init__(self, view, an_object):
                super().__init__(view, 'myform')
                self.use_layout(FormLayout())
                self.an_object = an_object

                self.call_enable_refresh()

                if self.exception:
                    self.layout.add_alert_for_domain_exception(self.exception)
                self.change_trigger_input = TextInput(self, an_object.fields.choice, refresh_widget=self)
                self.layout.add_input(self.change_trigger_input)
                self.add_child(P(self.view, text='My state is now %s' % an_object.choice))
                fixture.add_to_form(self, an_object)
                self.define_event_handler(an_object.events.submit)
                self.add_child(ButtonInput(self, an_object.events.submit))

            def call_enable_refresh(self):
                self.enable_refresh(on_refresh=self.an_object.events.choice_changed)

            def recalculate(self):
                self.an_object.recalculate()


        return MyForm

    def new_MainWidgetWithPersistentModelObject(self):
        fixture = self
        class MainWidgetWithPersistentModelObject(Widget):
            def __init__(self, view):
                super().__init__(view)
                an_object = fixture.model_object
                self.add_child(fixture.MyForm(view, an_object))

        return MainWidgetWithPersistentModelObject


@uses(query_string_fixture=QueryStringFixture, recalculate_fixture=RecalculateWidgetFixture)
class RecalculatedWidgetScenarios(Fixture):

    @scenario
    def plain_widget(self):
        def add_to_form(form, model_object):
            form.add_child(P(form.view, text='My calculated state is now %s' % model_object.calculated_state))

        def check_widget_value(browser, value):
            browser.wait_for(self.query_string_fixture.is_state_labelled_now, 'My calculated state', value)

        self.recalculate_fixture.add_to_form = add_to_form
        self.check_widget_value = check_widget_value
        self.recalculate_fixture.read_only = True

    @scenario
    def writable_input(self):
        def add_to_form(form, model_object):
            text_input = form.layout.add_input(TextInput(form, model_object.fields.calculated_state))
            form.add_child(P(form.view, text='Status: %s' % text_input.get_input_status()))

        def check_widget_value(browser, value):
            browser.wait_for(browser.is_element_value, XPath.input_labelled('Calculated'), str(value))
            status_text = browser.get_text(XPath.paragraph().including_text('Status: '))
            assert 'invalidly_entered' not in status_text

        self.recalculate_fixture.add_to_form = add_to_form
        self.check_widget_value = check_widget_value
        self.recalculate_fixture.read_only = False

    @scenario
    def read_only_input(self):
        self.writable_input()
        self.recalculate_fixture.read_only = True


@with_fixtures(WebFixture, QueryStringFixture, SqlAlchemyFixture, RecalculateWidgetFixture, RecalculatedWidgetScenarios)
def test_recalculate_on_refresh(web_fixture, query_string_fixture, sql_alchemy_fixture, recalculate_fixture, scenario):
    """You can make a widget recalculate domain values upon refresh by adding an Event to enable_refresh()."""

    fixture = recalculate_fixture

    with sql_alchemy_fixture.persistent_test_classes(fixture.ModelObject):

        Session.add(fixture.model_object)

        wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MainWidgetWithPersistentModelObject.factory())
        web_fixture.reahl_server.set_app(wsgi_app)
        browser = web_fixture.driver_browser

        browser.open('/')
        assert browser.wait_for(query_string_fixture.is_state_now, 1)
        scenario.check_widget_value(browser, 10)
        browser.type(XPath.input_labelled('Choice'), '2')

        # Case: values are recalculated after ajax
        assert browser.wait_for(query_string_fixture.is_state_now, 2)
        scenario.check_widget_value(browser, 20)

        # Case: values stay recalculated after submit with exception
        browser.click(XPath.button_labelled('submit'))
        assert browser.is_element_present(XPath.paragraph().including_text('An exception happened on submit'))
        scenario.check_widget_value(browser, 20)


@with_fixtures(WebFixture, QueryStringFixture, SqlAlchemyFixture, RecalculateWidgetFixture)
def test_error_on_refresh_action(web_fixture, query_string_fixture, sql_alchemy_fixture, recalculate_fixture):
    """When a DomainException is raised during an Action executed on_refresh, the Widget should still render
       (albeit differently) despite the fact that there was an exception and all inputs causing the exception
       are retained.
    """

    fixture = recalculate_fixture
    class FormThatCatchesErrors(fixture.MyForm):
        can_calculate = True

        def call_enable_refresh(self):
            self.can_calculate = True
            try:
                super().call_enable_refresh()
            except DomainException as ex:
                self.layout.add_alert_for_domain_exception(ex)
                self.can_calculate = False

    def add_to_form(form, model_object):
        if form.can_calculate:
            form.add_child(P(form.view, text='My calculated state is now %s' % model_object.calculated_state))
        else:
            form.add_child(P(form.view, text='Invalid input, cannot calculate'))

    fixture.MyForm = FormThatCatchesErrors
    fixture.add_to_form = add_to_form

    with sql_alchemy_fixture.persistent_test_classes(fixture.ModelObject):

        Session.add(fixture.model_object)

        wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MainWidgetWithPersistentModelObject.factory())
        web_fixture.reahl_server.set_app(wsgi_app)
        browser = web_fixture.driver_browser

        browser.open('/')
        assert browser.wait_for(query_string_fixture.is_state_now, 1)
        fixture.break_on_recalculate = True

        # The Widget is rendered differently, and inputs retained.
        browser.type(XPath.input_labelled('Choice'), '2', wait_for_ajax=False)
        error_message = XPath.paragraph().including_text('Breaking intentionally on recalculate').inside_of(XPath.div().including_class('errors'))
        assert browser.is_element_present(error_message)
        modified_widget_message = XPath.paragraph().including_text('Invalid input, cannot calculate')
        assert browser.is_element_present(modified_widget_message)

        # After breakage, selecting a working value restored how the Widget renders itself
        browser.type(XPath.input_labelled('Choice'), '3', wait_for_ajax=False)
        assert browser.is_element_present(XPath.paragraph().including_text('My state is now 3'))
        assert browser.is_element_present(XPath.paragraph().including_text('My calculated state is now 30'))

        # Implementation corner case: Subsequent breakages work correctly again
        browser.type(XPath.input_labelled('Choice'), '2', wait_for_ajax=False)
        assert browser.is_element_present(XPath.paragraph().including_text('My state is now 2'))
        assert browser.is_element_present(XPath.paragraph().including_text('Invalid input, cannot calculate'))


class DebugScenarios(Fixture):
    @scenario
    def debug_on(self):
        self.expected_debug = True

    @scenario
    def debug_off(self):
        self.expected_debug = False


@with_fixtures(WebFixture, QueryStringFixture, SqlAlchemyFixture, RecalculateWidgetFixture, DebugScenarios)
def test_forgotten_error_on_refresh_action(web_fixture, query_string_fixture, sql_alchemy_fixture, recalculate_fixture, debug_scenario):
    """When an DomainException is raised during an Action executed on_refresh, and the Widget does not handle it,
       and error page is displayed.
    """

    fixture = recalculate_fixture
    def add_to_form(form, model_object):
        form.add_child(P(form.view, text='My calculated state is now %s' % model_object.calculated_state))

    fixture.add_to_form = add_to_form

    with sql_alchemy_fixture.persistent_test_classes(fixture.ModelObject):

        Session.add(fixture.model_object)

        wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MainWidgetWithPersistentModelObject.factory())
        wsgi_app.config.reahlsystem.debug = debug_scenario.expected_debug
        web_fixture.reahl_server.set_app(wsgi_app)
        browser = web_fixture.driver_browser

        browser.open('/')
        assert browser.wait_for(query_string_fixture.is_state_now, 1)
        fixture.break_on_recalculate = True

        # Upon the ajax error, redirect to an error page
        with web_fixture.reahl_server.in_background(): # because we expect this call to throw an exception and we dont want to catch it here
            browser.type(XPath.input_labelled('Choice'), '2', wait_for_ajax=False)
            browser.wait_for_page_to_load()
        assert browser.wait_for_element_visible(XPath.heading(1).with_text('An error occurred:'))


@with_fixtures(WebFixture, QueryStringFixture, SqlAlchemyFixture)
def test_invalid_trigger_inputs(web_fixture, query_string_fixture, sql_alchemy_fixture):
    """Invalid values of trigger inputs are retained, while the calculated values are based on the last valid values in the domain."""

    fixture = scenario

    class ModelObject(Base):
        __tablename__ = 'test_responsive_disclosure_recalculate_invalids'
        id = Column(Integer, primary_key=True)
        choice = Column(Integer, default=1)
        choice2 = Column(Integer, default=4)
        choice3 = Column(Integer, default=9)
        calculated_state = Column(Integer, default=0)

        def recalculate(self):
            self.calculated_state = self.choice + self.choice2

        def submit(self):
            raise DomainException(message='An exception happened on submit')

        events = ExposedNames()
        events.choice_changed = lambda i: Event(action=Action(i.recalculate))
        events.submit = lambda i: Event(action=Action(i.submit))

        fields = ExposedNames()
        fields.choice = lambda i: ChoiceField([Choice(1, IntegerField(label='One')),
                                               Choice(2, IntegerField(label='Two')),
                                               Choice(3, IntegerField(label='Three'))],
                                              label='Choice')
        fields.choice2 = lambda i: ChoiceField([Choice(4, IntegerField(label='Four')),
                                                Choice(5, IntegerField(label='Five')),
                                                Choice(6, IntegerField(label='Six'))],
                                               label='Choice2')
        fields.calculated_state = lambda i: IntegerField(label='Calculated', writable=Allowed(False))

    class MyForm(Form):
        def __init__(self, view, an_object):
            super().__init__(view, 'myform')
            self.use_layout(FormLayout())
            self.an_object = an_object
            self.enable_refresh(on_refresh=an_object.events.choice_changed)
            if self.exception:
                self.layout.add_alert_for_domain_exception(self.exception)
            self.change_trigger_input = TextInput(self, an_object.fields.choice, refresh_widget=self)
            self.layout.add_input(self.change_trigger_input)
            self.add_child(P(self.view, text='My choice state is now %s' % an_object.choice))
            self.change2_trigger_input = TextInput(self, an_object.fields.choice2, refresh_widget=self)
            self.layout.add_input(self.change2_trigger_input)
            self.add_child(P(self.view, text='My choice2 state is now %s' % an_object.choice2))
            self.add_child(P(self.view, text='My calculated state is now %s' % an_object.calculated_state))
            self.define_event_handler(an_object.events.submit)
            self.add_child(ButtonInput(self, an_object.events.submit))

    class MainWidgetWithPersistentModelObject(Widget):
        def __init__(self, view):
            super().__init__(view)
            an_object = fixture.model_object
            self.add_child(MyForm(view, an_object))


    with sql_alchemy_fixture.persistent_test_classes(ModelObject):

        fixture.model_object = ModelObject()
        Session.add(fixture.model_object)

        wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=MainWidgetWithPersistentModelObject.factory())
        web_fixture.reahl_server.set_app(wsgi_app)
        browser = web_fixture.driver_browser

        browser.open('/')
        assert browser.wait_for(query_string_fixture.is_state_labelled_now, 'My choice state', 1)
        assert browser.wait_for(query_string_fixture.is_state_labelled_now, 'My choice2 state', 4)
        assert browser.wait_for(query_string_fixture.is_state_labelled_now, 'My calculated state', '5')

        # Case: Entering an invalid value does not trigger a refresh of the input doing the triggering
        with web_fixture.driver_browser.no_load_expected_for('input[name="myform-choice"]'):
            browser.type(XPath.input_labelled('Choice'), 'invalid value')

        # Case: Entering an valid value in a different trigger, triggers a refresh, but last valid value of choice is used
        browser.type(XPath.input_labelled('Choice2'), '5')
        assert browser.wait_for(query_string_fixture.is_state_labelled_now, 'My calculated state', '6')

        #       But, the invalid input is retained
        assert browser.is_element_value(XPath.input_labelled('Choice'), 'invalid value')


@with_fixtures(WebFixture, QueryStringFixture, SqlAlchemyFixture)
def test_invalid_non_trigger_input_corner_case(web_fixture, query_string_fixture, sql_alchemy_fixture):
    """If an invalid value was submitted via ajax for a non-trigger input, and a valid value is submitted for is with a 
       form, and a DomainException happens... then the non-trigger input must retain its new, valid value."""

    fixture = scenario

    class ModelObject(Base):
        __tablename__ = 'test_responsive_disclosure_recalculate_invalids'
        id = Column(Integer, primary_key=True)
        choice = Column(Integer, default=1)
        choice3 = Column(Integer, default=9)
        calculated_state = Column(Integer, default=0)

        def recalculate(self):
            self.calculated_state = self.choice * 10

        def submit(self):
            raise DomainException(message='An exception happened on submit')

        events = ExposedNames()
        events.choice_changed = lambda i: Event(action=Action(i.recalculate))
        events.submit = lambda i: Event(action=Action(i.submit))

        fields = ExposedNames()
        fields.choice = lambda i: ChoiceField([Choice(1, IntegerField(label='One')),
                                               Choice(2, IntegerField(label='Two')),
                                               Choice(3, IntegerField(label='Three'))],
                                              label='Choice')
        fields.choice3 = lambda i: ChoiceField([Choice(7, IntegerField(label='Seven')),
                                                Choice(8, IntegerField(label='Eight')),
                                                Choice(9, IntegerField(label='Nine'))],
                                               label='Choice3')
        fields.calculated_state = lambda i: IntegerField(label='Calculated', writable=Allowed(False))

    class MyForm(Form):
        def __init__(self, view, an_object):
            super().__init__(view, 'myform')
            self.an_object = an_object
            self.use_layout(FormLayout())
            self.enable_refresh(on_refresh=an_object.events.choice_changed)
            if self.exception:
                self.add_child(P(self.view, text=str(self.exception)))
            self.change_trigger_input = self.layout.add_input(TextInput(self, an_object.fields.choice, refresh_widget=self))
            self.add_child(P(self.view, text='My choice state is now %s' % an_object.choice))
            self.change3_non_trigger_input = self.layout.add_input(TextInput(self, an_object.fields.choice3))
            self.add_child(P(self.view, text='My calculated state is now %s' % an_object.calculated_state))
            self.define_event_handler(an_object.events.submit)
            self.add_child(ButtonInput(self, an_object.events.submit))

    class MainWidgetWithPersistentModelObject(Widget):
        def __init__(self, view):
            super().__init__(view)
            an_object = fixture.model_object
            self.add_child(MyForm(view, an_object))


    with sql_alchemy_fixture.persistent_test_classes(ModelObject):

        fixture.model_object = ModelObject()
        Session.add(fixture.model_object)

        wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=MainWidgetWithPersistentModelObject.factory())
        web_fixture.reahl_server.set_app(wsgi_app)
        browser = web_fixture.driver_browser

        browser.open('/')
        assert browser.wait_for(query_string_fixture.is_state_labelled_now, 'My choice state', 1)
        assert browser.wait_for(query_string_fixture.is_state_labelled_now, 'My calculated state', '10')

        browser.type(XPath.input_labelled('Choice3'), 'other invalid input')
        browser.type(XPath.input_labelled('Choice'), '2')
        browser.press_tab()
        assert browser.wait_for(query_string_fixture.is_state_labelled_now, 'My calculated state', '20')

        assert browser.is_element_value(XPath.input_labelled('Choice3'), 'other invalid input')
        browser.type(XPath.input_labelled('Choice3'), '8')
        browser.click(XPath.button_labelled('submit'))
        assert browser.is_element_present(XPath.paragraph().including_text('An exception happened on submit'))
        assert browser.is_element_value(XPath.input_labelled('Choice3'), '8')


# TODO: What about when you have multiple Forms on a page, with an input on both Forms that uses a Field bound to the same name on the same domain object?
#       Upon Ajax, all form inputs are submitted, not just one. It may be that their processing is ordered such that the one that never refreshes always happens last.
#       Because it happens last, it always overwrites the value to the old non-refreshed value and nothing ever changes?
#       One idea: first accept_input for all inputs outside of the widget being refreshed. Then the inputs in that Widget. Then the actual input which triggered the change. ?
