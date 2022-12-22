# Copyright 2019-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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



from sqlalchemy import Column, Integer, UnicodeText

from reahl.stubble import stubclass
from reahl.tofu import Fixture, scenario
from reahl.tofu.pytestsupport import with_fixtures, uses
from reahl.component.modelinterface import ExposedNames, Field, Event, PatternConstraint, Action
from reahl.component.exceptions import DomainException
from reahl.web.fw import Widget
from reahl.web.ui import Form, ButtonInput, TextInput, FormLayout, PrimitiveInput, HTMLElement, Div
from reahl.web_dev.fixtures import WebFixture
from reahl.web_dev.inputandvalidation.test_input import SimpleInputFixture
from reahl.browsertools.browsertools import Browser, XPath
from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture
from reahl.sqlalchemysupport import Base, Session


@uses(web_fixture=WebFixture)
class OptimisticConcurrencyFixture(Fixture):
    def new_ModelObject(self):
        class ModelObject(Base):
            __tablename__ = 'test_optimistic_concurrency_model_object'
            id = Column(Integer, primary_key=True)
            some_field = Column(UnicodeText)

            fields = ExposedNames()
            fields.some_field = lambda i: Field(label='Some field', default='not set').with_validation_constraint(PatternConstraint('((?!invalidinput).)*'))

            events = ExposedNames()
            events.submit = lambda i: Event(label='Submit')
            events.submit_break = lambda i: Event(label='Submit break', action=Action(i.always_break))

            def always_break(self):
                raise DomainException('boo')

        return ModelObject

    def new_model_object(self):
        return self.ModelObject()

    def new_MyForm(self):
        fixture = self
        class MyForm(Form):
            def __init__(self, view):
                super().__init__(view, 'myform')
                self.use_layout(FormLayout())
                self.set_attribute('novalidate', 'novalidate')

                if self.exception:
                    self.layout.add_alert_for_domain_exception(self.exception)

                self.layout.add_input(TextInput(self, fixture.model_object.fields.some_field))
                self.define_event_handler(fixture.model_object.events.submit)
                submit_button = self.add_child(ButtonInput(self, fixture.model_object.events.submit))
                submit_button.set_attribute('formnovalidate', 'formnovalidate') # TODO: the form's novalidate already does not, but somehow the browser still
                                                                                #   validates the input and disables the button. May be because the browser
                                                                                #   has cached javascript against our expectations because of a previous run?
                                                                                # We need to clear the browser's cached files before each test.
                self.define_event_handler(fixture.model_object.events.submit_break)
                self.add_child(ButtonInput(self, fixture.model_object.events.submit_break))
        return MyForm

    def make_concurrent_change_in_backend(self):
        self.model_object.some_field = 'changed by someone else'

    def concurrent_change_is_present(self):
        return self.model_object.some_field == 'changed by someone else'

    def is_concurrency_error_displayed(self):
        error_li = XPath.li().with_text('Some data changed since you opened this page, please reset input to try again.')
        return self.web_fixture.driver_browser.is_element_present(error_li)

    def is_any_error_displayed(self):
        return self.web_fixture.driver_browser.is_element_present(XPath.div().including_class('errors'))


@with_fixtures(WebFixture, SqlAlchemyFixture, OptimisticConcurrencyFixture)
def test_optimistic_concurrency(web_fixture, sql_alchemy_fixture, concurrency_fixture):
    """A user is prompted to handle the situation where data would be overwritten when submitting a 
       form that was originally rendered based on older data.
    """
    fixture = concurrency_fixture

    with sql_alchemy_fixture.persistent_test_classes(fixture.ModelObject):
        model_object = fixture.model_object
        Session.add(model_object)

        wsgi_app = web_fixture.new_wsgi_app(child_factory=fixture.MyForm.factory())
        web_fixture.reahl_server.set_app(wsgi_app)
        browser = web_fixture.driver_browser
        browser.open('/')

        # The form submit does not overwrite any data changed by other means
        assert not fixture.is_concurrency_error_displayed()

        browser.type(XPath.input_labelled('Some field'), 'something')
        fixture.make_concurrent_change_in_backend()
        
        browser.click(XPath.button_labelled('Submit'))

        assert fixture.is_concurrency_error_displayed()
        assert fixture.concurrent_change_is_present()

        # When presented with such an error, the user can click on a button to reset all inputs to the now-current values
        browser.click(XPath.button_labelled('Reset input'))
        assert not fixture.is_concurrency_error_displayed()
        assert browser.get_value(XPath.input_labelled('Some field')) == 'changed by someone else'

        browser.type(XPath.input_labelled('Some field'), 'final changed value')
        browser.click(XPath.button_labelled('Submit'))
        assert not fixture.is_concurrency_error_displayed()

        assert model_object.some_field == 'final changed value'


class ExceptionScenarios(Fixture):
    @scenario
    def break_with_validation_error(self):
        def submit_changed_but_invalid_inputs(browser):
            browser.type(XPath.input_labelled('Some field'), 'invalidinput')
            browser.click(XPath.button_labelled('Submit'))
        self.cause_exception_on_submit = submit_changed_but_invalid_inputs

    @scenario
    def break_with_other_domain_error(self):
        def submit_with_unchanged_inputs(browser):
            browser.click(XPath.button_labelled('Submit break'))
        self.cause_exception_on_submit = submit_with_unchanged_inputs


