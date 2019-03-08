# Copyright 2018 Reahl Software Services (Pty) Ltd. All rights reserved.
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


from __future__ import print_function, unicode_literals, absolute_import, division

import threading

from sqlalchemy import Column, Integer, Boolean

from reahl.tofu import Fixture, expected, scenario, uses
from reahl.tofu.pytestsupport import with_fixtures

from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import XPath, Browser
from reahl.web.fw import Widget
from reahl.web.ui import Form, Div, SelectInput, Label, P, RadioButtonSelectInput, CheckboxSelectInput, \
    CheckboxInput, ButtonInput, TextInput
from reahl.component.modelinterface import Field, BooleanField, MultiChoiceField, ChoiceField, Choice, exposed, IntegerField, \
    EmailField, Event
from reahl.component.exceptions import ProgrammerError, DomainException
from reahl.web.dynamic import DynamicSection
from reahl.web_dev.inputandvalidation.test_widgetqueryargs import QueryStringFixture
from reahl.sqlalchemysupport import Base, Session
from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture


@uses(web_fixture=WebFixture)
class ResponsiveDisclosureFixture(Fixture):

    def new_ModelObject(self):
        class ModelObject(object):
            @exposed
            def fields(self, fields):
                fields.choice = ChoiceField([Choice(1, IntegerField(label='One')),
                                             Choice(2, IntegerField(label='Two')),
                                             Choice(3, IntegerField(label='Three'))],
                                            default=1,
                                            label='Choice')
        return ModelObject

    def new_MyChangingWidget(self):
        class MyChangingWidget(Div):
            def __init__(self, view, trigger_input, model_object):
                self.trigger_input = trigger_input
                self.model_object = model_object
                super(MyChangingWidget, self).__init__(view, css_id='dave')
                self.enable_refresh()
                trigger_input.enable_notify_change(self, self.query_fields.fancy_state)
                self.add_child(P(self.view, text='My state is now %s' % self.fancy_state))

            @property
            def fancy_state(self):
                return self.model_object.choice

            @exposed
            def query_fields(self, fields):
                fields.fancy_state = self.model_object.fields.choice

        return MyChangingWidget

    def new_MainWidget(self):
        fixture = self
        class MainWidget(Widget):
            def __init__(self, view):
                super(MainWidget, self).__init__(view)
                an_object = fixture.ModelObject()
                form = self.add_child(fixture.MyForm(view, an_object))
                self.add_child(fixture.MyChangingWidget(view, form.change_trigger_input, an_object))

        return MainWidget

    def new_MyForm(self):
        class MyForm(Form):
            def __init__(self, view, an_object):
                super(MyForm, self).__init__(view, 'myform')
                self.change_trigger_input = SelectInput(self, an_object.fields.choice)
                self.add_child(Label(view, for_input=self.change_trigger_input))
                self.add_child(self.change_trigger_input)
        return MyForm


