# Copyright 2019 Reahl Software Services (Pty) Ltd. All rights reserved.
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
import six

from sqlalchemy import Column, Integer, UnicodeText

from reahl.tofu import Fixture, scenario
from reahl.tofu.pytestsupport import with_fixtures, uses
from reahl.component.modelinterface import exposed, Field, Event, PatternConstraint, Action
from reahl.component.exceptions import DomainException
from reahl.web.ui import Form, ButtonInput, TextInput, Label, FormLayout
from reahl.web_dev.fixtures import WebFixture
from reahl.webdev.tools import Browser, XPath
from reahl.sqlalchemysupport_dev.fixtures import SqlAlchemyFixture
from reahl.sqlalchemysupport import Base, Session


@uses(web_fixture=WebFixture)
class OptimisticConcurrencyFixture(Fixture):
    def new_ModelObject(self):
        class ModelObject(Base):
            __tablename__ = 'test_optimistic_concurrency_model_object'
            id = Column(Integer, primary_key=True)
            some_field = Column(UnicodeText)

            @exposed
            def fields(self, fields):
                fields.some_field = Field(label='Some field', default='not set').with_validation_constraint(PatternConstraint('((?!invalidinput).)*'))

            @exposed
            def events(self, events):
                events.submit = Event(label='Submit')
                events.submit_break = Event(label='Submit break', action=Action(self.always_break))

            def always_break(self):
                raise DomainException('boo')

        return ModelObject

    def new_model_object(self):
        model_object = self.ModelObject()
        Session.add(model_object)
        return model_object

    def new_MyForm(self):
        fixture = self
        class MyForm(Form):
            def __init__(self, view):
                super(MyForm, self).__init__(view, 'myform')
                self.set_attribute('novalidate', 'novalidate')
                self.use_layout(FormLayout())

                if self.exception:
                    self.layout.add_alert_for_domain_exception(self.exception)

                self.layout.add_input(TextInput(self, fixture.model_object.fields.some_field))
                self.define_event_handler(fixture.model_object.events.submit)
                self.add_child(ButtonInput(self, fixture.model_object.events.submit))
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
        fixture.model_object

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





# (move to a bootstrap-specific test:) if using FormLayout.add_alert_for_domain_exception

# Only VISIBLE PrimitiveInput value data is taken into account by default for such optimistic locking, but:
#  if an input becomes readonly (or not readonly) since last rendered, it is also considered as having changed.
#  passing ignore_concurrency=True prevents a PrimitiveInput from taking part, despite being visible, and despite its readablity
#  any VISIBLE Widget can take part, if it overrides its concurrency_hash_strings method, and append a string representing its value to the yielded values


# If the user submits to a form that is no longer present on the current view (because of changes data as well), 
# the user is sent to the general error page and all form input/exceptions for all forms on the view are cleared.
# When clicking on the OK button on said error page, the user is taken back to the view, but sees it refreshed to new values.