@with_fixtures(WebFixture, SqlAlchemyFixture, OptimisticConcurrencyFixture, ExceptionScenarios)
def test_clear_form_inputs_on_optimistic_concurrency(web_fixture, sql_alchemy_fixture, concurrency_fixture, scenario):
    """A concurrency error is detected upon submit after an exception.
       When a user resets inputs upon such a concurrency error, previous form exceptions and input data are cleared.
    """
    fixture = concurrency_fixture

    with sql_alchemy_fixture.persistent_test_classes(fixture.ModelObject):
        Session.add(fixture.model_object)

        wsgi_app = web_fixture.new_wsgi_app(child_factory=fixture.MyForm.factory())
        web_fixture.reahl_server.set_app(wsgi_app)
        browser = web_fixture.driver_browser
        browser.open('/')

        # Concurrency error is detected on submit after an exception
        scenario.cause_exception_on_submit(browser)
        assert fixture.is_any_error_displayed()
        assert not fixture.is_concurrency_error_displayed()

        fixture.make_concurrent_change_in_backend()

        browser.type(XPath.input_labelled('Some field'), 'valid input')
        browser.click(XPath.button_labelled('Submit'))
        assert fixture.is_concurrency_error_displayed()

        # Previous error and inputs are cleared
        browser.click(XPath.button_labelled('Reset input'))

        assert browser.get_value(XPath.input_labelled('Some field')) == 'changed by someone else'
        assert not fixture.is_any_error_displayed()



@stubclass(PrimitiveInput)
class PrimitiveInputStub(PrimitiveInput):
    def create_html_widget(self):
        return HTMLElement(self.view, 'input')


@uses(web_fixture=WebFixture, input_fixture=SimpleInputFixture)
class ParticipationScenarios(Fixture):
    
    @property
    def field(self):
        return self.input_fixture.field

    def new_non_readable_field(self):
        not_allowed = lambda x: False
        return self.input_fixture.new_field(readable=not_allowed, writable=not_allowed)

    @property
    def view(self):
        return self.web_fixture.view
    
    @property
    def form(self):
        return self.input_fixture.form
    
    @scenario
    def normal_visible_input(self):
        """Visible inputs participate by default"""
        self.widget = PrimitiveInputStub(self.form, self.field)
        self.expects_participation = True

    @scenario
    def normal_not_visible_input(self):
        """Non-Visible inputs are ignored"""
        self.widget = PrimitiveInputStub(self.form, self.non_readable_field)
        self.expects_participation = False

    @scenario
    def visible_input_that_ignores_concurrency(self):
        """Visible inputs that are explicitly set to ignore_concurrent_change are ignored"""
        self.widget = PrimitiveInputStub(self.form, self.field, ignore_concurrent_change=True)
        self.expects_participation = False

    @scenario
    def normal_non_input_widget(self):
        """Normal Widgets do not participate by default"""
        self.widget = Widget(self.view)
        self.expects_participation = False

    @scenario
    def custom_non_input_widget(self):
        """Normal Widgets can be made to particilate by yielding one or more strings denoting their value in get_concurrency_hash_strings method return"""
        class CustomWidget(Widget):
            def get_concurrency_hash_strings(self):
                yield 'a value'
                yield 'another'
        self.widget = CustomWidget(self.view)
        self.expects_participation = True


@with_fixtures(ParticipationScenarios)
def test_optimistic_concurrency_participation(scenario):
    """By default, only PrimitiveInputs are included in concurrency checks, but this is customisable in various ways"""
    assert scenario.expects_participation is bool(scenario.widget.get_concurrency_hash_digest())


@uses(input_fixture=SimpleInputFixture)
class ChangeScenarios(Fixture):
    writable = True
    def new_input_widget(self):
        return PrimitiveInputStub(self.input_fixture.form, self.input_fixture.new_field(writable=lambda field: self.writable))

    def set_unwritable(self):
        self.writable = False

    def change_domain_value(self):
        self.input_widget.bound_field.bound_to.an_attribute = 'changed'
        
    @scenario
    def change_readability(self):
        """When the input changes between being disabled and enabled, that counts as a change"""
        self.change_something = self.set_unwritable

    @scenario
    def change_value(self):
        """A changed ORIGINAL value of an input (ie whats in the domain) counts as a change"""
        self.change_something = self.change_domain_value


@with_fixtures(WebFixture, SimpleInputFixture, ChangeScenarios)
def test_optimistic_concurrency_what_constitutes_a_change(web_fixture, input_fixture, scenario):
    """When an Input is seen as having changed concurrently"""
    input_widget = scenario.input_widget

    before_hash = input_widget.get_concurrency_hash_digest()
    scenario.change_something()
    input_widget.bound_field.activate_global_field_data_store({}) # To simulate the Input being constructed twice and the comparison happening after the second
    assert before_hash != input_widget.get_concurrency_hash_digest()