class ResponsiveWidgetScenarios(ResponsiveDisclosureFixture):
    @scenario
    def select_input(self):
        fixture = self

        def change_value(browser):
            browser.select(XPath.select_labelled('Choice'), 'Three')
        self.change_value = change_value
        self.initial_state = 1
        self.changed_state = 3

    @scenario
    def radio_buttons(self):
        fixture = self

        class MyForm(Form):
            def __init__(self, view, an_object):
                super(MyForm, self).__init__(view, 'myform')
                self.change_trigger_input = RadioButtonSelectInput(self, an_object.fields.choice)
                self.add_child(Label(view, for_input=self.change_trigger_input))
                self.add_child(self.change_trigger_input)
        self.MyForm = MyForm

        def change_value(browser):
            browser.click(XPath.input_labelled('Three'))
        self.change_value = change_value
        self.initial_state = 1
        self.changed_state = 3

    @scenario
    def single_valued_checkbox(self):
        fixture = self

        class ModelObject(object):
            @exposed
            def fields(self, fields):
                fields.choice = BooleanField(default=False, label='Choice',
                                             true_value='✓', false_value='⍻')
        self.ModelObject = ModelObject

        class MyForm(Form):
            def __init__(self, view, an_object):
                super(MyForm, self).__init__(view, 'myform')
                self.change_trigger_input = CheckboxInput(self, an_object.fields.choice)
                self.change_trigger_input.set_id('marvin')
                self.add_child(Label(view, for_input=self.change_trigger_input))
                self.add_child(self.change_trigger_input)
        self.MyForm = MyForm

        def change_value(browser):
            browser.click(XPath.input_labelled('Choice'))
        self.change_value = change_value
        self.initial_state = False
        self.changed_state = True

    @scenario
    def multi_valued_checkbox_select(self):
        fixture = self

        class ModelObject(object):
            @exposed
            def fields(self, fields):
                fields.choice = MultiChoiceField([Choice(1, IntegerField(label='One')),
                                                  Choice(2, IntegerField(label='Two')),
                                                  Choice(3, IntegerField(label='Three'))],
                                                 default=[1],
                                                 label='Choice')
        self.ModelObject = ModelObject

        class MyForm(Form):
            def __init__(self, view, an_object):
                super(MyForm, self).__init__(view, 'myform')
                self.change_trigger_input = CheckboxSelectInput(self, an_object.fields.choice)
                self.change_trigger_input.set_id('marvin')
                self.add_child(Label(view, for_input=self.change_trigger_input))
                self.add_child(self.change_trigger_input)
        self.MyForm = MyForm

        def change_value(browser):
            browser.click(XPath.input_labelled('Three'))
        self.change_value = change_value
        self.initial_state = [1]
        self.changed_state = [1, 3]

    @scenario
    def multi_valued_checkbox_select_with_single_choice_corner_case_empty_a_list(self):
        self.multi_valued_checkbox_select()
        fixture = self

        class ModelObject(object):
            @exposed
            def fields(self, fields):
                fields.choice = MultiChoiceField([Choice(1, IntegerField(label='One'))],
                                                 default=[1],
                                                 label='Choice')
        self.ModelObject = ModelObject
        #self.MyForm from multi_valued_checkbox_select

        def change_value(browser):
            browser.click(XPath.input_labelled('One'))
        self.change_value = change_value
        self.initial_state = [1]
        self.changed_state = []

    @scenario
    def multi_valued_checkbox_select_with_single_choice_corner_case_add_to_empty_list(self):
        self.multi_valued_checkbox_select()
        fixture = self

        class ModelObject(object):
            @exposed
            def fields(self, fields):
                fields.choice = MultiChoiceField([Choice(1, IntegerField(label='One'))],
                                                 default=[],
                                                 label='Choice')
        self.ModelObject = ModelObject
        #self.MyForm from multi_valued_checkbox_select

        def change_value(browser):
            browser.click(XPath.input_labelled('One'))
        self.change_value = change_value
        self.initial_state = []
        self.changed_state = [1]

    @scenario
    def multi_valued_select(self):
        fixture = self

        class ModelObject(object):
            @exposed
            def fields(self, fields):
                fields.choice = MultiChoiceField([Choice(1, IntegerField(label='One')),
                                                  Choice(2, IntegerField(label='Two')),
                                                  Choice(3, IntegerField(label='Three'))],
                                                 default=[1],
                                                 label='Choice')
        self.ModelObject = ModelObject

        class MyForm(Form):
            def __init__(self, view, an_object):
                super(MyForm, self).__init__(view, 'myform')
                self.change_trigger_input = SelectInput(self, an_object.fields.choice)
                self.change_trigger_input.set_id('marvin')
                self.add_child(Label(view, for_input=self.change_trigger_input))
                self.add_child(self.change_trigger_input)
        self.MyForm = MyForm

        def change_value(browser):
            browser.select(XPath.select_labelled('Choice'), 'Three')
        self.change_value = change_value
        self.initial_state = [1]
        self.changed_state = [1, 3]


@with_fixtures(WebFixture, QueryStringFixture, ResponsiveWidgetScenarios)
def test_input_values_can_be_widget_arguments(web_fixture, query_string_fixture, responsive_widget_scenarios):
    """Widget query arguments can be linked to the value of an input, which means the Widget will be re-rendered if the input value changes."""

    fixture = responsive_widget_scenarios

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    assert browser.wait_for(query_string_fixture.is_state_now, fixture.initial_state)
    fixture.change_value(browser)
    assert browser.wait_for(query_string_fixture.is_state_now, fixture.changed_state)


class MultipleTriggerFixture(Fixture):
    def is_widget_blocked(self, browser):
        changing_widget_xpath = XPath('//div[@id="changing_widget_id"]')
        changing_widget_blocked_xpath = XPath('%s/div[@class="blockUI"]' % changing_widget_xpath)
        return browser.is_element_present(changing_widget_blocked_xpath)


@with_fixtures(WebFixture, QueryStringFixture, MultipleTriggerFixture)
def test_invalid_values_block_out_dependent_widgets(web_fixture, query_string_fixture, multiple_trigger_fixture):
    """If the user types an invalid value into an input serving as argument for one or more Widgets, the widgets are blocked out"""

    class ModelObject(object):
        @exposed
        def fields(self, fields):
            fields.choice = ChoiceField([Choice(1, IntegerField(label='One')),
                                         Choice(2, IntegerField(label='Two')),
                                         Choice(3, IntegerField(label='Three'))],
                                        default=1,
                                        label='Choice')
            fields.another_choice = ChoiceField([Choice(4, IntegerField(label='Four')),
                                         Choice(5, IntegerField(label='Five')),
                                         Choice(6, IntegerField(label='Six'))],
                                        default=4,
                                        label='Another Choice')

    class MyForm(Form):
        def __init__(self, view, an_object):
            super(MyForm, self).__init__(view, 'myform')
            self.change_trigger_input = TextInput(self, an_object.fields.choice)
            self.add_child(Label(view, for_input=self.change_trigger_input))
            self.add_child(self.change_trigger_input)

            self.sibling_change_trigger_input = TextInput(self, an_object.fields.another_choice)
            self.add_child(Label(view, for_input=self.sibling_change_trigger_input))
            self.add_child(self.sibling_change_trigger_input)

    class MyChangingWidget(Div):
        def __init__(self, view, trigger_input, sibling_trigger_input, model_object):
            self.trigger_input = trigger_input
            self.sibling_trigger_input = sibling_trigger_input
            self.model_object = model_object
            super(MyChangingWidget, self).__init__(view, css_id='changing_widget_id')
            self.enable_refresh()
            trigger_input.enable_notify_change(self, self.query_fields.fancy_state)
            sibling_trigger_input.enable_notify_change(self, self.query_fields.another_fancy_state)
            self.add_child(P(self.view, text='My state is now %s and %s' % (self.fancy_state, self.another_fancy_state)))

        @property
        def fancy_state(self):
            return self.model_object.choice

        @property
        def another_fancy_state(self):
            return self.model_object.another_choice

        @exposed
        def query_fields(self, fields):
            fields.fancy_state = self.model_object.fields.choice
            fields.another_fancy_state = self.model_object.fields.another_choice


    class MainWidget(Widget):
        def __init__(self, view):
            super(MainWidget, self).__init__(view)
            an_object = ModelObject()
            form = self.add_child(MyForm(view, an_object))
            self.add_child(MyChangingWidget(view, form.change_trigger_input, form.sibling_change_trigger_input, an_object))


    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    # Case: an invalid option blocks the Widget out, does not refresh
    assert not multiple_trigger_fixture.is_widget_blocked(browser)    
    assert query_string_fixture.is_state_now('1 and 4')

    browser.type(XPath.input_labelled('Choice'), 'not a valid option')
    browser.press_tab()
    assert browser.wait_for(multiple_trigger_fixture.is_widget_blocked, browser)    
    assert browser.wait_for(query_string_fixture.is_state_now, '1 and 4')

    # Case: a valid option changes does nothing if its sibling is still invalid
    browser.type(XPath.input_labelled('Another Choice'), '5')
    assert browser.wait_for(multiple_trigger_fixture.is_widget_blocked, browser)    
    assert browser.wait_for(query_string_fixture.is_state_now, '1 and 4')

    # Case: when all siblings are valid, the widget is refreshed, and it includes all relevant changed values
    browser.type(XPath.input_labelled('Choice'), '2')
    browser.press_tab()
    assert browser.wait_for_not(multiple_trigger_fixture.is_widget_blocked, browser)    
    assert browser.wait_for(query_string_fixture.is_state_now, '2 and 5')