@with_fixtures(WebFixture, SqlAlchemyFixture, OptimisticConcurrencyFixture)
def test_optimistic_concurrency_forms(web_fixture, sql_alchemy_fixture, concurrency_fixture):
    """When a form cannot be found anymore while submitting, we also assume it is because of changing data,
       this time sending the user to an error page after resetting view data.
    """
    fixture = concurrency_fixture

    fixture.show_form = True
    class FormContainer(Widget):
        def __init__(self, view):
            super().__init__(view)
            if fixture.show_form:
                self.add_child(fixture.MyForm(view))
            
    with sql_alchemy_fixture.persistent_test_classes(fixture.ModelObject):
        model_object = fixture.model_object
        Session.add(model_object)

        model_object.some_field = 'some value'

        wsgi_app = web_fixture.new_wsgi_app(child_factory=FormContainer.factory())
        web_fixture.reahl_server.set_app(wsgi_app)
        browser = web_fixture.driver_browser
        browser.open('/')

        # When submitting a form that is not present on the page anymore, user is ferried to an error page
        browser.type(XPath.input_labelled('Some field'), 'something else')
        fixture.show_form = False

        browser.click(XPath.button_labelled('Submit'))

        error_text = XPath.paragraph().with_text('Something changed on the server while you were busy. You cannot perform this action anymore.')
        assert browser.current_url.path == '/error'
        assert browser.is_element_present(error_text)

        # When presented with such an error, the user can click on a button to reset all inputs to the now-current values
        fixture.show_form = True                    # So we can check that form data was nuked
        browser.click(XPath.link().with_text('Ok'))
        assert browser.current_url.path == '/'      # Went back
        assert browser.get_value(XPath.input_labelled('Some field')) == 'some value'  # Form fields were cleared should the form now appear again



class OptimisticConcurrencyWithAjaxFixture(OptimisticConcurrencyFixture):
    def new_ModelObject(self):
        SuperModelObject = super().new_ModelObject()
        class ModelObject(SuperModelObject):
            some_trigger_field = Column(UnicodeText)

            fields = ExposedNames()
            fields.some_trigger_field = lambda i: Field(label='Some trigger field', default='not set')

        return ModelObject

    @scenario
    def refresh_entire_form(self):
        self.refresh_expected_for_form = True
        fixture = self
        SuperForm = super().new_MyForm()
        class MyForm(SuperForm):
            def __init__(self, view):
                super().__init__(view)
                self.enable_refresh()
                self.add_child(Div(view, css_id='inner_div'))
                self.layout.add_input(TextInput(self, fixture.model_object.fields.some_trigger_field, refresh_widget=self))
        self.MyForm = MyForm

    @scenario
    def refresh_only_a_part_of_the_form(self):
        self.refresh_expected_for_form = False
        fixture = self
        SuperForm = super().new_MyForm()
        class MyForm(SuperForm):
            def __init__(self, view):
                super().__init__(view)
                self.refreshing_div = self.add_child(Div(view, css_id='inner_div'))
                self.refreshing_div.enable_refresh()
                self.layout.add_input(TextInput(self, fixture.model_object.fields.some_trigger_field, refresh_widget=self.refreshing_div))
        self.MyForm = MyForm

    def is_refreshing_element_displayed(self):
        return self.web_fixture.driver_browser.is_element_present(XPath.paragraph().including_text('Hello'))


@with_fixtures(WebFixture, SqlAlchemyFixture, OptimisticConcurrencyWithAjaxFixture)
def test_optimistic_concurrency_with_ajax(web_fixture, sql_alchemy_fixture, concurrency_fixture):
    """When a concurrent change happens after an Ajax refresh, it is ignored in subsequent Ajax refreshes, 
       but upon an eventual submit the user is prompted.
    """
    fixture = concurrency_fixture
            
    with sql_alchemy_fixture.persistent_test_classes(fixture.ModelObject):
        model_object = fixture.model_object
        Session.add(model_object)

        model_object.some_trigger_field = 'some value'
        model_object.some_field = 'some value'

        wsgi_app = web_fixture.new_wsgi_app(child_factory=fixture.MyForm.factory(), enable_js=True)
        web_fixture.reahl_server.set_app(wsgi_app)
        browser = web_fixture.driver_browser
        browser.open('/')

        # Trigger refreshing once so that we create construction_client_side_state which may influence subsequent refreshings
        browser.type(XPath.input_labelled('Some field'), 'something for the fun of it')
        with browser.refresh_expected_for('#myform', fixture.refresh_expected_for_form),\
             browser.refresh_expected_for('#inner_div', True):
            browser.type(XPath.input_labelled('Some trigger field'), 'something else')

        fixture.make_concurrent_change_in_backend()

        assert not fixture.is_concurrency_error_displayed()
        browser.type(XPath.input_labelled('Some trigger field'), 'something else again')
        assert not fixture.is_concurrency_error_displayed()
        browser.click(XPath.button_labelled('Submit'))
        assert fixture.is_concurrency_error_displayed()