class BlockingRefreshFixture(ResponsiveDisclosureFixture):
    should_pause_to_simulate_long_refresh = False

    def new_block_event(self):
        return threading.Event()

    def simulate_long_refresh_start(self):
        self.block_event.wait()

    def simulate_long_refresh_done(self):
        self.block_event.set()

    def new_MyChangingWidget(self):
        fixture = self
        class ChangingWidgetThatPauses(super(BlockingRefreshFixture, self).new_MyChangingWidget()):
            def __init__(self, view, trigger_input, model_object):
                super(ChangingWidgetThatPauses, self).__init__(view, trigger_input, model_object)
                if fixture.should_pause_to_simulate_long_refresh:
                    fixture.simulate_long_refresh_start()

        return ChangingWidgetThatPauses

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
        browser.click(XPath.option_with_text('Three'))

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
        number = Column(Integer)
        choice = Column(Integer, default=1)

        @exposed
        def fields(self, fields):
            fields.choice = ChoiceField([Choice(1, IntegerField(label='One')),
                                         Choice(2, IntegerField(label='Two')),
                                         Choice(3, IntegerField(label='Three'))],
                                         label='Choice')
    fixture.ModelObject = ModelObject

    class FormWithButton(fixture.MyForm):
        def __init__(self, view, an_object):
            super(FormWithButton, self).__init__(view, an_object)

            self.define_event_handler(self.events.submit)
            self.add_child(ButtonInput(self, self.events.submit))

        @exposed
        def events(self, events):
            events.submit = Event(label='Submit')

    fixture.MyForm = FormWithButton

    with sql_alchemy_fixture.persistent_test_classes(ModelObject):

        model_object = ModelObject(number=123)
        Session.add(model_object)

        class MainWidget(Widget):
            def __init__(self, view):
                super(MainWidget, self).__init__(view)
                an_object = model_object
                form = self.add_child(fixture.MyForm(view, an_object))
                self.add_child(fixture.MyChangingWidget(view, form.change_trigger_input, an_object))
        fixture.MainWidget = MainWidget

        wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=MainWidget.factory())
        web_fixture.reahl_server.set_app(wsgi_app)
        browser = web_fixture.driver_browser
        browser.open('/')

        assert model_object.choice == 1
        browser.click(XPath.option_with_text('Three'))

        assert browser.wait_for(query_string_fixture.is_state_now, 3)  # The screen was updated,
        assert model_object.choice == 1                                # but the database not.

        browser.click(XPath.button_labelled('Submit'))
        assert browser.wait_for(query_string_fixture.is_state_now, 3)
        assert model_object.choice == 3                                # Now the database is updated too.


class DisclosedInputFixture(Fixture):

    def new_trigger_input_type(self):
        return CheckboxInput

    def new_model_object(self):
        class ModelObject(object):
            def __init__(self):
                self.trigger_field = True
                self.email = None

            @exposed
            def events(self, events):
                events.an_event = Event(label='click me')

            @exposed
            def fields(self, fields):
                fields.trigger_field = BooleanField(label='Trigger field')
                fields.email = EmailField(required=True, label='Email') #has required Validation Constraint
        return ModelObject()

    def new_MyForm(self):
        fixture = self
        class MyForm(Form):
            def __init__(self, view):
                super(MyForm, self).__init__(view, 'myform')

                checkbox_input = fixture.trigger_input_type(self, fixture.model_object.fields.trigger_field)
                self.add_child(Label(view, for_input=checkbox_input))
                self.add_child(checkbox_input)

                self.add_child(fixture.MyChangingWidget(self, checkbox_input, fixture.model_object))

                self.define_event_handler(fixture.model_object.events.an_event)
                self.add_child(ButtonInput(self, fixture.model_object.events.an_event))
        return MyForm

    def new_MyChangingWidget(self):
        fixture = self
        class MyChangingWidget(Div):
            def __init__(self, form, trigger_input, model_object):
                self.model_object = model_object
                super(MyChangingWidget, self).__init__(form.view, css_id='requiredinfoid')
                self.enable_refresh()
                trigger_input.enable_notify_change(self, self.query_fields.trigger_field)

                if self.model_object.trigger_field:
                    text_input = TextInput(form, self.model_object.fields.email)
                    self.add_child(Label(form.view, for_input=text_input))
                    self.add_child(text_input)

            @exposed
            def query_fields(self, fields):
                fields.trigger_field = self.model_object.fields.trigger_field
        return MyChangingWidget


@with_fixtures(WebFixture, DisclosedInputFixture)
def test_validation_of_undisclosed_yet_required_input(web_fixture, disclosed_input_fixture):
    """If a Field has a required constraint, but its Input is not currently displayed as part of the form (because of the
       state of another Input), and the form is submitted, the constraint should not cause an exception(input was omitted)."""

    fixture = disclosed_input_fixture

    model_object = fixture.model_object
    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MyForm.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    assert browser.is_element_present(XPath.input_labelled('Email'))
    browser.click(XPath.input_labelled('Trigger field'))
    assert not browser.is_element_present(XPath.input_labelled('Email'))
    browser.click(XPath.button_labelled('click me'))

    assert model_object.trigger_field is False
    assert not model_object.email


@with_fixtures(WebFixture, ResponsiveDisclosureFixture)
def test_trigger_input_may_not_be_on_refreshing_widget(web_fixture, responsive_disclosure_fixture):
    """You may not trigger one of your parents to refresh"""

    fixture = responsive_disclosure_fixture

    class ChangingWidget(fixture.MyChangingWidget):
        def __init__(self, view, form, model_object):
            super(ChangingWidget, self).__init__(view, form.change_trigger_input, model_object)
            self.add_child(form)

    class MainWidget(Widget):
        def __init__(self, view):
            super(MainWidget, self).__init__(view)
            model_object = fixture.ModelObject()
            form = fixture.MyForm(view, model_object)
            self.add_child(ChangingWidget(view, form, model_object))


    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=MainWidget.factory())
    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    
    with expected(ProgrammerError, test='Inputs are not allowed where they can trigger themselves to be refreshed. Some inputs were incorrectly placed:\n\t<SelectInput name=choice> is refreshed by <ChangingWidget div id="dave"> via field <ChoiceField name=choice>\n'):
        browser.open('/')


@with_fixtures(WebFixture, DisclosedInputFixture)
def test_correct_tab_order_for_responsive_widgets(web_fixture, disclosed_input_trigger_fixture):
    """When a user TAB's out of an input that then triggers a change, the tab is ignored and focus stays on the original input so that the tab order can be recalculated."""

    fixture = disclosed_input_trigger_fixture
    fixture.trigger_input_type = TextInput

    model_object = fixture.model_object
    model_object.trigger_field = False
    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MyForm.factory())

    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    # Case: a new input appears in next tab order position
    assert browser.get_value(XPath.input_labelled('Trigger field')) == 'off'
    browser.press_tab()
    assert browser.is_focus_on(XPath.input_labelled('Trigger field'))
    browser.type(XPath.input_labelled('Trigger field'), 'on')
    browser.press_tab()
    browser.press_tab()
    assert browser.is_focus_on(XPath.input_labelled('Email'))
    
    # Case: an input disappears from the next tab order position
    browser.type(XPath.input_labelled('Trigger field'), 'off')
    browser.press_tab()
    browser.press_tab()
    assert browser.is_focus_on(XPath.button_labelled('click me'))


@with_fixtures(WebFixture, DisclosedInputFixture)
def test_ignore_button_click_on_change(web_fixture, disclosed_input_trigger_fixture):
    """If a button click triggers a change to the page (due to a modified TextInput losing focus), the click is ignored."""

    fixture = disclosed_input_trigger_fixture
    fixture.trigger_input_type = TextInput

    model_object = fixture.model_object
    model_object.trigger_field = False
    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=fixture.MyForm.factory())

    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    assert browser.get_value(XPath.input_labelled('Trigger field')) == 'off'
    assert not browser.is_element_present(XPath.input_labelled('Email'))

    browser.type(XPath.input_labelled('Trigger field'), 'on')
    with browser.no_page_load_expected():
        browser.click(XPath.button_labelled('click me'))

    assert browser.is_focus_on(XPath.input_labelled('Trigger field'))
    assert browser.is_element_present(XPath.input_labelled('Email'))
    assert browser.is_on_top(XPath.button_labelled('click me'))


class NestedResponsiveDisclosureFixture(Fixture):

    def new_ModelObject(self):
        class ModelObject(object):
            def __init__(self):
                self.trigger_field = False
                self.nested_trigger_field = False

            @exposed
            def fields(self, fields):
                fields.trigger_field = BooleanField(label='Trigger field')
                fields.nested_trigger_field = BooleanField(label='Nested trigger field')

        return ModelObject

    def new_MyForm(self):
        fixture = self
        class MyForm(Form):
            def __init__(self, view):
                super(MyForm, self).__init__(view, 'myform')

                model_object = fixture.ModelObject()
                checkbox_input = CheckboxInput(self, model_object.fields.trigger_field)
                self.add_child(Label(view, for_input=checkbox_input))
                self.add_child(checkbox_input)

                self.add_child(fixture.MyChangingWidget(self, checkbox_input, model_object))
        return MyForm

    def new_MyChangingWidget(self):
        fixture = self

        class MyNestedChangingWidget(Div):
            def __init__(self, form, trigger_input, model_object):
                self.model_object = model_object
                super(MyNestedChangingWidget, self).__init__(form.view, css_id='nested_changing_widget')
                self.enable_refresh()
                trigger_input.enable_notify_change(self, self.query_fields.nested_trigger_field)

                if self.model_object.nested_trigger_field:
                    self.add_child(P(self.view, 'My state is now showing nested responsive content'))

            @exposed
            def query_fields(self, fields):
                fields.nested_trigger_field = self.model_object.fields.nested_trigger_field

        class MyChangingWidget(Div):
            def __init__(self, form, trigger_input, model_object):
                self.model_object = model_object
                super(MyChangingWidget, self).__init__(form.view, css_id='requiredinfoid')
                self.enable_refresh()
                trigger_input.enable_notify_change(self, self.query_fields.trigger_field)

                if self.model_object.trigger_field:
                    self.add_child(P(self.view, 'My state is now showing outer responsive content'))
                    nested_checkbox_input = CheckboxInput(form, model_object.fields.nested_trigger_field)
                    self.add_child(Label(self.view, for_input=nested_checkbox_input))
                    self.add_child(nested_checkbox_input)

                    self.add_child(MyNestedChangingWidget(form, nested_checkbox_input, model_object))

            @exposed
            def query_fields(self, fields):
                fields.trigger_field = self.model_object.fields.trigger_field
        return MyChangingWidget

    def are_all_parts_enabled(self, browser):
        return browser.is_interactable(XPath.input_labelled('Trigger field')) and \
            browser.is_interactable(XPath.input_labelled('Nested trigger field')) and \
            browser.is_on_top(XPath.paragraph_containing('showing nested responsive content'))


@with_fixtures(WebFixture, SqlAlchemyFixture, QueryStringFixture, NestedResponsiveDisclosureFixture)
def test_inputs_and_widgets_work_when_nested(web_fixture, sql_alchemy_fixture, query_string_fixture, nested_responsive_disclosure_fixture):
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
    assert browser.wait_for(query_string_fixture.is_state_now, 'showing nested responsive content')

    browser.click(XPath.input_labelled('Nested trigger field'))
    assert browser.wait_for(query_string_fixture.is_state_now, 'showing outer responsive content')
    assert browser.wait_for_not(query_string_fixture.is_state_now, 'showing nested responsive content')

    browser.click(XPath.input_labelled('Nested trigger field'))
    assert browser.wait_for(fixture.are_all_parts_enabled, browser)


@with_fixtures(WebFixture)
def test_retain_user_input_on_trigger_change(web_fixture):
    """"""

    class ModelObject(object):
        @exposed
        def fields(self, fields):
            fields.choice = ChoiceField([Choice(1, IntegerField(label='One')),
                                         Choice(2, IntegerField(label='Two'))],
                                        default=1,
                                        label='Choice')
            fields.alpha = Field(label="Alpha")
            fields.bravo1 = Field(label="Bravo1")
            fields.bravo2 = Field(label="Bravo2")

    an_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view):
            super(MyForm, self).__init__(view, 'myform')
            self.change_trigger_input = RadioButtonSelectInput(self, an_object.fields.choice)
            self.add_child(Label(view, for_input=self.change_trigger_input))
            self.add_child(self.change_trigger_input)
            self.add_child(MoreInputsSection(self, an_object, self.change_trigger_input))

    class MoreInputsSection(DynamicSection):
        def __init__(self, form, an_object, trigger_input):
            super(MoreInputsSection, self).__init__(form, 'moreinputs', [trigger_input])

            choice_selected = an_object.choice
            if choice_selected == 1:
                input_alpha = TextInput(form, an_object.fields.alpha)
                self.add_child(Label(form.view, for_input=input_alpha))
                self.add_child(input_alpha)

                input_bravo1 = TextInput(form, an_object.fields.bravo1)
                self.add_child(Label(form.view, for_input=input_bravo1))
                self.add_child(input_bravo1)

            elif choice_selected == 2:
                input_bravo1 = TextInput(form, an_object.fields.bravo1)
                self.add_child(Label(form.view, for_input=input_bravo1))
                self.add_child(input_bravo1)

                input_bravo2 = TextInput(form, an_object.fields.bravo2)
                self.add_child(Label(form.view, for_input=input_bravo2))
                self.add_child(input_bravo2)

    class MainWidget(Widget):
        def __init__(self, view):
            super(MainWidget, self).__init__(view)
            self.add_child(MyForm(view))

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=MyForm.factory())

    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    #populate the inputs
    browser.type(XPath.input_labelled('Alpha'), 'a')
    browser.type(XPath.input_labelled('Bravo1'), 'b1')

    browser.click(XPath.input_labelled('Two'))
    retained_value = browser.get_value(XPath.input_labelled('Bravo1'))
    assert retained_value == 'b1'


@with_fixtures(WebFixture)
def test_retain_nested_trigger_input_values_when_rerendered(web_fixture):
    """"""

    class ModelObject(object):
        @exposed
        def fields(self, fields):
            fields.choice = ChoiceField([Choice(1, IntegerField(label='One')),
                                         Choice(2, IntegerField(label='Two'))],
                                        default=1,
                                        label='Choice')
            fields.alpha = Field(label="Alpha")
            fields.bravo = Field(label="Bravo")
            fields.agree = BooleanField(label='I agree')
            fields.charlie = Field(label="Charlie")

    an_object = ModelObject()

    class MyForm(Form):
        def __init__(self, view):
            super(MyForm, self).__init__(view, 'myform')
            self.change_trigger_input = RadioButtonSelectInput(self, an_object.fields.choice)
            self.add_child(Label(view, for_input=self.change_trigger_input))
            self.add_child(self.change_trigger_input)
            self.add_child(MoreInputsSection(self, self.change_trigger_input))

    class MoreInputsSection(DynamicSection):
        def __init__(self, form, trigger_input):
            super(MoreInputsSection, self).__init__(form, 'moreinputs', [trigger_input])

            choice_selected = an_object.choice
            if choice_selected == 1:
                input_alpha = TextInput(form, an_object.fields.alpha)
                self.add_child(Label(form.view, for_input=input_alpha))
                self.add_child(input_alpha)
            if choice_selected == 2:
                input_bravo = TextInput(form, an_object.fields.bravo)
                self.add_child(Label(form.view, for_input=input_bravo))
                self.add_child(input_bravo)
                trigger = CheckboxInput(form, an_object.fields.agree)
                self.add_child(Label(form.view, for_input=trigger))
                self.add_child(trigger)
                self.add_child(NestedMoreInputsSection(form, trigger))

    class NestedMoreInputsSection(DynamicSection):
        def __init__(self, form, trigger_input):
            super(NestedMoreInputsSection, self).__init__(form, 'nestedmoreinputs', [trigger_input])
            if an_object.agree:
                input_charlie = TextInput(form, an_object.fields.charlie)
                self.add_child(Label(form.view, for_input=input_charlie))
                self.add_child(input_charlie)

    class MainWidget(Widget):
        def __init__(self, view):
            super(MainWidget, self).__init__(view)
            self.add_child(MyForm(view))

    wsgi_app = web_fixture.new_wsgi_app(enable_js=True, child_factory=MyForm.factory())

    web_fixture.reahl_server.set_app(wsgi_app)
    browser = web_fixture.driver_browser
    browser.open('/')

    #case: select a nested trigger
    browser.click(XPath.input_labelled('Two'))
    assert not browser.is_checked(XPath.input_labelled('I agree'))
    browser.click(XPath.input_labelled('I agree'))
    assert browser.is_checked(XPath.input_labelled('I agree'))
    browser.wait_for(XPath.input_labelled, 'Charlie')

    #make charlie and its parent disappear by clicking another trigger
    browser.click(XPath.input_labelled('One'))
    browser.wait_for_not(browser.is_visible, XPath.input_labelled('I agree'))
    browser.wait_for_not(browser.is_visible, XPath.input_labelled('Charlie'))

    #make charlie and its parent reappear and expect them to still have
    browser.click(XPath.input_labelled('Two'))
    assert browser.is_checked(XPath.input_labelled('I agree'))
    browser.wait_for(XPath.input_labelled, 'Charlie')

    #TODO: should we perhaps type in the Alpha,Bravo,Charlie inputs, or just remove them



# TODO: 
# - dealing with nestedforms that appear inside a DynamicWidget
# - dealing with lists/sentinels upon submitting a form when merging the querystring
# - test migration

# missing tests:
# - post, get exception, rerender
# - post, get exception, rerender, change parent trigger that results in different stuff, submit (various scenarios depending what different stuff you change)

# Test facts:
# - <CStest_retain_nested_trigger_input_values_when_rerendered> CS(Not true, their state is retained) when changing a parent trigger, the triggers that were nested in it, are cleared.
#   [- when a parent dynamic widget is changed, all its children widget arguments that happened to be applicable (because they were 
#    also opened) - are cleared explicitly in the fragment and as such we need to save a sentinel vanue in the DB for them else we would have no way to know that a cleared value should not be read from the saved DB input values.]
# - <  -- see aslo test_validation_of_undisclosed_yet_required_input>when a nested widget argument is required, but not present on the QS/fragment (or otherwise NOT validly entered), dont break, render the validation (non-js) error
#   [- when a widget argument on a nested dynamicwidget appears, it should be rendered empty if it is required and does not have a value or default]
# - when a domain exception occurs, the normal inputs on nested dynamicwidgets should still display whatever value was typed, and the trigger inputs as well and the fragment as it was before you submitted
#   [- the fragment is maintained by posting it to the server in a hidden input]
#   [- the fragment is also saved upon a breakage like use input, but globally for the view]
#   To ensure that, eg new/existing radio button is rendered correctly as well as that its widget is rendered according to its value as argument:
#     [- widget arguments come from either the QS or the fragment ]
#     [- when preparing an input, if it is a widget argument, widget argument input (QS/fragment) takes precedence over possible 
#        saved values in the database for the relevant input ]
# - when submitting with correct data after a domain exception, and you stay on the same page, all values and the hash are cleared as if you are looking at the page for the first time. 
#   [- when redirecting after a POST, the fragmnet is NOT included in the redirected URL (because that would result in more ajax fetches); but it is restored on the URL from its saved value using JS]
# -<CStest_retain_user_input_on_trigger_change>- when a parent trigger changes and a child is regenerated, if that child contains inputs and the user edited them, their edited values should be maintained

#? CStest whether a field can be required, but is not defaulted, and is refreshed - it won't have any input upon first ajax call - it broke at some stage.
       #its like <test_validation_of_undisclosed_yet_required_input>, but the input is visible, while it is being refreshed beause it appears in a section
# - when a parent trigger changes and a child is regenerated, if that child contains inputs and the user edited them, their edited values should be maintained
#     - case: even if they edited values are invalid


# - when a Field is for a list, and its name is overridden, it should look for input in overridden_name+[]

# - changing a trigger input changes tha hash, but it does not add an entry in browser history (NOT DONE history.replaceState does not work?)


# - a test for dynamicsection
